import {
  verifyAuditHashChain,
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
  CertificatePreviewCatalog,
  CertificatePreviewField,
  CertificatePreviewScenario,
  EmissionCertificatePreview,
  EmissionDryRunCatalog,
  EmissionDryRunProfile,
  EmissionDryRunResult,
  EmissionDryRunScenario,
  EmissionDryRunScenarioId,
  PublicCertificateScenarioId,
  RegistryOperationalStatus,
  ReviewSignatureCatalog,
  ReviewSignatureScenario,
  ReviewSignatureScenarioId,
  SignatureApprovalPanel,
  SignatureApprovalRequirement,
  SignatureQueueCatalog,
  SignatureQueueItem,
  SignatureQueueScenario,
  SignatureQueueScenarioId,
  SignatureQueueStatus,
  SignatureQueueValidation,
} from "@afere/contracts";

import type { PersistedOnboardingRecord, PersistedUserRecord } from "../auth/core-persistence.js";
import { runCertificateEmissionDryRun } from "./dry-run.js";
import {
  evaluateReviewSignatureWorkflow,
  type WorkflowMembershipInput,
} from "./review-signature-workflow.js";
import type {
  PersistedEmissionAuditEvent,
  PersistedServiceOrderRecord,
} from "./service-order-persistence.js";

type PersistedFlowInput = {
  nowUtc: string;
  records: PersistedServiceOrderRecord[];
  users: PersistedUserRecord[];
  onboarding: PersistedOnboardingRecord;
  selectedItemId?: string;
};

type PersistedAuditTrailInput = PersistedFlowInput & {
  auditEvents: PersistedEmissionAuditEvent[];
  selectedEventId?: string;
};

type FlowState = {
  record: PersistedServiceOrderRecord;
  dryRunScenarioId: EmissionDryRunScenarioId;
  dryRunResult: EmissionDryRunResult;
  preview: EmissionCertificatePreview;
  reviewScenarioId: ReviewSignatureScenarioId;
  reviewScenario: ReviewSignatureScenario;
  queueStatus: SignatureQueueStatus;
  queueValidations: SignatureQueueValidation[];
  queueBlockers: string[];
  queueWarnings: string[];
};

export function buildPersistedEmissionDryRunCatalog(input: PersistedFlowInput): EmissionDryRunCatalog {
  const states = buildFlowStates(input);
  const selectedState = selectState(states, input.selectedItemId);
  const selectedScenarioId = selectedState.dryRunScenarioId;

  return {
    selectedScenarioId,
    scenarios: DRY_RUN_SCENARIOS.map((scenarioId) =>
      buildDryRunScenario(selectScenarioState(states, scenarioId, selectedState), scenarioId),
    ),
  };
}

export function buildPersistedCertificatePreviewCatalog(
  input: PersistedFlowInput,
): CertificatePreviewCatalog {
  const states = buildFlowStates(input);
  const selectedState = selectState(states, input.selectedItemId);
  const selectedScenarioId = selectedState.dryRunScenarioId;

  return {
    selectedScenarioId,
    scenarios: DRY_RUN_SCENARIOS.map((scenarioId) =>
      buildPreviewScenario(selectScenarioState(states, scenarioId, selectedState), scenarioId),
    ),
  };
}

export function buildPersistedReviewSignatureCatalog(
  input: PersistedFlowInput,
): ReviewSignatureCatalog {
  const states = buildFlowStates(input);
  const selectedState = selectState(states, input.selectedItemId);
  const selectedScenarioId = selectedState.reviewScenarioId;

  return {
    selectedScenarioId,
    scenarios: REVIEW_SCENARIOS.map((scenarioId) => {
      const state = selectReviewScenarioState(states, scenarioId, selectedState);
      return {
        ...state.reviewScenario,
        id: scenarioId,
        label: reviewScenarioLabel(scenarioId),
        description: reviewScenarioDescription(scenarioId, state.record.workOrderNumber),
      };
    }),
  };
}

export function buildPersistedSignatureQueueCatalog(
  input: PersistedFlowInput,
): SignatureQueueCatalog {
  const states = buildFlowStates(input);
  const selectedState = selectState(states, input.selectedItemId);
  const selectedScenarioId = deriveQueueScenarioId(selectedState.queueStatus);

  return {
    selectedScenarioId,
    scenarios: QUEUE_SCENARIOS.map((scenarioId) =>
      buildQueueScenario(states, selectedState, scenarioId),
    ),
  };
}

export function buildPersistedAuditTrailCatalog(
  input: PersistedAuditTrailInput,
): AuditTrailCatalog {
  const states = buildFlowStates(input);
  const selectedState = selectState(states, input.selectedItemId);
  const groupedEvents = groupAuditEventsByServiceOrder(input.auditEvents);
  const selectedEvents = groupedEvents.get(selectedState.record.serviceOrderId) ?? [];
  const selectedScenarioId = deriveAuditScenarioId(selectedState.record, selectedEvents);

  return {
    selectedScenarioId,
    scenarios: AUDIT_SCENARIOS.map((scenarioId) =>
      buildAuditScenario({
        scenarioId,
        states,
        selectedState,
        groupedEvents,
        selectedEventId: input.selectedEventId,
      }),
    ),
  };
}

const DRY_RUN_SCENARIOS: EmissionDryRunScenarioId[] = [
  "type-b-ready",
  "type-a-suppressed",
  "type-c-blocked",
];

const REVIEW_SCENARIOS: ReviewSignatureScenarioId[] = [
  "approved-ready",
  "segregated-ready",
  "reviewer-conflict",
  "signatory-mfa-blocked",
];

const QUEUE_SCENARIOS: SignatureQueueScenarioId[] = [
  "approved-ready",
  "attention-required",
  "mfa-blocked",
];

const AUDIT_SCENARIOS: AuditTrailScenarioId[] = [
  "recent-emission",
  "reissue-attention",
  "integrity-blocked",
];

function buildFlowStates(input: PersistedFlowInput): FlowState[] {
  const userMap = new Map(input.users.map((user) => [user.userId, user]));
  const organizationCode = deriveOrganizationCode(input.onboarding.organizationSlug);
  const profile = mapRegulatoryProfile(input.onboarding.regulatoryProfile);
  const issuedNumbers = input.records
    .filter((record) => record.certificateNumber)
    .map((record) => ({
      organizationId: record.organizationId,
      certificateNumber: record.certificateNumber!,
    }));

  return input.records.map((record) => {
    const signatory = resolveAssignedUser(record.signatoryUserId, userMap);
    const reviewer = resolveAssignedUser(record.reviewerUserId, userMap);
    const reviewScenario = buildReviewScenario({
      record,
      users: input.users,
      records: input.records,
    });
    const dryRunResult = runCertificateEmissionDryRun({
      organization: {
        organizationId: record.organizationId,
        organizationCode,
        profile,
        displayName: input.onboarding.organizationName,
      },
      equipment: {
        customerId: record.customerId,
        customerName: record.customerName,
        address: record.customerAddress,
        instrumentType: record.instrumentType,
        instrumentDescription: record.equipmentLabel,
        serialNumber: record.equipmentSerialNumber,
        tagCode: record.equipmentTagCode,
      },
      standard: {
        source: record.standardSource,
        calibrationDate: record.executedAtUtc ?? input.nowUtc,
        hasValidCertificate: record.standardHasValidCertificate,
        certificateValidUntil: record.standardCertificateValidUntilUtc,
        certificateReference: record.standardCertificateReference,
        standardSetLabel: record.standardsLabel,
        measurementValue: record.standardMeasurementValue,
        applicableRange: record.standardApplicableRange,
      },
      measurement: {
        resultValue: record.measurementResultValue ?? Number.NaN,
        expandedUncertaintyValue:
          record.measurementExpandedUncertaintyValue ?? Number.NaN,
        coverageFactor: record.measurementCoverageFactor ?? Number.NaN,
        unit: record.measurementUnit ?? "",
      },
      signatory: {
        signatoryId: signatory?.userId ?? "missing-signatory",
        displayName: signatory?.displayName,
        authorizationLabel: signatory ? renderAuthorizationLabel(signatory, record.instrumentType) : undefined,
        competencies: (signatory?.competencies ?? []).map((competency) => ({
          instrumentType: competency.instrumentType,
          validFromUtc: deriveCompetencyValidFromUtc(competency.validUntilUtc),
          validUntilUtc: competency.validUntilUtc,
        })),
      },
      certificate: {
        certificateId: record.serviceOrderId,
        revision: record.certificateRevision ?? "R0",
        publicVerificationToken: record.publicVerificationToken ?? "",
        expectedQrHost: record.qrHost ?? defaultQrHost(input.onboarding.organizationSlug),
        issuedNumbers: issuedNumbers.filter(
          (issued) => issued.certificateNumber !== record.certificateNumber,
        ),
      },
      audit: {
        calibrationExecutedAtUtc: record.executedAtUtc ?? input.nowUtc,
        technicalReviewCompletedAtUtc:
          record.reviewCompletedAtUtc ?? record.reviewStartedAtUtc ?? input.nowUtc,
        signedAtUtc: record.signedAtUtc ?? record.signatureStartedAtUtc ?? input.nowUtc,
        emittedAtUtc: record.emittedAtUtc ?? input.nowUtc,
        technicalReviewerId: reviewer?.userId ?? record.reviewerUserId ?? "missing-reviewer",
        technicalReviewerName: reviewer?.displayName ?? record.reviewerName,
        deviceId: record.signatureDeviceId ?? record.reviewDeviceId ?? "device-v3-persisted",
      },
      environment: {
        procedureRangeLabel: record.environmentLabel,
      },
      decision: {
        requested: Boolean(record.decisionRuleLabel || record.decisionOutcomeLabel),
        ruleLabel: record.decisionRuleLabel,
        outcomeLabel: record.decisionOutcomeLabel,
      },
      notes: [record.commentDraft].filter((note) => note.length > 0),
      freeText: record.freeTextStatement,
    });

    const normalizedDryRunResult: EmissionDryRunResult = {
      ...dryRunResult,
      artifacts: {
        ...dryRunResult.artifacts,
        certificateNumber:
          record.certificateNumber ?? dryRunResult.artifacts.certificateNumber,
        qrCodeUrl:
          record.certificateNumber && record.publicVerificationToken
            ? dryRunResult.artifacts.qrCodeUrl ?? buildQrUrl(record)
            : dryRunResult.artifacts.qrCodeUrl,
      },
    };

    const preview = buildPreview(record, normalizedDryRunResult, input.onboarding);
    const queueValidations = buildQueueValidations(
      record,
      reviewScenario.result,
      normalizedDryRunResult,
      input.onboarding,
    );
    const queueBlockers = uniqueStrings([
      ...normalizedDryRunResult.blockers,
      ...reviewScenario.result.blockers,
      ...queueValidations
        .filter((validation) => validation.status === "failed")
        .map((validation) => validation.detail),
    ]);
    const queueWarnings = uniqueStrings([
      ...normalizedDryRunResult.warnings,
      ...reviewScenario.result.warnings,
      ...queueValidations
        .filter((validation) => validation.status === "warning")
        .map((validation) => validation.detail),
    ]);
    const queueStatus = deriveQueueStatus(queueBlockers, queueWarnings);

    return {
      record,
      dryRunScenarioId: deriveDryRunScenarioId(normalizedDryRunResult),
      dryRunResult: normalizedDryRunResult,
      preview,
      reviewScenarioId: deriveReviewScenarioId(record, reviewScenario.result),
      reviewScenario,
      queueStatus,
      queueValidations,
      queueBlockers,
      queueWarnings,
    };
  });
}

function buildDryRunScenario(state: FlowState, scenarioId: EmissionDryRunScenarioId): EmissionDryRunScenario {
  return {
    id: scenarioId,
    label: dryRunScenarioLabel(scenarioId),
    description: dryRunScenarioDescription(scenarioId, state.record.workOrderNumber),
    profile: state.dryRunResult.profile,
    result: state.dryRunResult,
  };
}

function buildPreviewScenario(state: FlowState, scenarioId: EmissionDryRunScenarioId): CertificatePreviewScenario {
  return {
    id: scenarioId,
    label: dryRunScenarioLabel(scenarioId),
    description: dryRunScenarioDescription(scenarioId, state.record.workOrderNumber),
    result: state.preview,
  };
}

function buildReviewScenario(input: {
  record: PersistedServiceOrderRecord;
  users: PersistedUserRecord[];
  records: PersistedServiceOrderRecord[];
}): ReviewSignatureScenario {
  const userMap = new Map(input.users.map((user) => [user.userId, user]));
  const instrumentType = input.record.instrumentType;
  const executor = toWorkflowMembership(
    resolveRequiredUser(input.record.executorUserId, userMap, "executor_not_found"),
    input.records,
  );
  const reviewer = input.record.reviewerUserId
    ? toWorkflowMembership(resolveAssignedUser(input.record.reviewerUserId, userMap), input.records)
    : undefined;
  const signatory = input.record.signatoryUserId
    ? toWorkflowMembership(resolveAssignedUser(input.record.signatoryUserId, userMap), input.records)
    : undefined;

  const result = evaluateReviewSignatureWorkflow({
    organizationId: input.record.organizationId,
    instrumentType,
    stage: resolveWorkflowStage(input.record),
    executor,
    reviewer,
    signatory,
    candidates: input.users.map((user) => toWorkflowMembership(user, input.records)),
  });

  const scenarioId = deriveReviewScenarioId(input.record, result);

  return {
    id: scenarioId,
    label: reviewScenarioLabel(scenarioId),
    description: reviewScenarioDescription(scenarioId, input.record.workOrderNumber),
    result,
  };
}

function buildQueueScenario(
  states: FlowState[],
  fallbackState: FlowState,
  scenarioId: SignatureQueueScenarioId,
): SignatureQueueScenario {
  const state = selectQueueScenarioState(states, scenarioId, fallbackState);
  const items = states.map((itemState) => buildQueueItem(itemState));
  const selectedItem = items.find((item) => item.itemId === state.record.serviceOrderId) ?? items[0]!;
  const summary = buildQueueSummary(states, scenarioId);

  return {
    id: scenarioId,
    label: queueScenarioLabel(scenarioId),
    description: queueScenarioDescription(scenarioId),
    summary,
    selectedItemId: selectedItem.itemId,
    items,
    approval: buildApprovalPanel(state),
  };
}

function buildQueueItem(state: FlowState): SignatureQueueItem {
  return {
    itemId: state.record.serviceOrderId,
    workOrderNumber: state.record.workOrderNumber,
    customerName: state.record.customerName,
    equipmentLabel: state.record.equipmentLabel,
    instrumentType: state.record.instrumentType,
    waitingSinceLabel: formatElapsedLabel(state.record.updatedAtUtc),
    certificateNumber: state.record.certificateNumber ?? state.dryRunResult.artifacts.certificateNumber,
    status: state.queueStatus,
    previewScenarioId: state.dryRunScenarioId,
    reviewSignatureScenarioId: state.reviewScenario.id,
    validations: state.queueValidations,
    blockers: state.queueBlockers,
    warnings: state.queueWarnings,
  };
}

function buildApprovalPanel(state: FlowState): SignatureApprovalPanel {
  const signatoryDisplayName =
    state.record.signatoryName ??
    state.reviewScenario.result.assignments.signatory?.displayName ??
    "Signatario nao atribuido";
  const authorizationLabel = renderAuthorizationLabel(
    undefined,
    state.record.instrumentType,
    state.record.signatoryName,
  );
  const compactPreview: CertificatePreviewField[] = [
    compactField("OS", state.record.workOrderNumber),
    compactField("Cliente", state.record.customerName),
    compactField("Equipamento", state.record.equipmentLabel),
    compactField(
      "Certificado",
      state.record.certificateNumber ?? state.dryRunResult.artifacts.certificateNumber ?? "Pendente",
    ),
    compactField(
      "Resumo tecnico",
      state.dryRunResult.artifacts.declarationSummary ?? "Declaracao indisponivel",
    ),
    compactField("QR publico", state.preview.qrCodeUrl ?? "Ainda nao publicado"),
  ];

  return {
    itemId: state.record.serviceOrderId,
    title: `${state.record.workOrderNumber} · assinatura final`,
    status: state.queueStatus,
    signatoryDisplayName,
    authorizationLabel,
    statement:
      state.record.signatureStatement ??
      `Eu, ${signatoryDisplayName}, confirmo a revisao final e autorizo a emissao controlada deste certificado.`,
    documentHash: state.record.documentHash ?? buildFallbackDocumentHash(state.record),
    canSign: state.queueStatus === "ready" && state.record.workflowStatus !== "emitted",
    actionLabel:
      state.record.workflowStatus === "emitted"
        ? "Certificado ja emitido"
        : state.queueStatus === "ready"
          ? "Assinar e emitir"
          : "Corrigir pendencias antes de assinar",
    blockers: state.queueBlockers,
    warnings: state.queueWarnings,
    authRequirements: buildApprovalRequirements(state),
    compactPreview,
  };
}

function buildApprovalRequirements(state: FlowState): SignatureApprovalRequirement[] {
  return [
    {
      factor: "password",
      label: "Senha",
      status: state.record.signatoryUserId ? "configured" : "missing",
      detail: state.record.signatoryUserId
        ? "Re-autenticacao por senha exigida antes da emissao."
        : "Atribua um signatario antes de concluir a emissao.",
    },
    {
      factor: "totp",
      label: "Codigo TOTP",
      status: state.reviewScenario.result.assignments.signatory?.mfaEnabled ? "configured" : "missing",
      detail: state.reviewScenario.result.assignments.signatory?.mfaEnabled
        ? "MFA ativo para o signatario atribuido."
        : "MFA ausente ou signatario nao elegivel.",
    },
  ];
}

function buildQueueSummary(states: FlowState[], scenarioId: SignatureQueueScenarioId) {
  const items = states.map((state) => buildQueueItem(state));
  const readyCount = items.filter((item) => item.status === "ready").length;
  const attentionCount = items.filter((item) => item.status === "attention").length;
  const blockedCount = items.filter((item) => item.status === "blocked").length;
  const oldest = states.reduce((current, candidate) =>
    candidate.record.updatedAtUtc < current.record.updatedAtUtc ? candidate : current,
  );
  const status: SignatureQueueStatus =
    scenarioId === "mfa-blocked"
      ? "blocked"
      : scenarioId === "attention-required"
        ? "attention"
        : "ready";

  return {
    status,
    headline:
      scenarioId === "approved-ready"
        ? "Fila persistida pronta para assinatura"
        : scenarioId === "attention-required"
          ? "Fila persistida exige conferencia final"
          : "Fila persistida bloqueada antes da emissao",
    pendingCount: items.length,
    readyCount,
    attentionCount,
    blockedCount,
    batchReadyCount: readyCount,
    oldestPendingLabel: formatElapsedLabel(oldest.record.updatedAtUtc),
    recommendedAction:
      scenarioId === "approved-ready"
        ? "Assinar os itens prontos e concluir a emissao oficial."
        : scenarioId === "attention-required"
          ? "Conferir a previa e os warnings antes da assinatura."
          : "Regularizar MFA, aprovacao tecnica ou numeracao antes de emitir.",
    blockers: uniqueStrings(items.flatMap((item) => item.blockers)),
    warnings: uniqueStrings(items.flatMap((item) => item.warnings)),
  };
}

function buildAuditScenario(input: {
  scenarioId: AuditTrailScenarioId;
  states: FlowState[];
  selectedState: FlowState;
  groupedEvents: Map<string, PersistedEmissionAuditEvent[]>;
  selectedEventId?: string;
}): AuditTrailScenario {
  const state = selectAuditScenarioState(
    input.states,
    input.groupedEvents,
    input.scenarioId,
    input.selectedState,
  );
  const events = input.groupedEvents.get(state.record.serviceOrderId) ?? [];
  const entries = events.map(toAuditEntry);
  const status = deriveAuditStatus(state.record, entries);
  const items = events.map((event) => buildAuditItem(entries, event, status));
  const selectedEvent =
    items.find((item) => item.eventId === input.selectedEventId) ??
    items[0];
  const detail = buildAuditDetail(state, entries, selectedEvent?.eventId, status);

  return {
    id: input.scenarioId,
    label: auditScenarioLabel(input.scenarioId),
    description: auditScenarioDescription(input.scenarioId, state.record.workOrderNumber),
    summary: {
      status,
      headline:
        status === "ready"
          ? "Trilha critica integra e pronta para auditoria"
          : status === "attention"
            ? "Trilha critica ainda em formacao"
            : "Trilha critica bloqueada por integridade ou lacuna obrigatoria",
      totalEvents: items.length,
      criticalEvents: items.filter((item) =>
        [
          "calibration.executed",
          "technical_review.completed",
          "certificate.signed",
          "certificate.emitted",
        ].includes(item.actionLabel),
      ).length,
      reissueEvents: 0,
      integrityFailures: status === "blocked" ? 1 : 0,
      recommendedAction:
        status === "ready"
          ? "Manter a cadeia pronta para consulta e exportacao."
          : status === "attention"
            ? "Completar assinatura e emissao para fechar a cadeia critica."
            : "Interromper o fluxo e investigar antes de reutilizar a cadeia.",
      blockers: detail.blockers,
      warnings: detail.warnings,
    },
    selectedEventId: selectedEvent?.eventId ?? "sem-evento",
    items: items.length > 0 ? items : [buildPlaceholderAuditItem(state.record)],
    detail,
  };
}

function buildAuditItem(
  entries: AuditChainEntry[],
  event: PersistedEmissionAuditEvent,
  overallStatus: RegistryOperationalStatus,
): AuditTrailEventItem {
  const hashChain = verifyAuditHashChain(entries);
  const current = entries.find((entry) => entry.id === event.eventId);

  return {
    eventId: event.eventId,
    occurredAtLabel: formatDateTime(event.occurredAtUtc),
    actorLabel: event.actorLabel,
    actionLabel: event.action,
    entityLabel: event.entityLabel,
    hashLabel: `${event.hash.slice(0, 4)}...`,
    status:
      !hashChain.ok && hashChain.firstInvalid?.id === current?.id
        ? "blocked"
        : overallStatus === "attention"
          ? "attention"
          : overallStatus,
  };
}

function buildAuditDetail(
  state: FlowState,
  entries: AuditChainEntry[],
  selectedEventId: string | undefined,
  status: RegistryOperationalStatus,
): AuditTrailDetail {
  const hashChain = verifyAuditHashChain(entries);
  const critical = verifyCriticalEventAuditTrail(entries);
  const reviewSignature = verifyTechnicalReviewSignatureAudit(entries);
  const missingActions = uniqueStrings([
    ...critical.missingActions,
    ...reviewSignature.missingActions,
  ]);
  const blockers =
    status === "blocked"
      ? uniqueStrings([
          ...(!hashChain.ok
            ? [`Hash-chain divergente em ${hashChain.firstInvalid?.id ?? "evento desconhecido"}.`]
            : []),
          ...missingActions.map((action) => `Evento obrigatorio ausente: ${action}.`),
        ])
      : [];
  const warnings =
    status === "attention"
      ? missingActions.map((action) => `Evento ainda pendente nesta cadeia: ${action}.`)
      : [];

  return {
    chainId: state.record.serviceOrderId,
    title: `${state.record.workOrderNumber} · trilha critica`,
    status,
    noticeLabel:
      status === "ready"
        ? "Cadeia integra e concluida."
        : status === "attention"
          ? "Cadeia ainda em formacao antes da emissao."
          : "Cadeia bloqueada por divergencia ou cobertura insuficiente.",
    selectedWindowLabel: "Tenant autenticado",
    selectedActorLabel: "Todos os atores da emissao",
    selectedEntityLabel: state.record.workOrderNumber,
    selectedActionLabel: selectedEventId ?? "Evento mais recente",
    chainStatusLabel:
      status === "ready"
        ? "Hash-chain integra e eventos criticos completos"
        : status === "attention"
          ? "Hash-chain integra, com eventos finais ainda pendentes"
          : "Fail-closed por integridade ou ausencia de evento critico",
    exportLabel:
      status === "ready"
        ? "Exportacao pronta para auditoria"
        : status === "attention"
          ? "Exportacao liberada apenas para conferencia interna"
          : "Exportacao bloqueada ate investigacao",
    coveredActions:
      uniqueStrings(entries.map((entry) => readAuditAction(entry))).length > 0
        ? uniqueStrings(entries.map((entry) => readAuditAction(entry)))
        : ["chain.pending"],
    missingActions,
    blockers,
    warnings,
    links: {
      workspaceScenarioId: mapWorkspaceScenario(state.dryRunScenarioId),
      serviceOrderScenarioId: mapServiceOrderScenario(state.record),
      reviewItemId: state.record.serviceOrderId,
      dryRunScenarioId: state.dryRunScenarioId,
      publicCertificateScenarioId: mapPublicCertificateScenario(state.record),
    },
  };
}

function buildPlaceholderAuditItem(record: PersistedServiceOrderRecord): AuditTrailEventItem {
  return {
    eventId: `${record.serviceOrderId}-pending`,
    occurredAtLabel: formatDateTime(record.updatedAtUtc),
    actorLabel: record.executorName,
    actionLabel: "chain.pending",
    entityLabel: record.workOrderNumber,
    hashLabel: "pend...",
    status: "attention",
  };
}

function buildPreview(
  record: PersistedServiceOrderRecord,
  result: EmissionDryRunResult,
  onboarding: PersistedOnboardingRecord,
): EmissionCertificatePreview {
  const suggestedReturnStep =
    result.status === "blocked"
      ? Math.min(
          ...result.checks
            .filter((check) => check.status === "failed")
            .map((check) => STEP_BY_CHECK[check.id]),
        )
      : undefined;

  return {
    status: result.status,
    headline:
      result.status === "ready"
        ? "Previa persistida pronta para conferencia"
        : "Previa persistida bloqueada antes da assinatura",
    templateId: result.artifacts.templateId,
    symbolPolicy: result.artifacts.symbolPolicy,
    certificateNumber: result.artifacts.certificateNumber,
    qrCodeUrl: result.artifacts.qrCodeUrl,
    qrVerificationStatus: result.artifacts.qrVerificationStatus,
    suggestedReturnStep: Number.isFinite(suggestedReturnStep) ? suggestedReturnStep : undefined,
    blockers: result.blockers,
    warnings: result.warnings,
    sections: [
      buildSection("header", "Cabecalho", [
        ["Organizacao emissora", onboarding.organizationName],
        ["Pacote normativo", onboarding.normativePackageVersion],
        ["OS", record.workOrderNumber],
        ["Certificado", result.artifacts.certificateNumber ?? "Numeracao pendente"],
      ]),
      buildSection("identification", "Identificacao", [
        ["Cliente", record.customerName],
        ["Equipamento", record.equipmentLabel],
        ["Serie", record.equipmentSerialNumber],
        ["TAG", record.equipmentTagCode],
      ]),
      buildSection("standards", "Padroes", [
        ["Padrao principal", record.standardsLabel],
        ["Fonte", record.standardSource],
        ["Certificado do padrao", record.standardCertificateReference],
        ["Validade", record.standardCertificateValidUntilUtc ? formatDate(record.standardCertificateValidUntilUtc) : "Nao informada"],
      ]),
      buildSection("environment", "Ambiente", [
        ["Condicoes", record.environmentLabel],
        ["Pontos da curva", record.curvePointsLabel],
        ["Evidencias", record.evidenceLabel],
      ]),
      buildSection("results", "Resultados", [
        ["Resultado", renderMeasurement(record.measurementResultValue, record.measurementUnit)],
        ["Incerteza expandida", renderMeasurement(record.measurementExpandedUncertaintyValue, record.measurementUnit)],
        ["Fator k", record.measurementCoverageFactor ? `k=${record.measurementCoverageFactor}` : "Nao informado"],
        ["Resumo tecnico", result.artifacts.declarationSummary ?? "Declaracao indisponivel"],
      ]),
      buildSection("decision", "Regra de decisao e observacoes", [
        ["Regra de decisao", record.decisionRuleLabel ?? "Nao aplicada"],
        ["Resultado da decisao", record.decisionOutcomeLabel ?? "Nao aplicado"],
        ["Texto livre", record.freeTextStatement ?? "Sem texto complementar"],
      ]),
      buildSection("authorization", "Revisao e assinatura", [
        ["Revisor tecnico", record.reviewerName ?? "Nao atribuido"],
        ["Signatario", record.signatoryName ?? "Nao atribuido"],
        ["Decisao da revisao", renderReviewDecision(record.reviewDecision)],
        ["Hash do documento", record.documentHash ?? buildFallbackDocumentHash(record)],
      ]),
      buildSection("footer", "Rodape e publicacao", [
        ["Revisao do certificado", record.certificateRevision ?? "R0"],
        ["QR publico", result.artifacts.qrCodeUrl ?? "Ainda nao publicado"],
        ["Politica de simbolo", result.artifacts.symbolPolicy],
        ["Status final", result.status === "ready" ? "Pronto para assinatura" : "Bloqueado"],
      ]),
    ],
  };
}

function buildSection(
  key: EmissionCertificatePreview["sections"][number]["key"],
  title: string,
  fields: Array<[string, string]>,
) {
  return {
    key,
    title,
    fields: fields.map(([label, value]) => ({ label, value })),
  };
}

const STEP_BY_CHECK: Record<EmissionDryRunResult["checks"][number]["id"], number> = {
  profile_policy: 11,
  equipment_registration: 2,
  standard_eligibility: 3,
  signatory_competence: 14,
  certificate_numbering: 13,
  measurement_declaration: 10,
  audit_trail: 15,
  qr_authenticity: 13,
};

function buildQueueValidations(
  record: PersistedServiceOrderRecord,
  review: ReviewSignatureScenario["result"],
  dryRun: EmissionDryRunResult,
  onboarding: PersistedOnboardingRecord,
): SignatureQueueValidation[] {
  return [
    {
      label: "Revisao tecnica",
      status:
        review.stage === "approved" || review.stage === "emitted" ? "passed" : "failed",
      detail:
        review.stage === "approved" || review.stage === "emitted"
          ? "Revisao tecnica concluida."
          : "A fila aceita apenas itens tecnicamente aprovados.",
    },
    {
      label: "Numeracao sequencial",
      status: onboarding.certificateNumberingConfigured ? "passed" : "failed",
      detail: onboarding.certificateNumberingConfigured
        ? "Configuracao de numeracao valida para emissao."
        : "Onboarding ainda nao concluiu a numeracao sequencial.",
    },
    {
      label: "QR publico",
      status: onboarding.publicQrConfigured ? "passed" : "failed",
      detail: onboarding.publicQrConfigured
        ? "Host publico configurado para verificacao."
        : "QR publico ainda nao foi configurado para o tenant.",
    },
    {
      label: "Signatario com MFA",
      status: review.assignments.signatory?.mfaEnabled ? "passed" : "failed",
      detail: review.assignments.signatory?.mfaEnabled
        ? "MFA ativo para o signatario atribuido."
        : "Signatario sem MFA obrigatorio ativo.",
    },
    {
      label: "Politica regulatoria",
      status: dryRun.artifacts.symbolPolicy === "suppressed" ? "warning" : "passed",
      detail:
        dryRun.artifacts.symbolPolicy === "suppressed"
          ? "Simbolo regulatorio suprimido: requer conferencia final."
          : "Politica regulatoria compativel com a assinatura.",
    },
    {
      label: "Hash do documento",
      status: record.documentHash ? "passed" : record.workflowStatus === "emitted" ? "failed" : "warning",
      detail: record.documentHash
        ? "Hash do documento ja materializado."
        : record.workflowStatus === "emitted"
          ? "Emissao sem hash persistido falha fechada."
          : "Hash final sera consolidado no momento da assinatura.",
    },
  ];
}

function deriveDryRunScenarioId(result: EmissionDryRunResult): EmissionDryRunScenarioId {
  if (result.status === "blocked") {
    return "type-c-blocked";
  }
  if (result.artifacts.symbolPolicy === "suppressed") {
    return "type-a-suppressed";
  }

  return "type-b-ready";
}

function deriveReviewScenarioId(
  record: PersistedServiceOrderRecord,
  result: ReviewSignatureScenario["result"],
): ReviewSignatureScenarioId {
  if (record.signatoryUserId && !result.assignments.signatory?.mfaEnabled) {
    return "signatory-mfa-blocked";
  }
  if (!record.reviewerUserId || record.reviewerUserId === record.executorUserId) {
    return "reviewer-conflict";
  }
  if (result.stage === "approved" || result.stage === "emitted") {
    return "approved-ready";
  }

  return "segregated-ready";
}

function deriveQueueScenarioId(status: SignatureQueueStatus): SignatureQueueScenarioId {
  if (status === "blocked") {
    return "mfa-blocked";
  }
  if (status === "attention") {
    return "attention-required";
  }

  return "approved-ready";
}

function deriveQueueStatus(blockers: string[], warnings: string[]): SignatureQueueStatus {
  if (blockers.length > 0) {
    return "blocked";
  }
  if (warnings.length > 0) {
    return "attention";
  }

  return "ready";
}

function deriveAuditScenarioId(
  record: PersistedServiceOrderRecord,
  events: PersistedEmissionAuditEvent[],
): AuditTrailScenarioId {
  const status = deriveAuditStatus(record, events.map(toAuditEntry));
  if (status === "blocked") {
    return "integrity-blocked";
  }
  if (status === "attention") {
    return "reissue-attention";
  }

  return "recent-emission";
}

function deriveAuditStatus(
  record: PersistedServiceOrderRecord,
  entries: AuditChainEntry[],
): RegistryOperationalStatus {
  if (entries.length === 0) {
    return record.workflowStatus === "emitted" ? "blocked" : "attention";
  }

  const hashChain = verifyAuditHashChain(entries);
  if (!hashChain.ok) {
    return "blocked";
  }

  if (record.workflowStatus !== "emitted") {
    return "attention";
  }

  const critical = verifyCriticalEventAuditTrail(entries);
  const reviewSignature = verifyTechnicalReviewSignatureAudit(entries);
  return critical.ok && reviewSignature.ok ? "ready" : "blocked";
}

function resolveWorkflowStage(record: PersistedServiceOrderRecord): ReviewSignatureScenario["result"]["stage"] {
  if (record.workflowStatus === "emitted") {
    return "emitted";
  }
  if (record.workflowStatus === "awaiting_signature" || record.reviewDecision === "approved") {
    return "approved";
  }

  return "in_review";
}

function toWorkflowMembership(
  user: PersistedUserRecord | undefined,
  records: PersistedServiceOrderRecord[],
): WorkflowMembershipInput {
  if (!user) {
    return {
      userId: "missing-user",
      displayName: "Usuario ausente",
      organizationId: "missing-org",
      roles: [],
      active: false,
      mfaEnabled: false,
      authorizedInstrumentTypes: [],
      pendingAssignments: 0,
    };
  }

  return {
    userId: user.userId,
    displayName: user.displayName,
    organizationId: user.organizationId,
    roles: user.roles,
    active: user.status === "active",
    mfaEnabled: user.mfaEnrolled,
    authorizedInstrumentTypes: user.competencies
      .filter((competency) => competency.status !== "expired")
      .map((competency) => competency.instrumentType),
    pendingAssignments: records.filter(
      (record) =>
        record.reviewerUserId === user.userId ||
        record.signatoryUserId === user.userId,
    ).length,
  };
}

function selectState(states: FlowState[], selectedItemId?: string) {
  return states.find((state) => state.record.serviceOrderId === selectedItemId) ?? states[0]!;
}

function selectScenarioState(
  states: FlowState[],
  scenarioId: EmissionDryRunScenarioId,
  fallbackState: FlowState,
) {
  return states.find((state) => state.dryRunScenarioId === scenarioId) ?? fallbackState;
}

function selectReviewScenarioState(
  states: FlowState[],
  scenarioId: ReviewSignatureScenarioId,
  fallbackState: FlowState,
) {
  return states.find((state) => state.reviewScenarioId === scenarioId) ?? fallbackState;
}

function selectQueueScenarioState(
  states: FlowState[],
  scenarioId: SignatureQueueScenarioId,
  fallbackState: FlowState,
) {
  return (
    states.find((state) => deriveQueueScenarioId(state.queueStatus) === scenarioId) ?? fallbackState
  );
}

function selectAuditScenarioState(
  states: FlowState[],
  groupedEvents: Map<string, PersistedEmissionAuditEvent[]>,
  scenarioId: AuditTrailScenarioId,
  fallbackState: FlowState,
) {
  return (
    states.find(
      (state) =>
        deriveAuditScenarioId(
          state.record,
          groupedEvents.get(state.record.serviceOrderId) ?? [],
        ) === scenarioId,
    ) ?? fallbackState
  );
}

function groupAuditEventsByServiceOrder(events: PersistedEmissionAuditEvent[]) {
  const grouped = new Map<string, PersistedEmissionAuditEvent[]>();
  for (const event of events) {
    const bucket = grouped.get(event.serviceOrderId) ?? [];
    bucket.push(event);
    bucket.sort((left, right) => {
      if (left.occurredAtUtc !== right.occurredAtUtc) {
        return left.occurredAtUtc.localeCompare(right.occurredAtUtc);
      }

      return left.eventId.localeCompare(right.eventId);
    });
    grouped.set(event.serviceOrderId, bucket);
  }

  return grouped;
}

function toAuditEntry(event: PersistedEmissionAuditEvent): AuditChainEntry {
  return {
    id: event.eventId,
    prevHash: event.prevHash,
    hash: event.hash,
    payload: {
      action: event.action,
      actorId: event.actorUserId,
      actorLabel: event.actorLabel,
      certificateId: event.serviceOrderId,
      certificateNumber: event.certificateNumber,
      entityLabel: event.entityLabel,
      timestampUtc: event.occurredAtUtc,
      deviceId: event.deviceId,
    },
  };
}

function readAuditAction(entry: AuditChainEntry) {
  const payload = entry.payload as { action?: string };
  return payload.action ?? "acao.desconhecida";
}

function resolveAssignedUser(
  userId: string | undefined,
  userMap: Map<string, PersistedUserRecord>,
) {
  return userId ? userMap.get(userId) : undefined;
}

function resolveRequiredUser(
  userId: string,
  userMap: Map<string, PersistedUserRecord>,
  message: string,
) {
  const user = userMap.get(userId);
  if (!user) {
    throw new Error(message);
  }

  return user;
}

function deriveOrganizationCode(slug: string) {
  const normalized = slug.replace(/[^a-z0-9]/gi, "").toUpperCase();
  return (normalized || "AFERE").slice(0, 12);
}

function mapRegulatoryProfile(profile: string): EmissionDryRunProfile {
  if (profile === "type_a") {
    return "A";
  }
  if (profile === "type_c") {
    return "C";
  }

  return "B";
}

function defaultQrHost(organizationSlug: string) {
  return `${organizationSlug}.afere.local`;
}

function buildQrUrl(record: PersistedServiceOrderRecord) {
  if (!record.publicVerificationToken) {
    return undefined;
  }

  return `https://${record.qrHost ?? defaultQrHost("afere")}/verify?certificate=${encodeURIComponent(
    record.serviceOrderId,
  )}&token=${encodeURIComponent(record.publicVerificationToken)}`;
}

function renderAuthorizationLabel(
  signatory: PersistedUserRecord | undefined,
  instrumentType: string,
  displayName?: string,
) {
  const competency = signatory?.competencies.find(
    (item) => item.instrumentType === instrumentType && item.status !== "expired",
  );

  return competency?.roleLabel ?? `Signatario autorizado para ${displayName ?? instrumentType}`;
}

function renderMeasurement(value: number | undefined, unit: string | undefined) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${value} ${unit ?? ""}`.trim()
    : "Nao informado";
}

function renderReviewDecision(decision: PersistedServiceOrderRecord["reviewDecision"]) {
  switch (decision) {
    case "approved":
      return "Aprovada";
    case "rejected":
      return "Reprovada";
    default:
      return "Pendente";
  }
}

function buildFallbackDocumentHash(record: PersistedServiceOrderRecord) {
  const source = [
    record.workOrderNumber,
    record.customerName,
    record.equipmentLabel,
    record.measurementResultValue ?? "na",
    record.measurementExpandedUncertaintyValue ?? "na",
  ].join("|");
  let hash = 0;
  for (const char of source) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }

  return `sha256-simulado-${hash.toString(16).padStart(8, "0")}`;
}

function compactField(label: string, value: string): CertificatePreviewField {
  return { label, value };
}

function deriveCompetencyValidFromUtc(validUntilUtc: string) {
  const date = new Date(validUntilUtc);
  date.setUTCFullYear(date.getUTCFullYear() - 1);
  return date.toISOString();
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function formatElapsedLabel(value: string) {
  const elapsedMs = Date.now() - new Date(value).getTime();
  const elapsedMinutes = Math.max(1, Math.round(elapsedMs / 60000));
  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} min`;
  }

  const hours = Math.floor(elapsedMinutes / 60);
  const minutes = elapsedMinutes % 60;
  return `${hours}h ${String(minutes).padStart(2, "0")}min`;
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values));
}

function mapWorkspaceScenario(scenarioId: EmissionDryRunScenarioId) {
  switch (scenarioId) {
    case "type-c-blocked":
      return "release-blocked" as const;
    case "type-a-suppressed":
      return "team-attention" as const;
    default:
      return "baseline-ready" as const;
  }
}

function mapServiceOrderScenario(record: PersistedServiceOrderRecord) {
  if (record.workflowStatus === "blocked") {
    return "review-blocked" as const;
  }
  if (record.workflowStatus === "in_execution") {
    return "history-pending" as const;
  }

  return "review-ready" as const;
}

function mapPublicCertificateScenario(record: PersistedServiceOrderRecord): PublicCertificateScenarioId {
  if (!record.certificateNumber || !record.publicVerificationToken) {
    return "not-found";
  }

  return "authentic";
}

function dryRunScenarioLabel(scenarioId: EmissionDryRunScenarioId) {
  switch (scenarioId) {
    case "type-a-suppressed":
      return "Previa com simbolo suprimido";
    case "type-c-blocked":
      return "Dry-run bloqueado";
    default:
      return "Dry-run pronto para emissao";
  }
}

function dryRunScenarioDescription(
  scenarioId: EmissionDryRunScenarioId,
  workOrderNumber: string,
) {
  switch (scenarioId) {
    case "type-a-suppressed":
      return `${workOrderNumber} esta pronto, mas exige conferencia adicional por politica regulatoria.`;
    case "type-c-blocked":
      return `${workOrderNumber} acumula bloqueios tecnicos ou de autorizacao.`;
    default:
      return `${workOrderNumber} ja consegue sustentar a previa oficial do certificado.`;
  }
}

function reviewScenarioLabel(scenarioId: ReviewSignatureScenarioId) {
  switch (scenarioId) {
    case "approved-ready":
      return "Workflow aprovado e pronto para assinatura";
    case "reviewer-conflict":
      return "Workflow bloqueado por conflito de revisor";
    case "signatory-mfa-blocked":
      return "Workflow bloqueado por MFA do signatario";
    default:
      return "Workflow com segregacao valida";
  }
}

function reviewScenarioDescription(
  scenarioId: ReviewSignatureScenarioId,
  workOrderNumber: string,
) {
  switch (scenarioId) {
    case "approved-ready":
      return `${workOrderNumber} concluiu a revisao tecnica e aguarda assinatura.`;
    case "reviewer-conflict":
      return `${workOrderNumber} ainda nao possui segregacao valida entre executor e revisor.`;
    case "signatory-mfa-blocked":
      return `${workOrderNumber} depende de MFA ativo para o signatario atribuido.`;
    default:
      return `${workOrderNumber} possui revisor e signatario segregados para seguir no fluxo.`;
  }
}

function queueScenarioLabel(scenarioId: SignatureQueueScenarioId) {
  switch (scenarioId) {
    case "attention-required":
      return "Fila com conferencia adicional";
    case "mfa-blocked":
      return "Fila bloqueada para assinatura";
    default:
      return "Fila pronta para assinatura";
  }
}

function queueScenarioDescription(scenarioId: SignatureQueueScenarioId) {
  switch (scenarioId) {
    case "attention-required":
      return "Itens persistidos com warning operacional antes da assinatura.";
    case "mfa-blocked":
      return "Itens persistidos bloqueados por MFA, aprovacao ou numeracao.";
    default:
      return "Itens persistidos aptos para assinatura e emissao.";
  }
}

function auditScenarioLabel(scenarioId: AuditTrailScenarioId) {
  switch (scenarioId) {
    case "integrity-blocked":
      return "Trilha critica bloqueada";
    case "reissue-attention":
      return "Trilha critica em formacao";
    default:
      return "Trilha critica integra";
  }
}

function auditScenarioDescription(
  scenarioId: AuditTrailScenarioId,
  workOrderNumber: string,
) {
  switch (scenarioId) {
    case "integrity-blocked":
      return `${workOrderNumber} falhou fechada por divergencia na cadeia ou evento critico ausente.`;
    case "reissue-attention":
      return `${workOrderNumber} ainda esta formando a cadeia critica antes da emissao final.`;
    default:
      return `${workOrderNumber} possui cadeia critica integra e concluida.`;
  }
}
