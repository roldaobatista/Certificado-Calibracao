import type {
  CertificatePreviewField,
  CertificatePreviewScenario,
  ReviewSignatureScenario,
  SignatureApprovalPanel,
  SignatureApprovalRequirement,
  SignatureQueueCatalog,
  SignatureQueueItem,
  SignatureQueueScenario,
  SignatureQueueScenarioId,
  SignatureQueueStatus,
  SignatureQueueValidation,
} from "@afere/contracts";

import {
  resolveCertificatePreviewScenario,
  type CertificatePreviewScenarioSelection,
} from "./certificate-preview-scenarios.js";
import {
  resolveReviewSignatureScenario,
  type ReviewSignatureScenarioSelection,
} from "./review-signature-scenarios.js";

type SignatureQueueItemDefinition = {
  itemId: string;
  workOrderNumber: string;
  waitingSinceLabel: string;
  instrumentType: string;
  previewScenarioId: CertificatePreviewScenarioSelection;
  reviewSignatureScenarioId: ReviewSignatureScenarioSelection;
  documentHash: string;
};

type SignatureQueueScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  oldestPendingLabel: string;
  selectedItemId: string;
  items: SignatureQueueItemDefinition[];
};

const SCENARIOS: Record<SignatureQueueScenarioId, SignatureQueueScenarioDefinition> = {
  "approved-ready": {
    label: "Fila pronta para assinatura",
    description: "Itens com revisao aprovada, previa pronta e MFA valido podem seguir para assinatura final.",
    recommendedAction: "Reautenticar o signatario e concluir a emissao dos itens prontos.",
    oldestPendingLabel: "2h 12min",
    selectedItemId: "os-2026-00142",
    items: [
      {
        itemId: "os-2026-00142",
        workOrderNumber: "OS-2026-00142",
        waitingSinceLabel: "18 min",
        instrumentType: "Balanca",
        previewScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "approved-ready",
        documentHash: "a3f9f2c1e4427bf0c12d",
      },
      {
        itemId: "os-2026-00138",
        workOrderNumber: "OS-2026-00138",
        waitingSinceLabel: "2h 12min",
        instrumentType: "Balanca",
        previewScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "approved-ready",
        documentHash: "9e10a8d53e8b71d644ab",
      },
    ],
  },
  "attention-required": {
    label: "Fila com atencao regulatoria",
    description: "A fila continua operacional, mas um item pede conferencia final por warning visivel na previa.",
    recommendedAction: "Conferir a previa compacta e registrar a decisao final antes da assinatura.",
    oldestPendingLabel: "5h 40min",
    selectedItemId: "os-2026-00135",
    items: [
      {
        itemId: "os-2026-00135",
        workOrderNumber: "OS-2026-00135",
        waitingSinceLabel: "5h 40min",
        instrumentType: "Balanca",
        previewScenarioId: "type-a-suppressed",
        reviewSignatureScenarioId: "approved-ready",
        documentHash: "7fb3a61044d2fe0981ac",
      },
      {
        itemId: "os-2026-00144",
        workOrderNumber: "OS-2026-00144",
        waitingSinceLabel: "26 min",
        instrumentType: "Balanca",
        previewScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "approved-ready",
        documentHash: "99d17acb7fa80e12be47",
      },
    ],
  },
  "mfa-blocked": {
    label: "Fila bloqueada por MFA",
    description: "A assinatura falha fechada quando o signatario nao possui MFA valido ou a previa continua bloqueada.",
    recommendedAction: "Habilitar MFA e corrigir os gates da previa antes de tentar assinar.",
    oldestPendingLabel: "42 min",
    selectedItemId: "os-2026-00147",
    items: [
      {
        itemId: "os-2026-00147",
        workOrderNumber: "OS-2026-00147",
        waitingSinceLabel: "42 min",
        instrumentType: "Balanca",
        previewScenarioId: "type-c-blocked",
        reviewSignatureScenarioId: "signatory-mfa-blocked",
        documentHash: "31fd9cbb8af14f6dd0e1",
      },
    ],
  },
};

const DEFAULT_SCENARIO: SignatureQueueScenarioId = "approved-ready";

export function listSignatureQueueScenarios(): SignatureQueueScenario[] {
  return (Object.keys(SCENARIOS) as SignatureQueueScenarioId[]).map((scenarioId) =>
    resolveSignatureQueueScenario(scenarioId),
  );
}

export function resolveSignatureQueueScenario(
  scenarioId?: string,
  itemId?: string,
): SignatureQueueScenario {
  const id = isSignatureQueueScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const definition = SCENARIOS[id];
  const items = definition.items.map((itemDefinition) => buildSignatureQueueItem(itemDefinition));
  const selectedItem = items.find((item) => item.itemId === itemId) ?? items.find((item) => item.itemId === definition.selectedItemId) ?? items[0];

  if (!selectedItem) {
    throw new Error("missing_signature_queue_items");
  }

  return {
    id,
    label: definition.label,
    description: definition.description,
    summary: buildQueueSummary(definition, items),
    selectedItemId: selectedItem.itemId,
    items,
    approval: buildApprovalPanel(selectedItem, definition),
  };
}

export function buildSignatureQueueCatalog(
  scenarioId?: string,
  itemId?: string,
): SignatureQueueCatalog {
  const selectedScenario = resolveSignatureQueueScenario(scenarioId, itemId);
  const scenarios = listSignatureQueueScenarios().map((scenario) =>
    scenario.id === selectedScenario.id ? selectedScenario : scenario,
  );

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios,
  };
}

function buildSignatureQueueItem(definition: SignatureQueueItemDefinition): SignatureQueueItem {
  const previewScenario = resolveCertificatePreviewScenario(definition.previewScenarioId);
  const workflowScenario = resolveReviewSignatureScenario(definition.reviewSignatureScenarioId);
  const validations = buildValidations(previewScenario, workflowScenario);
  const derivedWarnings = buildDerivedWarnings(previewScenario, validations);
  const blockers = uniqueStrings([
    ...previewScenario.result.blockers,
    ...workflowScenario.result.blockers,
  ]);
  const warnings = uniqueStrings([
    ...previewScenario.result.warnings,
    ...workflowScenario.result.warnings,
    ...derivedWarnings,
  ]);

  return {
    itemId: definition.itemId,
    workOrderNumber: definition.workOrderNumber,
    customerName: readPreviewField(previewScenario, "identification", "Cliente") ?? "Cliente nao identificado",
    equipmentLabel:
      readPreviewField(previewScenario, "identification", "Equipamento") ?? "Equipamento nao identificado",
    instrumentType: definition.instrumentType,
    waitingSinceLabel: definition.waitingSinceLabel,
    certificateNumber: previewScenario.result.certificateNumber,
    status: resolveQueueItemStatus(validations, blockers, warnings),
    previewScenarioId: previewScenario.id,
    reviewSignatureScenarioId: workflowScenario.id,
    validations,
    blockers,
    warnings,
  };
}

function buildValidations(
  previewScenario: CertificatePreviewScenario,
  workflowScenario: ReviewSignatureScenario,
): SignatureQueueValidation[] {
  const reviewApproved =
    workflowScenario.result.stage === "approved" || workflowScenario.result.stage === "emitted";
  const signatureAuthorized =
    workflowScenario.result.signatureStep.status === "ready" ||
    workflowScenario.result.signatureStep.status === "complete";
  const previewReady = previewScenario.result.status === "ready";
  const qrAuthentic = previewScenario.result.qrVerificationStatus === "authentic";
  const symbolSuppressed = previewScenario.result.symbolPolicy === "suppressed";

  return [
    {
      label: "Revisao tecnica",
      status: reviewApproved ? "passed" : "failed",
      detail: reviewApproved
        ? "Revisao tecnica concluida e fluxo avancado para assinatura."
        : "A fila de assinatura so aceita itens com revisao tecnica concluida.",
    },
    {
      label: "Signatario e MFA",
      status: signatureAuthorized ? "passed" : "failed",
      detail: signatureAuthorized
        ? "Signatario elegivel com MFA obrigatorio habilitado para este certificado."
        : "Assinatura permanece bloqueada enquanto o signatario nao estiver elegivel com MFA valido.",
    },
    {
      label: "Previa do certificado",
      status: previewReady ? "passed" : "failed",
      detail: previewReady
        ? "Previa integral pronta para conferencia final antes da emissao."
        : "A previa canonica ainda possui bloqueios e impede a assinatura.",
    },
    {
      label: "QR publico",
      status: qrAuthentic ? "passed" : "failed",
      detail: qrAuthentic
        ? "QR autenticado no backend canonico para verificacao publica."
        : "QR publico ainda nao foi autenticado para este item.",
    },
    {
      label: "Politica regulatoria",
      status: symbolSuppressed ? "warning" : "passed",
      detail: symbolSuppressed
        ? "Simbolo regulatorio suprimido conforme escopo; exige conferencia final do operador."
        : "Politica regulatoria compativel com a assinatura prevista.",
    },
  ];
}

function buildDerivedWarnings(
  previewScenario: CertificatePreviewScenario,
  validations: SignatureQueueValidation[],
): string[] {
  const validationWarning = validations.find((validation) => validation.status === "warning");

  return uniqueStrings([
    ...(previewScenario.result.symbolPolicy === "suppressed"
      ? ["Simbolo regulatorio suprimido na previa; conferir o escopo antes de assinar."]
      : []),
    ...(validationWarning ? [validationWarning.detail] : []),
  ]);
}

function resolveQueueItemStatus(
  validations: SignatureQueueValidation[],
  blockers: string[],
  warnings: string[],
): SignatureQueueStatus {
  if (blockers.length > 0 || validations.some((validation) => validation.status === "failed")) {
    return "blocked";
  }

  if (warnings.length > 0 || validations.some((validation) => validation.status === "warning")) {
    return "attention";
  }

  return "ready";
}

function buildQueueSummary(
  definition: SignatureQueueScenarioDefinition,
  items: SignatureQueueItem[],
): SignatureQueueScenario["summary"] {
  const readyCount = items.filter((item) => item.status === "ready").length;
  const attentionCount = items.filter((item) => item.status === "attention").length;
  const blockedCount = items.filter((item) => item.status === "blocked").length;
  const blockers = uniqueStrings(items.flatMap((item) => item.blockers));
  const warnings = uniqueStrings(items.flatMap((item) => item.warnings));
  const status = resolveQueueSummaryStatus(blockedCount, attentionCount);

  return {
    status,
    headline:
      status === "ready"
        ? "Fila pronta para assinatura controlada"
        : status === "attention"
          ? "Fila exige conferencia final antes da assinatura"
          : "Fila bloqueada antes da emissao",
    pendingCount: items.length,
    readyCount,
    attentionCount,
    blockedCount,
    batchReadyCount: readyCount,
    oldestPendingLabel: definition.oldestPendingLabel,
    recommendedAction: definition.recommendedAction,
    blockers,
    warnings,
  };
}

function buildApprovalPanel(
  item: SignatureQueueItem,
  definition: SignatureQueueScenarioDefinition,
): SignatureApprovalPanel {
  const source = definition.items.find((candidate) => candidate.itemId === item.itemId);

  if (!source) {
    throw new Error("missing_signature_queue_item_source");
  }

  const previewScenario = resolveCertificatePreviewScenario(source.previewScenarioId);
  const workflowScenario = resolveReviewSignatureScenario(source.reviewSignatureScenarioId);
  const signatoryDisplayName =
    workflowScenario.result.assignments.signatory?.displayName ?? workflowScenario.result.signatureStep.actorLabel;
  const authorizationLabel =
    readPreviewField(previewScenario, "authorization", "Autorizacao") ?? "Signatario autorizado";
  const compactPreview: CertificatePreviewField[] = compactFields([
    ["OS", item.workOrderNumber],
    ["Cliente", item.customerName],
    ["Equipamento", item.equipmentLabel],
    ["Certificado", item.certificateNumber ?? "Numeracao ainda indisponivel"],
    [
      "Resumo tecnico",
      readPreviewField(previewScenario, "results", "Resumo tecnico") ??
        "Resumo tecnico indisponivel para este item.",
    ],
    ["QR publico", previewScenario.result.qrCodeUrl ?? "QR publico ainda indisponivel"],
  ]);

  return {
    itemId: item.itemId,
    title: `${item.workOrderNumber} - assinatura final`,
    status: item.status,
    signatoryDisplayName,
    authorizationLabel,
    statement: `Eu, ${signatoryDisplayName}, ${authorizationLabel}, confirmo que revisei o conteudo e autorizo a emissao deste certificado.`,
    documentHash: source.documentHash,
    canSign: item.status !== "blocked",
    actionLabel: item.status === "blocked" ? "Corrigir bloqueios antes de assinar" : "Assinar e emitir",
    blockers: item.blockers,
    warnings: item.warnings,
    authRequirements: buildAuthRequirements(workflowScenario),
    compactPreview,
  };
}

function buildAuthRequirements(
  workflowScenario: ReviewSignatureScenario,
): SignatureApprovalRequirement[] {
  const signatory = workflowScenario.result.assignments.signatory;

  return [
    {
      factor: "password",
      label: "Senha",
      status: "configured",
      detail: "Re-autenticacao por senha obrigatoria antes da emissao final.",
    },
    {
      factor: "totp",
      label: "Codigo TOTP",
      status: signatory?.mfaEnabled ? "configured" : "missing",
      detail: signatory?.mfaEnabled
        ? "MFA ativo e pronto para a confirmacao final do signatario."
        : "MFA ausente; a assinatura permanece bloqueada ate o fator ser habilitado.",
    },
  ];
}

function resolveQueueSummaryStatus(
  blockedCount: number,
  attentionCount: number,
): SignatureQueueStatus {
  if (blockedCount > 0) {
    return "blocked";
  }

  if (attentionCount > 0) {
    return "attention";
  }

  return "ready";
}

function readPreviewField(
  scenario: CertificatePreviewScenario,
  sectionKey: CertificatePreviewScenario["result"]["sections"][number]["key"],
  label: string,
): string | undefined {
  return scenario.result.sections
    .find((section) => section.key === sectionKey)
    ?.fields.find((field) => field.label === label)?.value;
}

function compactFields(values: Array<[string, string]>): CertificatePreviewField[] {
  return values.map(([label, value]) => ({ label, value }));
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}

function isSignatureQueueScenarioId(value: string | undefined): value is SignatureQueueScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

export type SignatureQueueScenarioView = SignatureQueueScenario;
