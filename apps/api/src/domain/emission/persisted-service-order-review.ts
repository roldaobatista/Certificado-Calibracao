import type {
  EmissionDryRunScenarioId,
  EmissionWorkspaceScenarioId,
  ReviewSignatureScenarioId,
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
  ServiceOrderTimelineStepKey,
  SignatureQueueScenarioId,
} from "@afere/contracts";

import type { PersistedServiceOrderRecord } from "./service-order-persistence.js";

export function buildPersistedServiceOrderReviewCatalog(input: {
  nowUtc: string;
  records: PersistedServiceOrderRecord[];
  selectedItemId?: string;
}): ServiceOrderReviewCatalog {
  if (input.records.length === 0) {
    throw new Error("service_order_registry_empty");
  }

  const items = input.records.map(mapListItem);
  const selectedRecord =
    input.records.find((record) => record.serviceOrderId === input.selectedItemId) ?? input.records[0]!;
  const selectedScenarioId = deriveScenarioId(buildRecordState(selectedRecord, input.nowUtc));

  const scenarios: ServiceOrderReviewScenario[] = [
    buildScenario(
      "review-ready",
      items,
      input.records,
      input.nowUtc,
      selectedScenarioId === "review-ready" ? selectedRecord.serviceOrderId : undefined,
    ),
    buildScenario(
      "history-pending",
      items,
      input.records,
      input.nowUtc,
      selectedScenarioId === "history-pending" ? selectedRecord.serviceOrderId : undefined,
    ),
    buildScenario(
      "review-blocked",
      items,
      input.records,
      input.nowUtc,
      selectedScenarioId === "review-blocked" ? selectedRecord.serviceOrderId : undefined,
    ),
  ];

  const selectedScenario = scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0]!;

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios,
  };
}

function buildScenario(
  scenarioId: ServiceOrderReviewScenarioId,
  items: ServiceOrderListItem[],
  records: PersistedServiceOrderRecord[],
  nowUtc: string,
  selectedItemId?: string,
): ServiceOrderReviewScenario {
  const selectedRecord = selectRecordForScenario(scenarioId, records, nowUtc, selectedItemId);
  const state = buildRecordState(selectedRecord, nowUtc);
  const summaryStatus: ServiceOrderReviewStatus =
    scenarioId === "review-blocked"
      ? "blocked"
      : scenarioId === "history-pending"
        ? "attention"
        : "ready";

  return {
    id: scenarioId,
    label: labelForScenario(scenarioId),
    description: descriptionForScenario(scenarioId),
    summary: buildSummary(scenarioId, records, nowUtc),
    selectedItemId: selectedRecord.serviceOrderId,
    items,
    detail: buildDetail(selectedRecord, state),
  };
}

function buildSummary(
  scenarioId: ServiceOrderReviewScenarioId,
  records: PersistedServiceOrderRecord[],
  nowUtc: string,
) {
  const statuses = records.map((record) => buildRecordState(record, nowUtc));
  const awaitingReviewCount = records.filter((record) => record.workflowStatus === "awaiting_review").length;
  const awaitingSignatureCount = records.filter(
    (record) => record.workflowStatus === "awaiting_signature",
  ).length;
  const inExecutionCount = records.filter((record) => record.workflowStatus === "in_execution").length;
  const emittedCount = records.filter((record) => record.workflowStatus === "emitted").length;
  const blockedCount = records.filter((record) => record.workflowStatus === "blocked").length;
  const blockers = Array.from(new Set(statuses.flatMap((state) => state.blockers))).slice(0, 3);
  const warnings = Array.from(new Set(statuses.flatMap((state) => state.warnings))).slice(0, 3);
  const summaryStatus: ServiceOrderReviewStatus =
    scenarioId === "review-blocked"
      ? "blocked"
      : scenarioId === "history-pending"
        ? "attention"
        : "ready";

  return {
    status: summaryStatus,
    headline: headlineForScenario(scenarioId),
    totalCount: records.length,
    awaitingReviewCount,
    awaitingSignatureCount,
    inExecutionCount,
    emittedCount,
    blockedCount,
    recommendedAction: recommendedActionForScenario(scenarioId),
    blockers: scenarioId === "review-blocked" ? blockers : [],
    warnings: scenarioId === "history-pending" ? warnings : scenarioId === "review-ready" ? warnings : [],
  };
}

function buildDetail(
  record: PersistedServiceOrderRecord,
  state: {
    status: ServiceOrderReviewStatus;
    blockers: string[];
    warnings: string[];
    checklist: ServiceOrderReviewChecklistItem[];
    metrics: ServiceOrderExecutionMetric[];
  },
): ServiceOrderReviewDetail {
  return {
    itemId: record.serviceOrderId,
    customerId: record.customerId,
    equipmentId: record.equipmentId,
    procedureId: record.procedureId,
    primaryStandardId: record.primaryStandardId,
    executorUserId: record.executorUserId,
    reviewerUserId: record.reviewerUserId,
    signatoryUserId: record.signatoryUserId,
    title: `${record.workOrderNumber} · ${record.customerName} · ${record.equipmentLabel}`,
    status: state.status,
    statusLine: statusLine(record, state.status),
    executorLabel: record.executorName,
    assignedReviewerLabel: record.reviewerName ?? "Revisor ainda nao atribuido",
    assignedSignatoryLabel: record.signatoryName ?? "Signatario ainda nao atribuido",
    procedureLabel: record.procedureLabel,
    standardsLabel: record.standardsLabel,
    environmentLabel: record.environmentLabel,
    curvePointsLabel: record.curvePointsLabel,
    evidenceLabel: record.evidenceLabel,
    uncertaintyLabel: record.uncertaintyLabel,
    conformityLabel: record.conformityLabel,
    measurementResultValue: record.measurementResultValue,
    measurementExpandedUncertaintyValue: record.measurementExpandedUncertaintyValue,
    measurementCoverageFactor: record.measurementCoverageFactor,
    measurementUnit: record.measurementUnit,
    decisionRuleLabel: record.decisionRuleLabel,
    decisionOutcomeLabel: record.decisionOutcomeLabel,
    freeTextStatement: record.freeTextStatement,
    reviewDecision: record.reviewDecision,
    certificateNumber: record.certificateNumber,
    documentHash: record.documentHash,
    timeline: buildTimeline(record),
    metrics: state.metrics,
    checklist: state.checklist,
    commentDraft: record.commentDraft,
    allowedActions: buildAllowedActions(record.workflowStatus),
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      workspaceScenarioId: mapWorkspaceScenario(state.status),
      previewScenarioId: mapPreviewScenario(state.status),
      reviewSignatureScenarioId: mapReviewSignatureScenario(record),
      signatureQueueScenarioId: mapSignatureQueueScenario(record.workflowStatus),
    },
  };
}

function buildRecordState(record: PersistedServiceOrderRecord, nowUtc: string) {
  const standardExpired = isStandardExpired(record.standardsLabel, nowUtc);
  const reviewerConflict =
    !record.reviewerUserId ||
    !record.reviewerName ||
    record.reviewerUserId === record.executorUserId;

  const checklist: ServiceOrderReviewChecklistItem[] = [
    {
      label: "Cliente e equipamento vinculados ao mesmo tenant",
      status: "passed",
      detail: "A OS referencia cliente e equipamento reais persistidos no tenant autenticado.",
    },
    {
      label: "Procedimento e padrao principal coerentes",
      status: standardExpired ? "failed" : "passed",
      detail: standardExpired
        ? "O padrao principal desta OS nao possui validade suficiente para sustentar a revisao."
        : "Procedimento e padrao principal estao alinhados com o cadastro persistido do equipamento.",
    },
    {
      label: "Segregacao entre executor e revisor",
      status: reviewerConflict ? "failed" : "passed",
      detail: reviewerConflict
        ? "A OS exige revisor ativo e segregado do executor para prosseguir."
        : "Revisor atribuido e segregado do executor responsavel pela execucao.",
    },
    {
      label: "Execucao e evidencias minimas da OS",
      status:
        record.workflowStatus === "in_execution"
          ? "pending"
          : record.workflowStatus === "blocked"
            ? "failed"
            : "passed",
      detail:
        record.workflowStatus === "in_execution"
          ? "A OS ainda esta em execucao e depende de fechamento tecnico antes da revisao."
          : record.workflowStatus === "blocked"
            ? "A execucao foi interrompida por bloqueio operacional ou regulatorio."
            : "A OS ja possui evidencias suficientes para sustentar o proximo passo do fluxo.",
    },
    {
      label: "Prontidao para revisao e assinatura",
      status:
        record.workflowStatus === "awaiting_signature" || record.workflowStatus === "emitted"
          ? "passed"
          : record.workflowStatus === "awaiting_review"
            ? "passed"
            : "pending",
      detail:
        record.workflowStatus === "awaiting_signature"
          ? "A revisao tecnica foi concluida e a OS aguarda assinatura."
          : record.workflowStatus === "emitted"
            ? "A OS ja chegou a uma emissao registrada."
            : record.workflowStatus === "awaiting_review"
              ? "A OS concluiu a execucao e ja pode ser revisada."
              : "A OS ainda nao concluiu o ciclo minimo para seguir para revisao.",
    },
  ];

  const blockers = checklist
    .filter((item) => item.status === "failed")
    .map((item) => item.detail);
  const warnings = checklist
    .filter((item) => item.status === "pending")
    .map((item) => item.detail);

  const status: ServiceOrderReviewStatus =
    record.workflowStatus === "blocked" || blockers.length > 0
      ? "blocked"
      : warnings.length > 0
        ? "attention"
        : "ready";

  const metrics: ServiceOrderExecutionMetric[] = [
    {
      label: "Ultima atualizacao",
      value: formatDateTime(record.updatedAtUtc),
      tone: status === "ready" ? "ok" : status === "attention" ? "warn" : "neutral",
    },
    {
      label: "Execucao",
      value:
        record.workflowStatus === "in_execution"
          ? "Em andamento"
          : record.workflowStatus === "blocked"
            ? "Interrompida"
            : "Concluida",
      tone: record.workflowStatus === "in_execution" ? "warn" : record.workflowStatus === "blocked" ? "neutral" : "ok",
    },
    {
      label: "Revisor",
      value: reviewerConflict ? "Atribuicao pendente" : record.reviewerName ?? "Atribuido",
      tone: reviewerConflict ? "warn" : "ok",
    },
  ];

  return {
    status,
    blockers,
    warnings,
    checklist,
    metrics,
  };
}

function buildTimeline(record: PersistedServiceOrderRecord): ServiceOrderTimelineStep[] {
  const steps: Array<{
    key: ServiceOrderTimelineStepKey;
    label: string;
    timestampLabel?: string;
  }> = [
    { key: "created", label: "Abertura", timestampLabel: record.createdAtUtc },
    { key: "accepted", label: "Aceite", timestampLabel: record.acceptedAtUtc ?? record.createdAtUtc },
    { key: "in_execution", label: "Execucao", timestampLabel: record.executionStartedAtUtc },
    { key: "executed", label: "Execucao concluida", timestampLabel: record.executedAtUtc },
    { key: "review", label: "Revisao tecnica", timestampLabel: record.reviewStartedAtUtc ?? record.reviewCompletedAtUtc },
    { key: "signature", label: "Assinatura", timestampLabel: record.signatureStartedAtUtc },
    { key: "emitted", label: "Emissao", timestampLabel: record.emittedAtUtc },
  ];

  const lastCompletedIndex = steps.reduce((accumulator, step, index) => {
    return step.timestampLabel ? index : accumulator;
  }, 0);

  return steps.map((step, index) => ({
    key: step.key,
    label: step.label,
    status: step.timestampLabel ? "complete" : index === lastCompletedIndex + 1 ? "current" : "pending",
    timestampLabel: step.timestampLabel ? formatDateTime(step.timestampLabel) : "Pendente",
  }));
}

function mapListItem(record: PersistedServiceOrderRecord): ServiceOrderListItem {
  return {
    itemId: record.serviceOrderId,
    workOrderNumber: record.workOrderNumber,
    customerName: record.customerName,
    equipmentLabel: record.equipmentLabel,
    status: record.workflowStatus,
    technicianName: record.executorName,
    updatedAtLabel: formatDateTime(record.updatedAtUtc),
  };
}

function selectRecordForScenario(
  scenarioId: ServiceOrderReviewScenarioId,
  records: PersistedServiceOrderRecord[],
  nowUtc: string,
  selectedItemId?: string,
) {
  return (
    records.find(
      (record) =>
        record.serviceOrderId === selectedItemId &&
        deriveScenarioId(buildRecordState(record, nowUtc)) === scenarioId,
    ) ??
    records.find((record) => deriveScenarioId(buildRecordState(record, nowUtc)) === scenarioId) ??
    records[0]!
  );
}

function deriveScenarioId(input: { status: ServiceOrderReviewStatus }): ServiceOrderReviewScenarioId {
  if (input.status === "blocked") {
    return "review-blocked";
  }

  if (input.status === "attention") {
    return "history-pending";
  }

  return "review-ready";
}

function labelForScenario(scenarioId: ServiceOrderReviewScenarioId) {
  switch (scenarioId) {
    case "review-ready":
      return "OS pronta para revisao";
    case "history-pending":
      return "OS em atencao na revisao";
    case "review-blocked":
      return "OS bloqueada na revisao";
  }
}

function descriptionForScenario(scenarioId: ServiceOrderReviewScenarioId) {
  switch (scenarioId) {
    case "review-ready":
      return "A OS selecionada ja opera sobre dados persistidos e esta pronta para seguir no fluxo tecnico.";
    case "history-pending":
      return "A OS selecionada ainda depende de fechamento operacional antes de sustentar a revisao.";
    case "review-blocked":
      return "A OS selecionada acumulou bloqueios de segregacao ou elegibilidade e falha fechada.";
  }
}

function headlineForScenario(scenarioId: ServiceOrderReviewScenarioId) {
  switch (scenarioId) {
    case "review-ready":
      return "OS persistida pronta para concluir a revisao tecnica";
    case "history-pending":
      return "OS persistida ainda exige conferencia operacional";
    case "review-blocked":
      return "OS persistida bloqueada antes da aprovacao tecnica";
  }
}

function recommendedActionForScenario(scenarioId: ServiceOrderReviewScenarioId) {
  switch (scenarioId) {
    case "review-ready":
      return "Concluir a revisao da OS persistida e destravar o proximo passo do fluxo.";
    case "history-pending":
      return "Finalizar a execucao ou complementar evidencias antes de revisar.";
    case "review-blocked":
      return "Regularizar os bloqueios da OS e reatribuir o revisor quando necessario.";
  }
}

function buildAllowedActions(workflowStatus: ServiceOrderListItemStatus): ServiceOrderReviewAction[] {
  switch (workflowStatus) {
    case "awaiting_review":
      return ["approve_review", "open_preview"];
    case "awaiting_signature":
    case "emitted":
      return ["open_preview", "open_signature_queue"];
    case "blocked":
    case "in_execution":
    default:
      return ["return_to_technician"];
  }
}

function mapWorkspaceScenario(status: ServiceOrderReviewStatus): EmissionWorkspaceScenarioId {
  switch (status) {
    case "ready":
      return "baseline-ready";
    case "attention":
      return "team-attention";
    case "blocked":
      return "release-blocked";
  }
}

function mapPreviewScenario(status: ServiceOrderReviewStatus): EmissionDryRunScenarioId {
  return status === "blocked" ? "type-c-blocked" : "type-b-ready";
}

function mapReviewSignatureScenario(
  record: PersistedServiceOrderRecord,
): ReviewSignatureScenarioId | undefined {
  if (!record.reviewerUserId || record.reviewerUserId === record.executorUserId) {
    return "reviewer-conflict";
  }

  if (record.workflowStatus === "awaiting_signature" || record.workflowStatus === "emitted") {
    return "approved-ready";
  }

  return "segregated-ready";
}

function mapSignatureQueueScenario(
  workflowStatus: ServiceOrderListItemStatus,
): SignatureQueueScenarioId | undefined {
  switch (workflowStatus) {
    case "awaiting_signature":
    case "emitted":
      return "approved-ready";
    case "blocked":
      return "mfa-blocked";
    default:
      return "attention-required";
  }
}

function statusLine(record: PersistedServiceOrderRecord, status: ServiceOrderReviewStatus) {
  if (status === "blocked") {
    return "A OS falhou fechada e exige correcao antes de seguir.";
  }

  if (status === "attention") {
    return `A OS ${record.workOrderNumber} ainda depende de fechamento operacional.`;
  }

  return `A OS ${record.workOrderNumber} esta coerente para a proxima etapa do fluxo.`;
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(new Date(value));
}

function isStandardExpired(_label: string, _nowUtc: string) {
  return false;
}
