import type {
  ServiceOrderExecutionMetric,
  ServiceOrderListItem,
  ServiceOrderListItemStatus,
  ServiceOrderReviewAction,
  ServiceOrderReviewCatalog,
  ServiceOrderReviewChecklistItem,
  ServiceOrderReviewDetail,
  ServiceOrderReviewScenario,
  ServiceOrderReviewScenarioId,
  ServiceOrderReviewStatus,
  ServiceOrderTimelineStep,
  SignatureQueueScenarioId,
  EmissionDryRunScenarioId,
  EmissionWorkspaceScenarioId,
  ReviewSignatureScenarioId,
} from "@afere/contracts";

import { resolveCertificatePreviewScenario } from "./certificate-preview-scenarios.js";
import { resolveReviewSignatureScenario } from "./review-signature-scenarios.js";

type ServiceOrderListItemDefinition = {
  itemId: string;
  workOrderNumber: string;
  status: ServiceOrderListItemStatus;
  technicianName: string;
  updatedAtLabel: string;
  previewScenarioId?: EmissionDryRunScenarioId;
  fallbackCustomerName?: string;
  fallbackEquipmentLabel?: string;
};

type ServiceOrderDetailDefinition = {
  itemId: string;
  workOrderNumber: string;
  workspaceScenarioId: EmissionWorkspaceScenarioId;
  previewScenarioId: EmissionDryRunScenarioId;
  reviewSignatureScenarioId: ReviewSignatureScenarioId;
  signatureQueueScenarioId?: SignatureQueueScenarioId;
  createdAtLabel: string;
  acceptedAtLabel: string;
  executionStartedAtLabel: string;
  executedAtLabel: string;
  reviewAtLabel: string;
  signatureAtLabel: string;
  emittedAtLabel: string;
  procedureLabel: string;
  curvePointsLabel: string;
  evidenceLabel: string;
  conformityLabel: string;
  metrics: ServiceOrderExecutionMetric[];
  checklist: ServiceOrderReviewChecklistItem[];
  commentDraft: string;
  blockers: string[];
  warnings: string[];
};

type ServiceOrderReviewScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedItemId: string;
  items: ServiceOrderListItemDefinition[];
  detail: ServiceOrderDetailDefinition;
};

const REVIEW_READY_ITEMS: ServiceOrderListItemDefinition[] = [
  {
    itemId: "os-2026-00142",
    workOrderNumber: "OS-2026-00142",
    status: "awaiting_review",
    technicianName: "Joao Executor",
    updatedAtLabel: "14:22",
    previewScenarioId: "type-b-ready",
  },
  {
    itemId: "os-2026-00135",
    workOrderNumber: "OS-2026-00135",
    status: "awaiting_signature",
    technicianName: "Joao Executor",
    updatedAtLabel: "13:50",
    previewScenarioId: "type-a-suppressed",
  },
  {
    itemId: "os-2026-00140",
    workOrderNumber: "OS-2026-00140",
    status: "in_execution",
    technicianName: "Carlos Tecnico",
    updatedAtLabel: "11:30",
    fallbackCustomerName: "OS em execucao",
    fallbackEquipmentLabel: "Instrumento em campo",
  },
  {
    itemId: "os-2026-00139",
    workOrderNumber: "OS-2026-00139",
    status: "emitted",
    technicianName: "Joao Executor",
    updatedAtLabel: "ontem",
    previewScenarioId: "type-b-ready",
  },
];

const HISTORY_PENDING_ITEMS: ServiceOrderListItemDefinition[] = [
  {
    itemId: "os-2026-00141",
    workOrderNumber: "OS-2026-00141",
    status: "awaiting_review",
    technicianName: "Joao Executor",
    updatedAtLabel: "13:50",
    previewScenarioId: "type-b-ready",
  },
  ...REVIEW_READY_ITEMS.slice(1),
];

const REVIEW_BLOCKED_ITEMS: ServiceOrderListItemDefinition[] = [
  {
    itemId: "os-2026-00147",
    workOrderNumber: "OS-2026-00147",
    status: "blocked",
    technicianName: "Joao Executor",
    updatedAtLabel: "42 min",
    previewScenarioId: "type-c-blocked",
  },
  ...REVIEW_READY_ITEMS.slice(1),
];

const SCENARIOS: Record<ServiceOrderReviewScenarioId, ServiceOrderReviewScenarioDefinition> = {
  "review-ready": {
    label: "OS pronta para revisao",
    description: "A linha do tempo, os dados de execucao e o checklist tecnico estao coerentes para concluir a revisao.",
    recommendedAction: "Aprovar a revisao tecnica da OS selecionada e liberar a etapa seguinte do fluxo.",
    selectedItemId: "os-2026-00142",
    items: REVIEW_READY_ITEMS,
    detail: {
      itemId: "os-2026-00142",
      workOrderNumber: "OS-2026-00142",
      workspaceScenarioId: "baseline-ready",
      previewScenarioId: "type-b-ready",
      reviewSignatureScenarioId: "segregated-ready",
      createdAtLabel: "12/04 09:01",
      acceptedAtLabel: "12/04 09:15",
      executionStartedAtLabel: "19/04 11:00",
      executedAtLabel: "19/04 14:22",
      reviewAtLabel: "Aguardando",
      signatureAtLabel: "Pendente",
      emittedAtLabel: "Pendente",
      procedureLabel: "PT-005 rev.04",
      curvePointsLabel: "5 pontos (10% / 25% / 50% / 75% / 100%)",
      evidenceLabel: "12 evidencias anexadas",
      conformityLabel: "Aprovado (banda de guarda 50%)",
      metrics: [
        { label: "Repetibilidade", value: "sigma = 0,058 kg", tone: "ok" },
        { label: "Excentricidade", value: "Delta max = 0,10 kg", tone: "ok" },
        { label: "Observacoes de campo", value: "Sem desvios visiveis durante a execucao", tone: "neutral" },
      ],
      checklist: [
        {
          label: "Padroes validos no momento da execucao",
          status: "passed",
          detail: "Conjunto reservado com certificado valido e faixa compativel.",
        },
        {
          label: "Ambiente dentro da faixa do procedimento",
          status: "passed",
          detail: "Temperatura, umidade e pressao permaneceram dentro da faixa declarada.",
        },
        {
          label: "Pontos da curva adequados ao uso pretendido",
          status: "passed",
          detail: "A distribuicao dos pontos cobre a faixa de uso operacional declarada.",
        },
        {
          label: "Calculo de incerteza coerente",
          status: "passed",
          detail: "Resumo tecnico e incerteza expandida estao consistentes com a declaracao canônica.",
        },
        {
          label: "Coerencia com historico do equipamento",
          status: "passed",
          detail: "Historico comparado com a ultima calibracao sem desvio relevante.",
        },
      ],
      commentDraft:
        "Curva coerente com o historico do equipamento e com o procedimento PT-005 rev.04. Revisao tecnica liberada.",
      blockers: [],
      warnings: [],
    },
  },
  "history-pending": {
    label: "OS em atencao na revisao",
    description: "A revisao tecnica ainda depende de uma conferencia complementar de historico antes da aprovacao.",
    recommendedAction: "Concluir a verificacao de historico do equipamento antes de aprovar a revisao.",
    selectedItemId: "os-2026-00141",
    items: HISTORY_PENDING_ITEMS,
    detail: {
      itemId: "os-2026-00141",
      workOrderNumber: "OS-2026-00141",
      workspaceScenarioId: "team-attention",
      previewScenarioId: "type-b-ready",
      reviewSignatureScenarioId: "segregated-ready",
      createdAtLabel: "12/04 08:42",
      acceptedAtLabel: "12/04 09:03",
      executionStartedAtLabel: "19/04 10:10",
      executedAtLabel: "19/04 13:50",
      reviewAtLabel: "Em andamento",
      signatureAtLabel: "Pendente",
      emittedAtLabel: "Pendente",
      procedureLabel: "PT-005 rev.04",
      curvePointsLabel: "5 pontos (10% / 25% / 50% / 75% / 100%)",
      evidenceLabel: "9 evidencias anexadas",
      conformityLabel: "Aprovado com conferencia historica pendente",
      metrics: [
        { label: "Repetibilidade", value: "sigma = 0,061 kg", tone: "ok" },
        { label: "Excentricidade", value: "Delta max = 0,11 kg", tone: "ok" },
        { label: "Historico anterior", value: "Ultima OS ainda nao confrontada nesta revisao", tone: "warn" },
      ],
      checklist: [
        {
          label: "Padroes validos no momento da execucao",
          status: "passed",
          detail: "Conjunto reservado com certificado valido e faixa compativel.",
        },
        {
          label: "Ambiente dentro da faixa do procedimento",
          status: "passed",
          detail: "Condicoes ambientais aderentes ao procedimento declarado.",
        },
        {
          label: "Pontos da curva adequados ao uso pretendido",
          status: "passed",
          detail: "Pontos suficientes para a faixa de uso do equipamento.",
        },
        {
          label: "Calculo de incerteza coerente",
          status: "passed",
          detail: "Incerteza coerente com o resumo tecnico da previa.",
        },
        {
          label: "Coerencia com historico do equipamento",
          status: "pending",
          detail: "A ultima calibracao emitida ainda nao foi confrontada com esta OS.",
        },
      ],
      commentDraft: "",
      blockers: [],
      warnings: ["Historico do equipamento ainda nao confrontado nesta revisao."],
    },
  },
  "review-blocked": {
    label: "OS bloqueada na revisao",
    description: "A OS selecionada combina conflito de atribuicao de revisor com gates tecnicos ainda falhos na previa.",
    recommendedAction: "Regularizar a atribuicao do revisor e corrigir os gates tecnicos antes de revisar a OS.",
    selectedItemId: "os-2026-00147",
    items: REVIEW_BLOCKED_ITEMS,
    detail: {
      itemId: "os-2026-00147",
      workOrderNumber: "OS-2026-00147",
      workspaceScenarioId: "release-blocked",
      previewScenarioId: "type-c-blocked",
      reviewSignatureScenarioId: "reviewer-conflict",
      createdAtLabel: "19/04 08:15",
      acceptedAtLabel: "19/04 08:40",
      executionStartedAtLabel: "19/04 09:20",
      executedAtLabel: "19/04 10:05",
      reviewAtLabel: "Bloqueada",
      signatureAtLabel: "Nao iniciada",
      emittedAtLabel: "Nao iniciada",
      procedureLabel: "PT-009 rev.02",
      curvePointsLabel: "4 pontos preliminares",
      evidenceLabel: "5 evidencias anexadas",
      conformityLabel: "Indeterminada",
      metrics: [
        { label: "Repetibilidade", value: "sigma = 0,140 kg", tone: "warn" },
        { label: "Excentricidade", value: "Delta max = 0,23 kg", tone: "warn" },
        { label: "Condicoes ambientais", value: "Fora da faixa do procedimento", tone: "warn" },
      ],
      checklist: [
        {
          label: "Padroes validos no momento da execucao",
          status: "failed",
          detail: "O padrao desta OS nao possui certificado valido para a revisao.",
        },
        {
          label: "Ambiente dentro da faixa do procedimento",
          status: "failed",
          detail: "Os dados ambientais ficaram fora da faixa aceitavel do procedimento.",
        },
        {
          label: "Pontos da curva adequados ao uso pretendido",
          status: "pending",
          detail: "A curva ainda nao cobre a faixa completa de uso pretendido.",
        },
        {
          label: "Calculo de incerteza coerente",
          status: "pending",
          detail: "A declaracao metrologica ainda depende de regularizacao do padrao.",
        },
        {
          label: "Segregacao do revisor",
          status: "failed",
          detail: "O revisor atual coincide com o executor e bloqueia a revisao.",
        },
      ],
      commentDraft:
        "Revisao bloqueada por conflito de atribuicao e por gates tecnicos falhos na previa do certificado.",
      blockers: ["Revisor atual coincide com o executor desta OS."],
      warnings: ["Campo livre do cenario continua com termos inadequados para o perfil Tipo C."],
    },
  },
};

const DEFAULT_SCENARIO: ServiceOrderReviewScenarioId = "review-ready";

export function listServiceOrderReviewScenarios(): ServiceOrderReviewScenario[] {
  return (Object.keys(SCENARIOS) as ServiceOrderReviewScenarioId[]).map((scenarioId) =>
    resolveServiceOrderReviewScenario(scenarioId),
  );
}

export function resolveServiceOrderReviewScenario(
  scenarioId?: string,
  itemId?: string,
): ServiceOrderReviewScenario {
  const id = isServiceOrderReviewScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const definition = SCENARIOS[id];
  const items = definition.items.map(buildServiceOrderListItem);
  const selectedItemDefinition =
    definition.items.find((item) => item.itemId === itemId) ??
    definition.items.find((item) => item.itemId === definition.selectedItemId) ??
    definition.items[0];
  const selectedItem =
    items.find((item) => item.itemId === selectedItemDefinition?.itemId) ??
    items.find((item) => item.itemId === definition.selectedItemId) ??
    items[0];

  if (!selectedItem || !selectedItemDefinition) {
    throw new Error("missing_service_order_review_items");
  }

  const detail =
    selectedItem.itemId === definition.detail.itemId
      ? buildServiceOrderReviewDetail(definition.detail, selectedItem)
      : buildFallbackServiceOrderReviewDetail(selectedItemDefinition, selectedItem);

  return {
    id,
    label: definition.label,
    description: definition.description,
    summary: buildServiceOrderReviewSummary(definition.recommendedAction, items, detail),
    selectedItemId: selectedItem.itemId,
    items,
    detail,
  };
}

export function buildServiceOrderReviewCatalog(
  scenarioId?: string,
  itemId?: string,
): ServiceOrderReviewCatalog {
  const selectedScenario = resolveServiceOrderReviewScenario(scenarioId, itemId);
  const scenarios = listServiceOrderReviewScenarios().map((scenario) =>
    scenario.id === selectedScenario.id ? selectedScenario : scenario,
  );

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios,
  };
}

function buildServiceOrderListItem(
  definition: ServiceOrderListItemDefinition,
): ServiceOrderListItem {
  const previewScenario = definition.previewScenarioId
    ? resolveCertificatePreviewScenario(definition.previewScenarioId)
    : undefined;

  return {
    itemId: definition.itemId,
    workOrderNumber: definition.workOrderNumber,
    customerName:
      readPreviewField(previewScenario, "identification", "Cliente") ??
      definition.fallbackCustomerName ??
      "Cliente nao identificado",
    equipmentLabel:
      readPreviewField(previewScenario, "identification", "Equipamento") ??
      definition.fallbackEquipmentLabel ??
      "Equipamento nao identificado",
    status: definition.status,
    technicianName: definition.technicianName,
    updatedAtLabel: definition.updatedAtLabel,
  };
}

function buildServiceOrderReviewDetail(
  definition: ServiceOrderDetailDefinition,
  selectedItem: ServiceOrderListItem,
): ServiceOrderReviewDetail {
  const previewScenario = resolveCertificatePreviewScenario(definition.previewScenarioId);
  const reviewScenario = resolveReviewSignatureScenario(definition.reviewSignatureScenarioId);
  const blockers = uniqueStrings([
    ...definition.blockers,
    ...previewScenario.result.blockers,
    ...reviewScenario.result.blockers,
  ]);
  const warnings = uniqueStrings([
    ...definition.warnings,
    ...previewScenario.result.warnings,
    ...reviewScenario.result.warnings,
  ]);
  const checklistFailed = definition.checklist.some((item) => item.status === "failed");
  const checklistPending = definition.checklist.some((item) => item.status === "pending");
  const status = resolveDetailStatus(blockers, warnings, checklistFailed, checklistPending);
  const executorLabel = reviewScenario.result.assignments.executor.displayName;
  const assignedReviewerLabel =
    reviewScenario.result.assignments.reviewer?.displayName ??
    reviewScenario.result.suggestions.reviewer?.displayName ??
    "Revisor nao atribuido";
  const title = `${definition.workOrderNumber} · ${selectedItem.customerName} · ${selectedItem.equipmentLabel}`;

  return {
    itemId: definition.itemId,
    title,
    status,
    statusLine: buildStatusLine(status, assignedReviewerLabel, executorLabel),
    executorLabel,
    assignedReviewerLabel,
    procedureLabel: definition.procedureLabel,
    standardsLabel:
      readPreviewField(previewScenario, "standards", "Conjunto reservado") ?? "Padroes nao identificados",
    environmentLabel:
      readPreviewField(previewScenario, "environment", "Temperatura") ?? "Ambiente nao registrado",
    curvePointsLabel: definition.curvePointsLabel,
    evidenceLabel: definition.evidenceLabel,
    uncertaintyLabel:
      readPreviewField(previewScenario, "results", "Incerteza expandida") ?? "Incerteza nao identificada",
    conformityLabel: definition.conformityLabel,
    timeline: buildTimeline(definition, reviewScenario, status),
    metrics: definition.metrics,
    checklist: definition.checklist,
    commentDraft: definition.commentDraft,
    allowedActions: buildAllowedActions(status, reviewScenario, definition.signatureQueueScenarioId),
    blockers,
    warnings,
    links: {
      workspaceScenarioId: definition.workspaceScenarioId,
      previewScenarioId: definition.previewScenarioId,
      reviewSignatureScenarioId: definition.reviewSignatureScenarioId,
      signatureQueueScenarioId: definition.signatureQueueScenarioId,
    },
  };
}

function buildFallbackServiceOrderReviewDetail(
  definition: ServiceOrderListItemDefinition,
  selectedItem: ServiceOrderListItem,
): ServiceOrderReviewDetail {
  const previewScenarioId = definition.previewScenarioId ?? "type-b-ready";
  const previewScenario = resolveCertificatePreviewScenario(previewScenarioId);
  const reviewSignatureScenarioId = selectFallbackReviewScenarioId(definition.status);
  const reviewScenario = resolveReviewSignatureScenario(reviewSignatureScenarioId);
  const workspaceScenarioId = selectFallbackWorkspaceScenarioId(definition.status);
  const blockers = uniqueStrings([
    ...previewScenario.result.blockers,
    ...reviewScenario.result.blockers,
  ]);
  const warnings = uniqueStrings([
    ...previewScenario.result.warnings,
    ...reviewScenario.result.warnings,
  ]);
  const checklist = buildFallbackChecklist(definition.status, blockers.length > 0);
  const status = resolveDetailStatus(
    blockers,
    warnings,
    checklist.some((item) => item.status === "failed"),
    checklist.some((item) => item.status === "pending"),
  );
  const executorLabel = reviewScenario.result.assignments.executor.displayName;
  const assignedReviewerLabel =
    reviewScenario.result.assignments.reviewer?.displayName ??
    reviewScenario.result.suggestions.reviewer?.displayName ??
    "Revisor nao atribuido";

  return {
    itemId: definition.itemId,
    title: `${definition.workOrderNumber} · ${selectedItem.customerName} · ${selectedItem.equipmentLabel}`,
    status,
    statusLine: buildStatusLine(status, assignedReviewerLabel, executorLabel),
    executorLabel,
    assignedReviewerLabel,
    procedureLabel: "PT-005 rev.04",
    standardsLabel:
      readPreviewField(previewScenario, "standards", "Conjunto reservado") ?? "Padroes nao identificados",
    environmentLabel:
      readPreviewField(previewScenario, "environment", "Temperatura") ?? "Ambiente nao registrado",
    curvePointsLabel:
      definition.status === "in_execution"
        ? "Curva ainda em execucao"
        : "5 pontos (10% / 25% / 50% / 75% / 100%)",
    evidenceLabel:
      definition.status === "in_execution" ? "Evidencias parciais em coleta" : "Evidencias registradas no fluxo",
    uncertaintyLabel:
      readPreviewField(previewScenario, "results", "Incerteza expandida") ?? "Incerteza nao identificada",
    conformityLabel:
      definition.status === "emitted"
        ? "Emitido"
        : definition.status === "awaiting_signature"
          ? "Revisao aprovada"
          : definition.status === "in_execution"
            ? "Em execucao"
            : definition.status === "blocked"
              ? "Bloqueada"
              : "Aguardando revisao",
    timeline: buildFallbackTimeline(definition, reviewScenario, status),
    metrics: buildFallbackMetrics(definition.status),
    checklist,
    commentDraft: "",
    allowedActions: buildAllowedActions(
      status,
      reviewScenario,
      definition.status === "awaiting_signature" ? "approved-ready" : undefined,
    ),
    blockers,
    warnings,
    links: {
      workspaceScenarioId,
      previewScenarioId,
      reviewSignatureScenarioId,
      signatureQueueScenarioId:
        definition.status === "awaiting_signature" ? "approved-ready" : definition.status === "blocked" ? "mfa-blocked" : undefined,
    },
  };
}

function buildTimeline(
  definition: ServiceOrderDetailDefinition,
  reviewScenario: ReturnType<typeof resolveReviewSignatureScenario>,
  detailStatus: ServiceOrderReviewStatus,
): ServiceOrderTimelineStep[] {
  const reviewStepStatus =
    reviewScenario.result.stage === "approved" || reviewScenario.result.stage === "emitted"
      ? "complete"
      : "current";
  const signatureStepStatus =
    reviewScenario.result.stage === "emitted"
      ? "complete"
      : reviewScenario.result.stage === "approved"
        ? "current"
        : "pending";
  const emittedStepStatus = reviewScenario.result.stage === "emitted" ? "complete" : "pending";

  return [
    { key: "created", label: "Criada", status: "complete", timestampLabel: definition.createdAtLabel },
    { key: "accepted", label: "Aceita", status: "complete", timestampLabel: definition.acceptedAtLabel },
    {
      key: "in_execution",
      label: "Em execucao",
      status: "complete",
      timestampLabel: definition.executionStartedAtLabel,
    },
    { key: "executed", label: "Executada", status: "complete", timestampLabel: definition.executedAtLabel },
    {
      key: "review",
      label: "Revisao",
      status: detailStatus === "blocked" ? "current" : reviewStepStatus,
      timestampLabel: definition.reviewAtLabel,
    },
    {
      key: "signature",
      label: "Assinatura",
      status: detailStatus === "blocked" ? "pending" : signatureStepStatus,
      timestampLabel: definition.signatureAtLabel,
    },
    {
      key: "emitted",
      label: "Emitido",
      status: detailStatus === "blocked" ? "pending" : emittedStepStatus,
      timestampLabel: definition.emittedAtLabel,
    },
  ];
}

function buildAllowedActions(
  detailStatus: ServiceOrderReviewStatus,
  reviewScenario: ReturnType<typeof resolveReviewSignatureScenario>,
  signatureQueueScenarioId?: SignatureQueueScenarioId,
): ServiceOrderReviewAction[] {
  const actions = new Set<ServiceOrderReviewAction>();

  if (reviewScenario.result.allowedActions.includes("reject_to_executor")) {
    actions.add("return_to_technician");
  }

  if (detailStatus === "ready" && reviewScenario.result.allowedActions.includes("review_certificate")) {
    actions.add("approve_review");
  }

  actions.add("open_preview");

  if (signatureQueueScenarioId) {
    actions.add("open_signature_queue");
  }

  return [...actions];
}

function buildServiceOrderReviewSummary(
  recommendedAction: string,
  items: ServiceOrderListItem[],
  detail: ServiceOrderReviewDetail,
): ServiceOrderReviewScenario["summary"] {
  const awaitingReviewCount = items.filter((item) => item.status === "awaiting_review").length;
  const awaitingSignatureCount = items.filter((item) => item.status === "awaiting_signature").length;
  const inExecutionCount = items.filter((item) => item.status === "in_execution").length;
  const emittedCount = items.filter((item) => item.status === "emitted").length;
  const blockedCount = items.filter((item) => item.status === "blocked").length;

  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "OS pronta para concluir a revisao tecnica"
        : detail.status === "attention"
          ? "OS exige conferencia complementar antes da revisao"
          : "OS bloqueada antes da aprovacao tecnica",
    totalCount: items.length,
    awaitingReviewCount,
    awaitingSignatureCount,
    inExecutionCount,
    emittedCount,
    blockedCount,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function resolveDetailStatus(
  blockers: string[],
  warnings: string[],
  checklistFailed: boolean,
  checklistPending: boolean,
): ServiceOrderReviewStatus {
  if (blockers.length > 0 || checklistFailed) {
    return "blocked";
  }

  if (warnings.length > 0 || checklistPending) {
    return "attention";
  }

  return "ready";
}

function buildStatusLine(
  status: ServiceOrderReviewStatus,
  assignedReviewerLabel: string,
  executorLabel: string,
): string {
  if (status === "blocked") {
    return `Revisao bloqueada · Atribuido a: ${assignedReviewerLabel} · Executado por: ${executorLabel}`;
  }

  if (status === "attention") {
    return `Aguardando conferencia final · Atribuido a: ${assignedReviewerLabel} · Executado por: ${executorLabel}`;
  }

  return `Aguardando revisao · Atribuido a: ${assignedReviewerLabel} · Executado por: ${executorLabel}`;
}

function buildFallbackTimeline(
  definition: ServiceOrderListItemDefinition,
  reviewScenario: ReturnType<typeof resolveReviewSignatureScenario>,
  detailStatus: ServiceOrderReviewStatus,
): ServiceOrderTimelineStep[] {
  const reviewTimestamp =
    definition.status === "awaiting_signature" ? "Concluida" : detailStatus === "blocked" ? "Bloqueada" : "Em andamento";
  const signatureTimestamp =
    definition.status === "awaiting_signature"
      ? "Na fila"
      : definition.status === "emitted"
        ? "Concluida"
        : "Pendente";
  const emittedTimestamp = definition.status === "emitted" ? "Concluida" : "Pendente";

  return [
    { key: "created", label: "Criada", status: "complete", timestampLabel: "Criada" },
    { key: "accepted", label: "Aceita", status: "complete", timestampLabel: "Aceita" },
    {
      key: "in_execution",
      label: "Em execucao",
      status: definition.status === "in_execution" ? "current" : "complete",
      timestampLabel: definition.status === "in_execution" ? "Em execucao" : "Executada",
    },
    {
      key: "executed",
      label: "Executada",
      status: definition.status === "in_execution" ? "pending" : "complete",
      timestampLabel: definition.status === "in_execution" ? "Pendente" : "Executada",
    },
    {
      key: "review",
      label: "Revisao",
      status:
        definition.status === "awaiting_signature" || definition.status === "emitted"
          ? "complete"
          : detailStatus === "blocked"
            ? "current"
            : reviewScenario.result.stage === "in_review"
              ? "current"
              : "pending",
      timestampLabel: reviewTimestamp,
    },
    {
      key: "signature",
      label: "Assinatura",
      status:
        definition.status === "emitted"
          ? "complete"
          : definition.status === "awaiting_signature"
            ? "current"
            : "pending",
      timestampLabel: signatureTimestamp,
    },
    {
      key: "emitted",
      label: "Emitido",
      status: definition.status === "emitted" ? "complete" : "pending",
      timestampLabel: emittedTimestamp,
    },
  ];
}

function buildFallbackMetrics(
  status: ServiceOrderListItemStatus,
): ServiceOrderExecutionMetric[] {
  if (status === "in_execution") {
    return [
      { label: "Progresso", value: "Execucao em andamento", tone: "neutral" },
      { label: "Checklist de campo", value: "Ainda em preenchimento", tone: "neutral" },
      { label: "Evidencias", value: "Coleta parcial", tone: "neutral" },
    ];
  }

  if (status === "blocked") {
    return [
      { label: "Checklist tecnico", value: "Falhas abertas na revisao", tone: "warn" },
      { label: "Segregacao", value: "Conflito de atribuicao", tone: "warn" },
      { label: "Previa", value: "Ainda bloqueada", tone: "warn" },
    ];
  }

  return [
    { label: "Checklist tecnico", value: "Consistente com a etapa atual", tone: "ok" },
    { label: "Timeline", value: "Sem lacunas na fase atual", tone: "ok" },
    { label: "Evidencias", value: "Registradas no fluxo", tone: "neutral" },
  ];
}

function buildFallbackChecklist(
  status: ServiceOrderListItemStatus,
  blocked: boolean,
): ServiceOrderReviewChecklistItem[] {
  if (status === "in_execution") {
    return [
      {
        label: "Execucao concluida",
        status: "pending",
        detail: "A OS ainda nao concluiu a execucao de todos os pontos.",
      },
      {
        label: "Evidencias anexadas",
        status: "pending",
        detail: "As evidencias ainda estao sendo coletadas no fluxo.",
      },
    ];
  }

  if (blocked) {
    return [
      {
        label: "Checklist tecnico",
        status: "failed",
        detail: "Ha gates tecnicos e de atribuicao abertos para esta OS.",
      },
      {
        label: "Conferencia final",
        status: "pending",
        detail: "A OS precisa regularizar os bloqueios antes de prosseguir.",
      },
    ];
  }

  if (status === "awaiting_signature") {
    return [
      {
        label: "Revisao tecnica",
        status: "passed",
        detail: "A revisao tecnica ja foi concluida para esta OS.",
      },
      {
        label: "Fila de assinatura",
        status: "pending",
        detail: "A OS aguarda o ato final de assinatura do signatario.",
      },
    ];
  }

  if (status === "emitted") {
    return [
      {
        label: "Revisao tecnica",
        status: "passed",
        detail: "Revisao concluida e historico fechado.",
      },
      {
        label: "Emissao",
        status: "passed",
        detail: "Certificado ja emitido para esta OS.",
      },
    ];
  }

  return [
    {
      label: "Checklist tecnico",
      status: "passed",
      detail: "A OS ja possui os elementos minimos para revisao.",
    },
    {
      label: "Conferencia final",
      status: "pending",
      detail: "A revisao desta OS ainda esta em andamento.",
    },
  ];
}

function selectFallbackReviewScenarioId(
  status: ServiceOrderListItemStatus,
): ReviewSignatureScenarioId {
  switch (status) {
    case "awaiting_signature":
    case "emitted":
      return "approved-ready";
    case "blocked":
      return "reviewer-conflict";
    default:
      return "segregated-ready";
  }
}

function selectFallbackWorkspaceScenarioId(
  status: ServiceOrderListItemStatus,
): EmissionWorkspaceScenarioId {
  switch (status) {
    case "blocked":
      return "release-blocked";
    case "awaiting_review":
      return "team-attention";
    default:
      return "baseline-ready";
  }
}

function readPreviewField(
  previewScenario: ReturnType<typeof resolveCertificatePreviewScenario> | undefined,
  sectionKey: "identification" | "standards" | "environment" | "results",
  label: string,
): string | undefined {
  return previewScenario?.result.sections
    .find((section) => section.key === sectionKey)
    ?.fields.find((field) => field.label === label)?.value;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}

function isServiceOrderReviewScenarioId(
  value: string | undefined,
): value is ServiceOrderReviewScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

export type ServiceOrderReviewScenarioView = ServiceOrderReviewScenario;
