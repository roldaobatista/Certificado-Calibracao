import {
  computeAuditHash,
  verifyAuditHashChain,
  verifyControlledReissueAuditTrail,
  verifyCriticalEventAuditTrail,
  verifyTechnicalReviewSignatureAudit,
  type AuditChainEntry,
} from "@afere/audit-log";
import type {
  AuditTrailCatalog,
  AuditTrailDetail,
  AuditTrailEventItem,
  AuditTrailScenario,
  AuditTrailScenarioId,
  EmissionDryRunScenarioId,
  EmissionWorkspaceScenarioId,
  PublicCertificateScenarioId,
  RegistryOperationalStatus,
  ServiceOrderReviewScenarioId,
} from "@afere/contracts";

type AuditEventPayload = {
  action: string;
  actorId?: string;
  actorLabel: string;
  entityId: string;
  entityLabel: string;
  timestampUtc: string;
  deviceId?: string;
  previousCertificateHash?: string;
  previousRevision?: string;
  newRevision?: string;
  recipient?: string;
};

type AuditTrailScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedEventId: string;
  windowLabel: string;
  actorLabel: string;
  actionLabel: string;
  entityLabel: string;
  workspaceScenarioId?: EmissionWorkspaceScenarioId;
  serviceOrderScenarioId?: ServiceOrderReviewScenarioId;
  reviewItemId?: string;
  dryRunScenarioId?: EmissionDryRunScenarioId;
  publicCertificateScenarioId?: PublicCertificateScenarioId;
  events: Array<{
    id: string;
    payload: AuditEventPayload;
    tamperHash?: boolean;
  }>;
};

const PREVIOUS_CERTIFICATE_HASH = "a".repeat(64);
const GENESIS_HASH = "0".repeat(64);

const SCENARIOS: Record<AuditTrailScenarioId, AuditTrailScenarioDefinition> = {
  "recent-emission": {
    label: "Emissao recente com hash-chain integra",
    description: "Recorte com OS recente emitida, eventos criticos completos e trilha pronta para exportacao.",
    recommendedAction: "Seguir com a operacao normal e exportar a trilha apenas quando auditoria ou cliente solicitarem evidencias.",
    selectedEventId: "audit-4",
    windowLabel: "Ultimos 7 dias",
    actorLabel: "Todos",
    actionLabel: "Todas",
    entityLabel: "OS-2026-00142",
    workspaceScenarioId: "baseline-ready",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
    dryRunScenarioId: "type-b-ready",
    publicCertificateScenarioId: "authentic",
    events: [
      {
        id: "audit-1",
        payload: {
          action: "calibration.executed",
          actorId: "tech-1",
          actorLabel: "Joao Executor",
          entityId: "OS-2026-00142",
          entityLabel: "OS-2026-00142",
          timestampUtc: "2026-04-19T14:15:30Z",
          deviceId: "device-field-01",
        },
      },
      {
        id: "audit-2",
        payload: {
          action: "technical_review.completed",
          actorId: "reviewer-1",
          actorLabel: "Maria Souza",
          entityId: "OS-2026-00142",
          entityLabel: "OS-2026-00142",
          timestampUtc: "2026-04-19T14:18:11Z",
          deviceId: "device-review-01",
        },
      },
      {
        id: "audit-3",
        payload: {
          action: "certificate.signed",
          actorId: "signatory-1",
          actorLabel: "Carlos Lima",
          entityId: "CERT-AFR-000124",
          entityLabel: "CERT-AFR-000124",
          timestampUtc: "2026-04-19T14:22:42Z",
          deviceId: "device-sign-01",
        },
      },
      {
        id: "audit-4",
        payload: {
          action: "certificate.emitted",
          actorId: "system",
          actorLabel: "Sistema",
          entityId: "CERT-AFR-000124",
          entityLabel: "CERT-AFR-000124",
          timestampUtc: "2026-04-19T14:22:45Z",
          deviceId: "backend-emission-01",
        },
      },
    ],
  },
  "reissue-attention": {
    label: "Reemissao controlada em evidencia",
    description: "Recorte com reemissao controlada, dupla aprovacao e notificacao ao cliente preservadas na cadeia.",
    recommendedAction: "Conferir a notificacao da reemissao e manter a trilha pronta para consulta do cliente e auditoria.",
    selectedEventId: "audit-7",
    windowLabel: "Ultimos 30 dias",
    actorLabel: "Todos",
    actionLabel: "Reemissao",
    entityLabel: "CERT-AFR-000118",
    workspaceScenarioId: "team-attention",
    serviceOrderScenarioId: "history-pending",
    reviewItemId: "os-2026-00141",
    dryRunScenarioId: "type-b-ready",
    publicCertificateScenarioId: "reissued",
    events: [
      {
        id: "audit-1",
        payload: {
          action: "calibration.executed",
          actorId: "tech-1",
          actorLabel: "Joao Executor",
          entityId: "OS-2026-00141",
          entityLabel: "OS-2026-00141",
          timestampUtc: "2026-04-18T10:10:00Z",
          deviceId: "device-field-01",
        },
      },
      {
        id: "audit-2",
        payload: {
          action: "technical_review.completed",
          actorId: "reviewer-1",
          actorLabel: "Maria Souza",
          entityId: "OS-2026-00141",
          entityLabel: "OS-2026-00141",
          timestampUtc: "2026-04-18T13:10:00Z",
          deviceId: "device-review-01",
        },
      },
      {
        id: "audit-3",
        payload: {
          action: "certificate.signed",
          actorId: "signatory-1",
          actorLabel: "Carlos Lima",
          entityId: "CERT-AFR-000118",
          entityLabel: "CERT-AFR-000118",
          timestampUtc: "2026-04-18T13:20:00Z",
          deviceId: "device-sign-01",
        },
      },
      {
        id: "audit-4",
        payload: {
          action: "certificate.emitted",
          actorId: "system",
          actorLabel: "Sistema",
          entityId: "CERT-AFR-000118",
          entityLabel: "CERT-AFR-000118",
          timestampUtc: "2026-04-18T13:20:05Z",
          deviceId: "backend-emission-01",
        },
      },
      {
        id: "audit-5",
        payload: {
          action: "certificate.reissue.approved",
          actorId: "reviewer-1",
          actorLabel: "Maria Souza",
          entityId: "CERT-AFR-000118",
          entityLabel: "CERT-AFR-000118",
          timestampUtc: "2026-04-21T08:00:00Z",
        },
      },
      {
        id: "audit-6",
        payload: {
          action: "certificate.reissue.approved",
          actorId: "signatory-2",
          actorLabel: "Renata Qualidade",
          entityId: "CERT-AFR-000118",
          entityLabel: "CERT-AFR-000118",
          timestampUtc: "2026-04-21T08:05:00Z",
        },
      },
      {
        id: "audit-7",
        payload: {
          action: "certificate.reissued",
          actorId: "system",
          actorLabel: "Sistema",
          entityId: "CERT-AFR-000118-R1",
          entityLabel: "CERT-AFR-000118-R1",
          timestampUtc: "2026-04-21T08:08:00Z",
          previousCertificateHash: PREVIOUS_CERTIFICATE_HASH,
          previousRevision: "R0",
          newRevision: "R1",
        },
      },
      {
        id: "audit-8",
        payload: {
          action: "certificate.reissue.notified",
          actorId: "system",
          actorLabel: "Sistema",
          entityId: "CERT-AFR-000118-R1",
          entityLabel: "CERT-AFR-000118-R1",
          timestampUtc: "2026-04-21T08:09:00Z",
          recipient: "cliente@industriaxyz.com.br",
        },
      },
    ],
  },
  "integrity-blocked": {
    label: "Divergencia de integridade na trilha",
    description: "Recorte com falha de integridade ou ausencia de evento critico, mantendo a operacao em fail-closed.",
    recommendedAction: "Interromper a exportacao e abrir investigacao antes de reutilizar esta cadeia em qualquer fluxo regulado.",
    selectedEventId: "audit-3",
    windowLabel: "Ultimos 7 dias",
    actorLabel: "Todos",
    actionLabel: "Assinatura",
    entityLabel: "OS-2026-00147",
    workspaceScenarioId: "release-blocked",
    serviceOrderScenarioId: "review-blocked",
    reviewItemId: "os-2026-00147",
    dryRunScenarioId: "type-c-blocked",
    publicCertificateScenarioId: "not-found",
    events: [
      {
        id: "audit-1",
        payload: {
          action: "calibration.executed",
          actorId: "tech-1",
          actorLabel: "Joao Executor",
          entityId: "OS-2026-00147",
          entityLabel: "OS-2026-00147",
          timestampUtc: "2026-04-19T10:10:00Z",
          deviceId: "device-field-01",
        },
      },
      {
        id: "audit-2",
        payload: {
          action: "technical_review.completed",
          actorId: "reviewer-1",
          actorLabel: "Maria Souza",
          entityId: "OS-2026-00147",
          entityLabel: "OS-2026-00147",
          timestampUtc: "2026-04-19T12:00:00Z",
          deviceId: "device-review-01",
        },
      },
      {
        id: "audit-3",
        payload: {
          action: "certificate.signed",
          actorId: "signatory-1",
          actorLabel: "Carlos Lima",
          entityId: "CERT-AFR-000147",
          entityLabel: "CERT-AFR-000147",
          timestampUtc: "2026-04-19T12:15:00Z",
          deviceId: "device-sign-01",
        },
        tamperHash: true,
      },
      {
        id: "audit-4",
        payload: {
          action: "certificate.emitted",
          actorId: "system",
          actorLabel: "Sistema",
          entityId: "CERT-AFR-000147",
          entityLabel: "CERT-AFR-000147",
          timestampUtc: "2026-04-19T12:16:00Z",
          deviceId: "backend-emission-01",
        },
      },
    ],
  },
};

const DEFAULT_SCENARIO: AuditTrailScenarioId = "recent-emission";

export function listAuditTrailScenarios(): AuditTrailScenario[] {
  return (Object.keys(SCENARIOS) as AuditTrailScenarioId[]).map((scenarioId) =>
    resolveAuditTrailScenario(scenarioId),
  );
}

export function resolveAuditTrailScenario(
  scenarioId?: string,
  eventId?: string,
): AuditTrailScenario {
  const definition = SCENARIOS[isAuditTrailScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO];
  const entries = buildAuditEntries(definition);
  const status = resolveScenarioStatus(entries);
  const items = entries.map((entry) => buildAuditTrailEventItem(entries, entry));
  const selectedEvent =
    items.find((item) => item.eventId === eventId) ??
    items.find((item) => item.eventId === definition.selectedEventId) ??
    items[0];

  if (!selectedEvent) {
    throw new Error("missing_audit_trail_items");
  }

  const detail = buildAuditTrailDetail(definition, entries, selectedEvent.eventId, status);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildAuditTrailSummary(definition.recommendedAction, entries, detail, status),
    selectedEventId: selectedEvent.eventId,
    items,
    detail,
  };
}

export function buildAuditTrailCatalog(
  scenarioId?: string,
  eventId?: string,
): AuditTrailCatalog {
  const selectedScenario = resolveAuditTrailScenario(scenarioId, eventId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listAuditTrailScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildAuditEntries(definition: AuditTrailScenarioDefinition): AuditChainEntry[] {
  const entries: AuditChainEntry[] = [];
  let previousHash = GENESIS_HASH;

  for (const event of definition.events) {
    const computedHash = computeAuditHash(previousHash, event.payload);
    const hash = event.tamperHash ? `${computedHash.slice(0, -1)}x` : computedHash;

    entries.push({
      id: event.id,
      prevHash: previousHash,
      payload: event.payload,
      hash,
    });

    previousHash = hash;
  }

  return entries;
}

function buildAuditTrailEventItem(
  entries: AuditChainEntry[],
  entry: AuditChainEntry,
): AuditTrailEventItem {
  const hashChain = verifyAuditHashChain(entries);
  const reissue = verifyControlledReissueAuditTrail(entries);

  return {
    eventId: entry.id,
    occurredAtLabel: readTimestamp(entry.payload),
    actorLabel: readActor(entry.payload),
    actionLabel: readAction(entry.payload),
    entityLabel: readEntity(entry.payload),
    hashLabel: `${entry.hash.slice(0, 4)}.`,
    status:
      hashChain.firstInvalid?.id === entry.id
        ? "blocked"
        : readAction(entry.payload).includes("reissue")
          ? reissue.ok
            ? "attention"
            : "blocked"
          : "ready",
  };
}

function buildAuditTrailDetail(
  definition: AuditTrailScenarioDefinition,
  entries: AuditChainEntry[],
  selectedEventId: string,
  status: RegistryOperationalStatus,
): AuditTrailDetail {
  const hashChain = verifyAuditHashChain(entries);
  const requireReissue = hasReissue(entries);
  const critical = verifyCriticalEventAuditTrail(entries, { requireReissue });
  const reviewSignature = verifyTechnicalReviewSignatureAudit(entries);
  const reissue = verifyControlledReissueAuditTrail(entries);

  if (!entries.some((entry) => entry.id === selectedEventId)) {
    throw new Error(`missing_audit_trail_event:${selectedEventId}`);
  }

  const blockers = uniqueStrings([
    ...(hashChain.ok
      ? []
      : [`Hash-chain divergente em ${hashChain.firstInvalid?.id ?? "evento desconhecido"}.`]),
    ...critical.missingActions.map((action) => `Evento critico ausente: ${action}.`),
    ...reviewSignature.invalidEntries.map(
      (issue) => `Metadado invalido em ${issue.action}: ${issue.invalidFields.join(", ")}.`,
    ),
    ...reviewSignature.missingActions.map((action) => `Evento obrigatorio ausente: ${action}.`),
    ...reissue.approvalErrors.map(renderReissueApprovalError),
    ...reissue.sequenceErrors.map(renderReissueSequenceError),
    ...(requireReissue ? reissue.missingActions.map((action) => `Evento de reemissao ausente: ${action}.`) : []),
  ]);
  const warnings = uniqueStrings([
    ...(requireReissue && reissue.ok ? ["Cadeia contem reemissao controlada ja notificada ao cliente."] : []),
    ...(status === "attention" ? ["Fluxo sensivel: manter exportacao sob revisao do gestor da qualidade."] : []),
  ]);

  return {
    chainId: definition.entityLabel,
    title: `${definition.entityLabel} · ${definition.actionLabel}`,
    status,
    noticeLabel:
      status === "ready"
        ? "Trilha integra e pronta para consulta."
        : status === "attention"
          ? "Trilha integra, mas com evento sensivel que exige leitura cuidadosa."
          : "Trilha bloqueada por integridade ou cobertura critica insuficiente.",
    selectedWindowLabel: definition.windowLabel,
    selectedActorLabel: definition.actorLabel,
    selectedEntityLabel: definition.entityLabel,
    selectedActionLabel: definition.actionLabel,
    chainStatusLabel:
      hashChain.ok && critical.ok && reviewSignature.ok && (!requireReissue || reissue.ok)
        ? "Hash-chain integra e criterios criticos satisfeitos"
        : "Fail-closed: divergencia ou criterio critico ausente",
    exportLabel:
      status === "blocked"
        ? "Exportacao bloqueada ate investigacao"
        : status === "attention"
          ? "Exportacao liberada com ressalva de revisao"
          : "Exportacao pronta para auditoria",
    coveredActions: coveredActions(entries),
    selectedEventContextFields: [],
    missingActions: uniqueStrings([
      ...critical.missingActions,
      ...reviewSignature.missingActions,
      ...(requireReissue ? reissue.missingActions : []),
    ]),
    blockers,
    warnings,
    links: {
      workspaceScenarioId: definition.workspaceScenarioId,
      serviceOrderScenarioId: definition.serviceOrderScenarioId,
      reviewItemId: definition.reviewItemId,
      dryRunScenarioId: definition.dryRunScenarioId,
      publicCertificateScenarioId: definition.publicCertificateScenarioId,
    },
  };
}

function buildAuditTrailSummary(
  recommendedAction: string,
  entries: AuditChainEntry[],
  detail: AuditTrailDetail,
  status: RegistryOperationalStatus,
): AuditTrailScenario["summary"] {
  return {
    status,
    headline:
      status === "ready"
        ? "Trilha de auditoria integra e pronta para consulta"
        : status === "attention"
          ? "Trilha integra com reemissao controlada em destaque"
          : "Trilha bloqueada por divergencia de integridade",
    totalEvents: entries.length,
    criticalEvents: entries.filter((entry) =>
      [
        "calibration.executed",
        "technical_review.completed",
        "certificate.signed",
        "certificate.emitted",
        "certificate.reissued",
      ].includes(readAction(entry.payload)),
    ).length,
    reissueEvents: entries.filter((entry) => readAction(entry.payload).includes("reissue")).length,
    integrityFailures: detail.blockers.some((item) => item.includes("Hash-chain divergente")) ? 1 : 0,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function resolveScenarioStatus(entries: AuditChainEntry[]): RegistryOperationalStatus {
  const hashChain = verifyAuditHashChain(entries);
  const requireReissue = hasReissue(entries);
  const critical = verifyCriticalEventAuditTrail(entries, { requireReissue });
  const reviewSignature = verifyTechnicalReviewSignatureAudit(entries);
  const reissue = verifyControlledReissueAuditTrail(entries);

  if (!hashChain.ok || !critical.ok || !reviewSignature.ok || (requireReissue && !reissue.ok)) {
    return "blocked";
  }

  if (requireReissue && reissue.ok) {
    return "attention";
  }

  return "ready";
}

function hasReissue(entries: AuditChainEntry[]): boolean {
  return entries.some((entry) => readAction(entry.payload).includes("reissue"));
}

function coveredActions(entries: AuditChainEntry[]): string[] {
  return uniqueStrings(entries.map((entry) => readAction(entry.payload)));
}

function renderReissueApprovalError(error: string): string {
  switch (error) {
    case "approvals_below_minimum":
      return "Reemissao sem duas aprovacoes registradas.";
    case "approvers_not_distinct":
      return "Reemissao com aprovadores nao distintos.";
    default:
      return error;
  }
}

function renderReissueSequenceError(error: string): string {
  switch (error) {
    case "notification_must_follow_reissue":
      return "Notificacao ao cliente registrada antes da reemissao.";
    default:
      return error;
  }
}

function readTimestamp(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "sem timestamp";
  }

  const timestamp = (payload as { timestampUtc?: unknown }).timestampUtc;
  return typeof timestamp === "string" ? timestamp.replace("T", " ").replace("Z", " UTC") : "sem timestamp";
}

function readActor(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "Desconhecido";
  }

  const actor = (payload as { actorLabel?: unknown }).actorLabel;
  return typeof actor === "string" ? actor : "Desconhecido";
}

function readAction(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "acao.desconhecida";
  }

  const action = (payload as { action?: unknown }).action;
  return typeof action === "string" ? action : "acao.desconhecida";
}

function readEntity(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "Entidade desconhecida";
  }

  const entity = (payload as { entityLabel?: unknown }).entityLabel;
  return typeof entity === "string" ? entity : "Entidade desconhecida";
}

function resolveScenarioId(scenarioId?: string): AuditTrailScenarioId {
  return isAuditTrailScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function isAuditTrailScenarioId(value: string | undefined): value is AuditTrailScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}
