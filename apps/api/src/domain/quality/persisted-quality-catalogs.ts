import type {
  InternalAuditCatalog,
  InternalAuditChecklistItem,
  InternalAuditFindingItem,
  ManagementReviewAutomaticInput,
  ManagementReviewCatalog,
  NonconformityRegistryCatalog,
  NonconformingWorkCatalog,
  QualityHubCatalog,
  QualityHubModule,
  QualityIndicatorRegistryCatalog,
  RegistryOperationalStatus,
} from "@afere/contracts";

import type { PersistedServiceOrderRecord } from "../emission/service-order-persistence.js";
import type {
  PersistedComplianceProfileRecord,
  PersistedInternalAuditCycleRecord,
  PersistedManagementReviewMeetingRecord,
  PersistedNonconformityRecord,
  PersistedNonconformingWorkRecord,
  PersistedQualityIndicatorSnapshotRecord,
} from "./quality-persistence.js";
import {
  buildManagementReviewCalendar,
  buildManagementReviewCalendarExportHref,
  formatManagementReviewSchedule,
} from "./management-review-calendar.js";
import { buildManagementReviewSignature } from "./management-review-signature.js";

type BuilderStatus = RegistryOperationalStatus;

type DerivedIndicator = {
  indicatorId: string;
  title: string;
  currentValue: number;
  targetValue: number;
  unitLabel: string;
  trendLabel: string;
  ownerLabel: string;
  cadenceLabel: string;
  periodLabel: string;
  measurementDefinitionLabel: string;
  evidenceLabel: string;
  managementReviewLabel: string;
  relatedArtifacts: string[];
  blockers: string[];
  warnings: string[];
  status: BuilderStatus;
  snapshots: Array<{
    monthStartUtc: string;
    monthLabel: string;
    valueLabel: string;
    status: BuilderStatus;
  }>;
  links: {
    nonconformityId?: string;
    nonconformityScenarioId?: "open-attention" | "critical-response" | "resolved-history";
  };
};

export function buildPersistedNonconformityCatalog(input: {
  nowUtc: string;
  records: PersistedNonconformityRecord[];
  selectedNcId?: string;
}): NonconformityRegistryCatalog {
  const items = [...input.records].sort(compareStatusThenDate);
  const selectedRecord = selectRecord(items, input.selectedNcId);
  const totals = summarizeNonconformities(items);

  const attentionRecord = pickFirstByStatus(items, "attention") ?? selectedRecord;
  const blockedRecord = pickFirstByStatus(items, "blocked") ?? selectedRecord;
  const readyRecord = pickFirstByStatus(items, "ready") ?? selectedRecord;

  return {
    selectedScenarioId: inferQualityScenarioId(totals.status, {
      ready: "resolved-history",
      attention: "open-attention",
      blocked: "critical-response",
    }),
    scenarios: [
      buildNonconformityScenario(
        "open-attention",
        "NCs em acompanhamento real",
        "Nao conformidades persistidas do tenant com follow-up sobre OS e evidencias reais.",
        items,
        attentionRecord,
        totals,
      ),
      buildNonconformityScenario(
        "critical-response",
        "NC critica em resposta fail-closed",
        "O recorte destaca a NC bloqueante que ancora o follow-up operacional e regulatorio.",
        items,
        blockedRecord,
        totals,
      ),
      buildNonconformityScenario(
        "resolved-history",
        "Historico de NCs resolvidas",
        "O recorte preserva rastreabilidade das NCs encerradas sobre registros persistidos do tenant.",
        items,
        readyRecord,
        totals,
      ),
    ],
  };
}

export function buildPersistedNonconformingWorkCatalog(input: {
  records: PersistedNonconformingWorkRecord[];
  selectedCaseId?: string;
  nonconformities: PersistedNonconformityRecord[];
}): NonconformingWorkCatalog {
  const items = [...input.records].sort((left, right) => right.updatedAtUtc.localeCompare(left.updatedAtUtc));
  const selectedRecord = selectRecord(items, input.selectedCaseId);
  const totals = summarizeNonconformingWork(items);
  const attentionRecord = pickFirstByStatus(items, "attention") ?? selectedRecord;
  const blockedRecord = pickFirstByStatus(items, "blocked") ?? selectedRecord;
  const readyRecord = pickFirstByStatus(items, "ready") ?? selectedRecord;

  return {
    selectedScenarioId: inferQualityScenarioId(totals.status, {
      ready: "archived-history",
      attention: "contained-attention",
      blocked: "release-blocked",
    }),
    scenarios: [
      buildNonconformingWorkScenario(
        "contained-attention",
        "Contencao preventiva ativa",
        "O modulo V5 opera sobre casos reais de trabalho nao conforme vinculados ao fluxo persistido.",
        items,
        attentionRecord,
        totals,
        input.nonconformities,
      ),
      buildNonconformingWorkScenario(
        "release-blocked",
        "Liberacao bloqueada por caso critico",
        "O recorte destaca o caso de contencao que ainda impede liberacao segura do fluxo real.",
        items,
        blockedRecord,
        totals,
        input.nonconformities,
      ),
      buildNonconformingWorkScenario(
        "archived-history",
        "Historico restaurado",
        "Casos encerrados permanecem visiveis como rastreabilidade real do retorno ao fluxo.",
        items,
        readyRecord,
        totals,
        input.nonconformities,
      ),
    ],
  };
}

export function buildPersistedInternalAuditCatalog(input: {
  cycles: PersistedInternalAuditCycleRecord[];
  nonconformities: PersistedNonconformityRecord[];
  selectedCycleId?: string;
}): InternalAuditCatalog {
  const cycles = [...input.cycles].sort((left, right) => right.scheduledAtUtc.localeCompare(left.scheduledAtUtc));
  const selectedCycle = selectRecord(cycles, input.selectedCycleId);
  const findings = buildAuditFindings(selectedCycle, input.nonconformities);
  const totals = summarizeInternalAudits(cycles, input.nonconformities);
  const readyCycle = pickFirstByStatus(cycles, "ready") ?? selectedCycle;
  const attentionCycle = pickFirstByStatus(cycles, "attention") ?? selectedCycle;
  const blockedCycle = pickFirstByStatus(cycles, "blocked") ?? selectedCycle;

  return {
    selectedScenarioId: inferQualityScenarioId(totals.status, {
      ready: "program-on-track",
      attention: "follow-up-attention",
      blocked: "extraordinary-escalation",
    }),
    scenarios: [
      buildInternalAuditScenario(
        "program-on-track",
        "Programa em trilho real",
        "A auditoria interna passa a operar sobre evidencias persistidas e follow-up real.",
        cycles,
        readyCycle,
        totals,
        buildAuditFindings(readyCycle, input.nonconformities),
      ),
      buildInternalAuditScenario(
        "follow-up-attention",
        "Follow-up de auditoria em aberto",
        "O recorte destaca ciclos com follow-up pendente sobre NCs e evidencias reais.",
        cycles,
        attentionCycle,
        totals,
        buildAuditFindings(attentionCycle, input.nonconformities),
      ),
      buildInternalAuditScenario(
        "extraordinary-escalation",
        "Ciclo extraordinario bloqueante",
        "O recorte fail-closed destaca quando a auditoria interna ancora resposta critica do tenant.",
        cycles,
        blockedCycle,
        totals,
        buildAuditFindings(blockedCycle, input.nonconformities),
      ),
    ],
  };
}

export function buildPersistedQualityIndicatorCatalog(input: {
  nowUtc: string;
  serviceOrders: PersistedServiceOrderRecord[];
  nonconformities: PersistedNonconformityRecord[];
  nonconformingWork: PersistedNonconformingWorkRecord[];
  internalAuditCycles: PersistedInternalAuditCycleRecord[];
  managementReviewMeetings: PersistedManagementReviewMeetingRecord[];
  indicatorSnapshots: PersistedQualityIndicatorSnapshotRecord[];
  selectedIndicatorId?: string;
}): QualityIndicatorRegistryCatalog {
  const indicators = deriveIndicators(input);
  const selectedIndicator =
    indicators.find((indicator) => indicator.indicatorId === input.selectedIndicatorId) ?? indicators[0]!;
  const selectedReady =
    indicators.find(
      (indicator) =>
        indicator.indicatorId === selectedIndicator.indicatorId && indicator.status === "ready",
    ) ??
    indicators.find((indicator) => indicator.status === "ready") ??
    indicators[0]!;
  const selectedAttention =
    indicators.find(
      (indicator) =>
        indicator.indicatorId === selectedIndicator.indicatorId && indicator.status === "attention",
    ) ??
    indicators.find((indicator) => indicator.status === "attention") ??
    indicators[0]!;
  const selectedBlocked =
    indicators.find(
      (indicator) =>
        indicator.indicatorId === selectedIndicator.indicatorId && indicator.status === "blocked",
    ) ??
    indicators.find((indicator) => indicator.status === "blocked") ??
    indicators[0]!;
  const summary = summarizeIndicators(indicators);

  return {
    selectedScenarioId: inferQualityScenarioId(summary.status, {
      ready: "baseline-ready",
      attention: "action-sla-attention",
      blocked: "critical-drift",
    }),
    scenarios: [
      buildIndicatorScenario(
        "baseline-ready",
        "Indicadores em baseline real",
        "O painel V5 deriva tendencias reais do tenant sem depender apenas de snapshots demonstrativos.",
        indicators,
        selectedReady,
        summary,
      ),
      buildIndicatorScenario(
        "action-sla-attention",
        "Indicadores em atencao",
        "O recorte destaca os desvios que exigem acao antes da proxima analise critica.",
        indicators,
        selectedAttention,
        summary,
      ),
      buildIndicatorScenario(
        "critical-drift",
        "Deriva critica da Qualidade",
        "O recorte fail-closed mostra o indicador que bloqueia a saude operacional da V5.",
        indicators,
        selectedBlocked,
        summary,
      ),
    ],
  };
}

export function buildPersistedManagementReviewCatalog(input: {
  meetings: PersistedManagementReviewMeetingRecord[];
  serviceOrders: PersistedServiceOrderRecord[];
  nonconformities: PersistedNonconformityRecord[];
  internalAuditCycles: PersistedInternalAuditCycleRecord[];
  complianceProfile?: PersistedComplianceProfileRecord | null;
  selectedMeetingId?: string;
}): ManagementReviewCatalog {
  const meetings = [...input.meetings].sort((left, right) => right.scheduledForUtc.localeCompare(left.scheduledForUtc));
  const selectedMeeting = selectRecord(meetings, input.selectedMeetingId);
  const autoInputs = buildManagementReviewAutomaticInputs(input);
  const summary = summarizeManagementReviews(meetings);
  const calendar = buildManagementReviewCalendar({ meetings });
  const readyMeeting = pickFirstByStatus(meetings, "ready") ?? selectedMeeting;
  const attentionMeeting = pickFirstByStatus(meetings, "attention") ?? selectedMeeting;
  const blockedMeeting = pickFirstByStatus(meetings, "blocked") ?? selectedMeeting;

  return {
    selectedScenarioId: inferQualityScenarioId(summary.status, {
      ready: "ordinary-ready",
      attention: "agenda-attention",
      blocked: "extraordinary-response",
    }),
    scenarios: [
      buildManagementReviewScenario(
        "ordinary-ready",
        "Analise critica ordinaria",
        "A direcao passa a consolidar pauta e deliberacoes sobre dados persistidos da operacao e da Qualidade.",
        meetings,
        readyMeeting,
        autoInputs,
        calendar,
        summary,
      ),
      buildManagementReviewScenario(
        "agenda-attention",
        "Pauta em preparacao",
        "O recorte destaca a reuniao com pendencias reais antes do fechamento da ata.",
        meetings,
        attentionMeeting,
        autoInputs,
        calendar,
        summary,
      ),
      buildManagementReviewScenario(
        "extraordinary-response",
        "Resposta extraordinaria",
        "O recorte fail-closed destaca reuniao e deliberacoes extraordinarias baseadas em dados reais.",
        meetings,
        blockedMeeting,
        autoInputs,
        calendar,
        summary,
      ),
    ],
  };
}

export function buildPersistedQualityHubCatalog(input: {
  serviceOrders: PersistedServiceOrderRecord[];
  nonconformities: PersistedNonconformityRecord[];
  nonconformingWork: PersistedNonconformingWorkRecord[];
  internalAuditCycles: PersistedInternalAuditCycleRecord[];
  managementReviewMeetings: PersistedManagementReviewMeetingRecord[];
  indicatorSnapshots: PersistedQualityIndicatorSnapshotRecord[];
  complianceProfile?: PersistedComplianceProfileRecord | null;
  selectedModuleKey?: QualityHubModule["key"];
}): QualityHubCatalog {
  const indicators = deriveIndicators({
    nowUtc: new Date().toISOString(),
    serviceOrders: input.serviceOrders,
    nonconformities: input.nonconformities,
    nonconformingWork: input.nonconformingWork,
    internalAuditCycles: input.internalAuditCycles,
    managementReviewMeetings: input.managementReviewMeetings,
    indicatorSnapshots: input.indicatorSnapshots,
  });
  const latestMeeting = [...input.managementReviewMeetings].sort(
    (left, right) => right.scheduledForUtc.localeCompare(left.scheduledForUtc),
  )[0];
  const openNcCount = input.nonconformities.filter((record) => record.status !== "ready").length;
  const overdueActions = input.nonconformities.filter(
    (record) => record.status !== "ready" && record.dueAtUtc < new Date().toISOString(),
  ).length;
  const blockerCount =
    input.nonconformities.filter((record) => record.status === "blocked").length +
    input.nonconformingWork.filter((record) => record.status === "blocked").length +
    indicators.filter((indicator) => indicator.status === "blocked").length;
  const status: BuilderStatus =
    blockerCount > 0
      ? "blocked"
      : openNcCount > 0 || indicators.some((indicator) => indicator.status === "attention")
        ? "attention"
        : "ready";
  const modules = buildQualityHubModules(input, indicators);
  const selectedModuleKey = modules.some((module) => module.key === input.selectedModuleKey)
    ? input.selectedModuleKey!
    : modules[0]?.key ?? "nonconformities";
  const implementedModuleCount = modules.filter((module) => module.availability === "implemented").length;
  const plannedModuleCount = modules.filter((module) => module.availability === "planned").length;

  const scenarios = [
    {
      id: "operational-attention" as const,
      label: "Qualidade em operacao real",
      description:
        "O hub consolida NCs, contencao, auditoria, indicadores e analise critica sobre dados persistidos do tenant.",
    },
    {
      id: "critical-response" as const,
      label: "Qualidade em resposta critica",
      description:
        "O hub destaca o recorte fail-closed quando o tenant possui bloqueios reais de Qualidade ou governanca.",
    },
    {
      id: "stable-baseline" as const,
      label: "Qualidade em baseline controlada",
      description:
        "O hub mostra o tenant sem bloqueios criticos e com ciclo de gestao apoiado em dados persistidos.",
    },
  ].map((scenario) => ({
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    selectedModuleKey,
    links: {
      organizationSettingsScenarioId: mapStatusToSettingsScenario(status),
      nonconformityScenarioId: mapStatusToNcScenario(status),
    },
    summary: {
      status,
      organizationName: input.complianceProfile?.organizationName ?? "Organizacao ativa",
      openNonconformities: openNcCount,
      overdueActions,
      auditProgramCount: input.internalAuditCycles.length,
      complaintCount: 0,
      activeRiskCount: input.complianceProfile?.regulatoryProfile === "type_a" ? 1 : 0,
      implementedModuleCount,
      plannedModuleCount,
      nextManagementReviewLabel: latestMeeting?.nextMeetingLabel ?? "Sem reuniao agendada",
      recommendedAction:
        status === "blocked"
          ? "Conter os bloqueios ativos e fechar o follow-up antes de liberar nova evolucao regulatoria."
          : status === "attention"
            ? "Fechar os itens em atencao e levar os desvios reais para a proxima analise critica."
            : "Manter a trilha da V5 estavel, com revisao regulatoria e auditoria interna em dia.",
      blockers:
        status === "blocked"
          ? ["Existem bloqueios reais de Qualidade ou governanca regulatoria no tenant."]
          : [],
      warnings:
        status === "attention"
          ? ["A V5 esta operando sobre dados reais, mas ainda ha follow-up ativo no tenant."]
          : [],
    },
    modules,
  }));

  return {
    selectedScenarioId: inferQualityScenarioId(status, {
      ready: "stable-baseline",
      attention: "operational-attention",
      blocked: "critical-response",
    }),
    scenarios,
  };
}

function buildNonconformityScenario(
  id: "open-attention" | "critical-response" | "resolved-history",
  label: string,
  description: string,
  items: PersistedNonconformityRecord[],
  selectedRecord: PersistedNonconformityRecord,
  totals: ReturnType<typeof summarizeNonconformities>,
) {
  return {
    id,
    label,
    description,
    summary: {
      status: totals.status,
      headline:
        totals.status === "blocked"
          ? "NC critica requer resposta coordenada"
          : totals.status === "attention"
            ? "NCs reais em acompanhamento"
            : "Historico de NCs controlado",
      openCount: totals.openCount,
      criticalCount: totals.criticalCount,
      closedCount: totals.closedCount,
      recommendedAction:
        selectedRecord.status === "blocked"
          ? "Manter o fluxo contido ate concluir a acao corretiva e a evidencia minima."
          : selectedRecord.status === "attention"
            ? "Fechar a acao pendente antes do prazo e manter o vinculo com a OS real."
            : "Preservar a evidencia encerrada como historico auditavel.",
      blockers: selectedRecord.blockers,
      warnings: selectedRecord.warnings,
    },
    selectedNcId: selectedRecord.ncId,
    items: items.map((record) => ({
      ncId: record.ncId,
      summary: record.title,
      originLabel: record.originLabel,
      severityLabel: record.severityLabel,
      ownerLabel: record.ownerLabel,
      ageLabel: humanizeAge(record.openedAtUtc, record.resolvedAtUtc),
      status: record.status,
    })),
    detail: {
      ncId: selectedRecord.ncId,
      title: selectedRecord.title,
      status: selectedRecord.status,
      noticeLabel: selectedRecord.noticeLabel,
      originLabel: selectedRecord.originLabel,
      severityLabel: selectedRecord.severityLabel,
      ownerLabel: selectedRecord.ownerLabel,
      openedAtLabel: formatDateTime(selectedRecord.openedAtUtc),
      dueAtLabel: formatDateTime(selectedRecord.dueAtUtc),
      rootCauseLabel: selectedRecord.rootCauseLabel,
      containmentLabel: selectedRecord.containmentLabel,
      correctiveActionLabel: selectedRecord.correctiveActionLabel,
      evidenceLabel: selectedRecord.evidenceLabel,
      blockers: selectedRecord.blockers,
      warnings: selectedRecord.warnings,
      links: {
        workspaceScenarioId: mapStatusToWorkspaceScenario(selectedRecord.status),
        auditTrailScenarioId: mapStatusToAuditTrailScenario(selectedRecord.status, Boolean(selectedRecord.certificateNumber)),
      },
    },
  };
}

function buildNonconformingWorkScenario(
  id: "contained-attention" | "release-blocked" | "archived-history",
  label: string,
  description: string,
  items: PersistedNonconformingWorkRecord[],
  selectedRecord: PersistedNonconformingWorkRecord,
  totals: ReturnType<typeof summarizeNonconformingWork>,
  nonconformities: PersistedNonconformityRecord[],
) {
  const linkedNc = selectedRecord.nonconformityId
    ? nonconformities.find((record) => record.ncId === selectedRecord.nonconformityId)
    : undefined;

  return {
    id,
    label,
    description,
    summary: {
      status: totals.status,
      headline:
        totals.status === "blocked"
          ? "Trabalho nao conforme bloqueia liberacao"
          : totals.status === "attention"
            ? "Contencao real em acompanhamento"
            : "Historico de contencao restaurado",
      openCaseCount: totals.openCount,
      blockedReleaseCount: totals.blockedCount,
      restoredCount: totals.restoredCount,
      recommendedAction:
        selectedRecord.status === "blocked"
          ? "Nao liberar o fluxo ate regularizar a regra de contencao e a evidencia final."
          : selectedRecord.status === "attention"
            ? "Concluir a evidencia de contencao antes de restaurar o uso do item afetado."
            : "Preservar a restauracao como historico auditavel do tenant.",
      blockers: selectedRecord.blockers,
      warnings: selectedRecord.warnings,
    },
    selectedCaseId: selectedRecord.caseId,
    items: items.map((record) => ({
      caseId: record.caseId,
      titleLabel: record.title,
      affectedEntityLabel: record.affectedEntityLabel,
      originLabel: record.originLabel,
      impactLabel: record.releaseRuleLabel,
      status: record.status,
    })),
    detail: {
      caseId: selectedRecord.caseId,
      title: selectedRecord.title,
      status: selectedRecord.status,
      noticeLabel: selectedRecord.noticeLabel,
      classificationLabel: selectedRecord.classificationLabel,
      originLabel: selectedRecord.originLabel,
      affectedEntityLabel: selectedRecord.affectedEntityLabel,
      containmentLabel: selectedRecord.containmentLabel,
      releaseRuleLabel: selectedRecord.releaseRuleLabel,
      evidenceLabel: selectedRecord.evidenceLabel,
      restorationLabel: selectedRecord.restorationLabel,
      blockers: selectedRecord.blockers,
      warnings: selectedRecord.warnings,
      links: {
        workspaceScenarioId: mapStatusToWorkspaceScenario(selectedRecord.status),
        auditTrailScenarioId: mapStatusToAuditTrailScenario(selectedRecord.status),
        nonconformityScenarioId: linkedNc ? mapStatusToNcScenario(linkedNc.status) : undefined,
      },
    },
  };
}

function buildInternalAuditScenario(
  id: "program-on-track" | "follow-up-attention" | "extraordinary-escalation",
  label: string,
  description: string,
  cycles: PersistedInternalAuditCycleRecord[],
  selectedCycle: PersistedInternalAuditCycleRecord,
  totals: ReturnType<typeof summarizeInternalAudits>,
  findings: InternalAuditFindingItem[],
) {
  return {
    id,
    label,
    description,
    summary: {
      status: totals.status,
      headline:
        totals.status === "blocked"
          ? "Auditoria interna em escalacao extraordinaria"
          : totals.status === "attention"
            ? "Auditoria interna com follow-up aberto"
            : "Programa de auditoria interna controlado",
      programLabel: `Programa ${new Date(selectedCycle.scheduledAtUtc).getUTCFullYear()}`,
      plannedCycleCount: cycles.length,
      completedCycleCount: cycles.filter((cycle) => cycle.status === "ready").length,
      openFindingCount: findings.filter((finding) => finding.status !== "ready").length,
      recommendedAction:
        selectedCycle.status === "blocked"
          ? "Fechar o ciclo extraordinario antes de qualquer liberacao do recorte critico."
          : selectedCycle.status === "attention"
            ? "Concluir o follow-up dos achados reais antes do proximo ciclo."
            : "Manter evidencias e follow-up arquivados no programa anual.",
      blockers: selectedCycle.blockers,
      warnings: selectedCycle.warnings,
    },
    selectedCycleId: selectedCycle.cycleId,
    cycles: cycles.map((cycle) => ({
      cycleId: cycle.cycleId,
      cycleLabel: cycle.cycleLabel,
      windowLabel: cycle.windowLabel,
      scopeLabel: cycle.scopeLabel,
      auditorLabel: cycle.auditorLabel,
      findingsLabel: `${buildAuditFindings(cycle, []).length} achado(s)`,
      status: cycle.status,
      statusLabel:
        cycle.status === "ready"
          ? "Programa controlado"
          : cycle.status === "blocked"
            ? "Escalacao extraordinaria"
            : "Follow-up em aberto",
    })),
    detail: {
      cycleId: selectedCycle.cycleId,
      title: `${selectedCycle.cycleLabel} - ${selectedCycle.scopeLabel}`,
      status: selectedCycle.status,
      noticeLabel: selectedCycle.noticeLabel,
      auditorLabel: selectedCycle.auditorLabel,
      auditeeLabel: selectedCycle.auditeeLabel,
      periodLabel: selectedCycle.periodLabel,
      scopeLabel: selectedCycle.scopeLabel,
      reportLabel: selectedCycle.reportLabel,
      evidenceLabel: selectedCycle.evidenceLabel,
      nextReviewLabel: selectedCycle.nextReviewLabel,
      checklist: toAuditChecklist(selectedCycle.checklist),
      findings,
      blockers: selectedCycle.blockers,
      warnings: selectedCycle.warnings,
      links: {
        nonconformityScenarioId: mapFindingsToNcScenario(findings),
      },
    },
  };
}

function buildManagementReviewScenario(
  id: "ordinary-ready" | "agenda-attention" | "extraordinary-response",
  label: string,
  description: string,
  meetings: PersistedManagementReviewMeetingRecord[],
  selectedMeeting: PersistedManagementReviewMeetingRecord,
  automaticInputs: ManagementReviewAutomaticInput[],
  calendar: ReturnType<typeof buildManagementReviewCalendar>,
  summary: ReturnType<typeof summarizeManagementReviews>,
) {
  return {
    id,
    label,
    description,
    summary: {
      status: summary.status,
      headline:
        summary.status === "blocked"
          ? "Analise critica extraordinaria em curso"
          : summary.status === "attention"
            ? "Analise critica com pauta pendente"
            : "Analise critica arquivada e controlada",
      nextMeetingLabel: selectedMeeting.nextMeetingLabel,
      agendaCount: selectedMeeting.agendaItems.length,
      automaticInputCount: automaticInputs.length,
      openDecisionCount: selectedMeeting.decisions.filter((decision) => decision.status !== "ready").length,
      recommendedAction:
        selectedMeeting.status === "blocked"
          ? "Tratar o recorte extraordinario antes de fechar qualquer release sensivel."
          : selectedMeeting.status === "attention"
            ? "Fechar pauta e deliberacoes pendentes antes de arquivar a ata."
            : "Manter a ata arquivada e carregar os insumos do proximo ciclo.",
      blockers: selectedMeeting.blockers,
      warnings: selectedMeeting.warnings,
    },
    selectedMeetingId: selectedMeeting.meetingId,
    meetings: meetings.map((meeting) => ({
      meetingId: meeting.meetingId,
      dateLabel: meeting.dateLabel,
      titleLabel: meeting.titleLabel,
      outcomeLabel: meeting.outcomeLabel,
      status: meeting.status,
    })),
    detail: {
      meetingId: selectedMeeting.meetingId,
      title: selectedMeeting.titleLabel,
      status: selectedMeeting.status,
      noticeLabel: selectedMeeting.noticeLabel,
      nextMeetingLabel: selectedMeeting.nextMeetingLabel,
      scheduledForLabel: formatManagementReviewSchedule(selectedMeeting.scheduledForUtc),
      chairLabel: selectedMeeting.chairLabel,
      attendeesLabel: selectedMeeting.attendeesLabel,
      periodLabel: selectedMeeting.periodLabel,
      ataLabel: selectedMeeting.ataLabel,
      evidenceLabel: selectedMeeting.evidenceLabel,
      calendarExportHref: buildManagementReviewCalendarExportHref({
        meetingId: selectedMeeting.meetingId,
      }),
      calendar,
      signature: buildManagementReviewSignature({
        heldAtUtc: selectedMeeting.heldAtUtc,
        signedAtUtc: selectedMeeting.signedAtUtc,
        signedByLabel: selectedMeeting.signedByLabel,
        signatureDeviceId: selectedMeeting.signatureDeviceId,
        signatureStatement: selectedMeeting.signatureStatement,
      }),
      agendaItems: selectedMeeting.agendaItems,
      automaticInputs,
      decisions: selectedMeeting.decisions,
      blockers: selectedMeeting.blockers,
      warnings: selectedMeeting.warnings,
    },
  };
}

function buildIndicatorScenario(
  id: "baseline-ready" | "action-sla-attention" | "critical-drift",
  label: string,
  description: string,
  indicators: DerivedIndicator[],
  selectedIndicator: DerivedIndicator,
  summary: ReturnType<typeof summarizeIndicators>,
) {
  return {
    id,
    label,
    description,
    summary: {
      status: summary.status,
      headline:
        summary.status === "blocked"
          ? "Indicadores com deriva critica"
          : summary.status === "attention"
            ? "Indicadores em atencao preventiva"
            : "Indicadores em baseline real",
      monthlyWindowLabel: summary.monthlyWindowLabel,
      indicatorCount: indicators.length,
      attentionCount: summary.attentionCount,
      blockedCount: summary.blockedCount,
      recommendedAction:
        selectedIndicator.status === "blocked"
          ? "Conter o desvio critico antes de seguir com nova publicacao regulatoria."
          : selectedIndicator.status === "attention"
            ? "Corrigir a tendencia antes da proxima analise critica."
            : "Manter o monitoramento continuo do tenant.",
      blockers: selectedIndicator.blockers,
      warnings: selectedIndicator.warnings,
    },
    selectedIndicatorId: selectedIndicator.indicatorId,
    indicators: indicators.map((indicator) => ({
      indicatorId: indicator.indicatorId,
      title: indicator.title,
      currentLabel: formatIndicatorValue(indicator.currentValue, indicator.unitLabel),
      targetLabel: formatIndicatorValue(indicator.targetValue, indicator.unitLabel),
      trendLabel: indicator.trendLabel,
      ownerLabel: indicator.ownerLabel,
      cadenceLabel: indicator.cadenceLabel,
      status: indicator.status,
    })),
    detail: {
      indicatorId: selectedIndicator.indicatorId,
      title: selectedIndicator.title,
      status: selectedIndicator.status,
      noticeLabel:
        selectedIndicator.status === "blocked"
          ? "Desvio critico do tenant"
          : selectedIndicator.status === "attention"
            ? "Indicador em atencao"
            : "Indicador estavel",
      currentLabel: formatIndicatorValue(selectedIndicator.currentValue, selectedIndicator.unitLabel),
      targetLabel: formatIndicatorValue(selectedIndicator.targetValue, selectedIndicator.unitLabel),
      trendLabel: selectedIndicator.trendLabel,
      ownerLabel: selectedIndicator.ownerLabel,
      cadenceLabel: selectedIndicator.cadenceLabel,
      periodLabel: selectedIndicator.periodLabel,
      measurementDefinitionLabel: selectedIndicator.measurementDefinitionLabel,
      evidenceLabel: selectedIndicator.evidenceLabel,
      managementReviewLabel: selectedIndicator.managementReviewLabel,
      snapshots: selectedIndicator.snapshots.map((snapshot) => ({
        monthLabel: snapshot.monthLabel,
        valueLabel: snapshot.valueLabel,
        status: snapshot.status,
      })),
      relatedArtifacts: selectedIndicator.relatedArtifacts,
      blockers: selectedIndicator.blockers,
      warnings: selectedIndicator.warnings,
      links: {
        nonconformityId: selectedIndicator.links.nonconformityId,
        nonconformityScenarioId: selectedIndicator.links.nonconformityScenarioId,
      },
    },
  };
}

function buildQualityHubModules(
  input: {
    nonconformities: PersistedNonconformityRecord[];
    nonconformingWork: PersistedNonconformingWorkRecord[];
    internalAuditCycles: PersistedInternalAuditCycleRecord[];
    managementReviewMeetings: PersistedManagementReviewMeetingRecord[];
    complianceProfile?: PersistedComplianceProfileRecord | null;
  },
  indicators: DerivedIndicator[],
): QualityHubModule[] {
  const latestMeeting = [...input.managementReviewMeetings].sort(
    (left, right) => right.scheduledForUtc.localeCompare(left.scheduledForUtc),
  )[0];
  const implemented: QualityHubModule[] = [
    {
      key: "nonconformities",
      title: "NC e acoes corretivas",
      clauseLabel: "ISO/IEC 17025 7.10 e 8.7",
      metricLabel: `${input.nonconformities.filter((record) => record.status !== "ready").length} NC(s) aberta(s)`,
      summary: "Modulo persistido de nao conformidades sobre OS, certificados e evidencias reais.",
      status: summarizeNonconformities(input.nonconformities).status,
      availability: "implemented",
      href: "/quality/nonconformities",
      ctaLabel: "Abrir NCs",
      nextStepLabel: "Fechar o follow-up da NC real mais critica do tenant.",
      blockers: input.nonconformities.filter((record) => record.status === "blocked").map((record) => record.title),
      warnings: input.nonconformities.filter((record) => record.status === "attention").map((record) => record.title),
    },
    {
      key: "audit-trail",
      title: "Trilha de auditoria",
      clauseLabel: "ISO/IEC 17025 7.5 e 8.4",
      metricLabel: "Fluxo central persistido",
      summary: "A trilha critica continua operando sobre eventos reais da emissao e da reemissao.",
      status: input.nonconformities.some((record) => record.status === "blocked") ? "blocked" : "ready",
      availability: "implemented",
      href: "/quality/audit-trail",
      ctaLabel: "Abrir trilha",
      nextStepLabel: "Conferir a ultima cadeia real antes do proximo rito de release.",
      blockers: [],
      warnings: [],
    },
    {
      key: "nonconforming-work",
      title: "Trabalho nao conforme",
      clauseLabel: "ISO/IEC 17025 7.10",
      metricLabel: `${input.nonconformingWork.filter((record) => record.status !== "ready").length} caso(s) ativos`,
      summary: "Modulo persistido de contencao e restauracao segura do fluxo real.",
      status: summarizeNonconformingWork(input.nonconformingWork).status,
      availability: "implemented",
      href: "/quality/nonconforming-work",
      ctaLabel: "Abrir contencao",
      nextStepLabel: "Concluir a regra de liberacao do caso mais recente.",
      blockers: input.nonconformingWork.filter((record) => record.status === "blocked").map((record) => record.title),
      warnings: input.nonconformingWork.filter((record) => record.status === "attention").map((record) => record.title),
    },
    {
      key: "internal-audit",
      title: "Auditoria interna",
      clauseLabel: "ISO/IEC 17025 8.8",
      metricLabel: `${input.internalAuditCycles.length} ciclo(s) persistidos`,
      summary: "Programa real de auditoria interna com ciclos, checklist e achados sobre evidencias persistidas.",
      status: summarizeInternalAudits(input.internalAuditCycles, input.nonconformities).status,
      availability: "implemented",
      href: "/quality/internal-audit",
      ctaLabel: "Abrir auditoria",
      nextStepLabel: "Fechar o follow-up do ciclo aberto antes do proximo ciclo.",
      blockers: input.internalAuditCycles.filter((record) => record.status === "blocked").map((record) => record.cycleLabel),
      warnings: input.internalAuditCycles.filter((record) => record.status === "attention").map((record) => record.cycleLabel),
    },
    {
      key: "management-review",
      title: "Analise critica",
      clauseLabel: "ISO/IEC 17025 8.9",
      metricLabel: latestMeeting?.titleLabel ?? "Sem reuniao agendada",
      summary: "Reunioes e deliberacoes persistidas da direcao sobre dados reais do tenant.",
      status: summarizeManagementReviews(input.managementReviewMeetings).status,
      availability: "implemented",
      href: "/quality/management-review",
      ctaLabel: "Abrir analise critica",
      nextStepLabel: "Levar os desvios reais para a proxima reuniao.",
      blockers: input.managementReviewMeetings.filter((record) => record.status === "blocked").map((record) => record.titleLabel),
      warnings: input.managementReviewMeetings.filter((record) => record.status === "attention").map((record) => record.titleLabel),
    },
    {
      key: "indicators",
      title: "Indicadores",
      clauseLabel: "ISO/IEC 17025 8.9",
      metricLabel: `${indicators.filter((indicator) => indicator.status !== "ready").length} alerta(s)`,
      summary: "Indicadores V5 derivados do estado persistido do fluxo central e da Qualidade ativa.",
      status: summarizeIndicators(indicators).status,
      availability: "implemented",
      href: "/quality/indicators",
      ctaLabel: "Abrir indicadores",
      nextStepLabel: "Corrigir a tendencia do indicador mais pressionado do tenant.",
      blockers: indicators.filter((indicator) => indicator.status === "blocked").map((indicator) => indicator.title),
      warnings: indicators.filter((indicator) => indicator.status === "attention").map((indicator) => indicator.title),
    },
  ];

  const planned: QualityHubModule[] = [
    {
      key: "complaints",
      title: "Reclamacoes",
      clauseLabel: "ISO/IEC 17025 7.9",
      metricLabel: "Leitura canonica preservada",
      summary: "O modulo segue disponivel como leitura canônica, sem persistencia dedicada nesta fatia.",
      status: "attention",
      availability: "planned",
      href: "/quality/complaints?scenario=open-follow-up",
      ctaLabel: "Abrir reclamacoes",
      nextStepLabel: "Conectar o workflow transacional de reclamacoes em evolucao futura.",
      blockers: [],
      warnings: ["Ainda nao ha persistencia dedicada para reclamacoes na V5."],
    },
    {
      key: "risk-impartiality",
      title: "Imparcialidade e riscos",
      clauseLabel: "ISO/IEC 17025 4.1 e 8.5",
      metricLabel: input.complianceProfile?.regulatoryProfile === "type_a" ? "Perfil Tipo A ativo" : "Monitoramento minimo",
      summary: "Riscos seguem visiveis no recorte canônico; a V5 integra governanca regulatoria sem abrir workflow dedicado de riscos.",
      status: input.complianceProfile?.regulatoryProfile === "type_a" ? "attention" : "ready",
      availability: "planned",
      href: "/quality/risk-register?scenario=stable-monitoring",
      ctaLabel: "Abrir riscos",
      nextStepLabel: "Planejar persistencia dedicada quando a trilha de riscos virar fatia propria.",
      blockers: [],
      warnings: [],
    },
    {
      key: "documents",
      title: "Documentos da qualidade",
      clauseLabel: "ISO/IEC 17025 8.3 e 8.4",
      metricLabel: input.complianceProfile?.releaseNormVersion
        ? `Release ${input.complianceProfile.releaseNormVersion}`
        : "Acervo canônico",
      summary: "A V5 integra governanca normativa ao tenant, mas o GED transacional segue evolucao futura.",
      status: "attention",
      availability: "planned",
      href: "/quality/documents?scenario=operational-ready",
      ctaLabel: "Abrir documentos",
      nextStepLabel: "Expandir o controle documental transacional em fatia futura.",
      blockers: [],
      warnings: ["GED e anexos binarios continuam fora desta fatia."],
    },
  ];

  return [...implemented, ...planned];
}

function deriveIndicators(input: {
  nowUtc: string;
  serviceOrders: PersistedServiceOrderRecord[];
  nonconformities: PersistedNonconformityRecord[];
  nonconformingWork: PersistedNonconformingWorkRecord[];
  internalAuditCycles: PersistedInternalAuditCycleRecord[];
  managementReviewMeetings: PersistedManagementReviewMeetingRecord[];
  indicatorSnapshots: PersistedQualityIndicatorSnapshotRecord[];
}): DerivedIndicator[] {
  const totalOrders = Math.max(1, input.serviceOrders.length);
  const emittedOrders = input.serviceOrders.filter((record) => record.workflowStatus === "emitted").length;
  const reissuedOrders = input.serviceOrders.filter((record) => record.certificateRevision && record.certificateRevision !== "R0").length;
  const openNc = input.nonconformities.filter((record) => record.status !== "ready").length;
  const blockedNc = input.nonconformities.filter((record) => record.status === "blocked").length;
  const blockedWork = input.nonconformingWork.filter((record) => record.status === "blocked").length;
  const openAuditCycles = input.internalAuditCycles.filter((record) => record.status !== "ready").length;
  const openMeetings = input.managementReviewMeetings.filter((record) => record.status !== "ready").length;

  const indicators: DerivedIndicator[] = [
    {
      indicatorId: "indicator-emission-completion",
      title: "OS emitidas no fluxo persistido",
      currentValue: round((emittedOrders / totalOrders) * 100),
      targetValue: 85,
      unitLabel: "%",
      trendLabel: emittedOrders >= totalOrders / 2 ? "Estavel" : "Abaixo da meta",
      ownerLabel: "Operacoes",
      cadenceLabel: "Semanal",
      periodLabel: "Recorte operacional atual",
      measurementDefinitionLabel: "Percentual de OS do tenant em status emitido sobre o total persistido.",
      evidenceLabel: `${emittedOrders}/${totalOrders} OS emitidas no fluxo central persistido.`,
      managementReviewLabel: "Levar a taxa de conclusao para a proxima analise critica.",
      relatedArtifacts: ["service_orders", "emission_audit_events"],
      blockers: [],
      warnings: emittedOrders / totalOrders < 0.85 ? ["A taxa de emissao esta abaixo da meta configurada."] : [],
      status: emittedOrders / totalOrders < 0.6 ? "blocked" : emittedOrders / totalOrders < 0.85 ? "attention" : "ready",
      snapshots: buildFallbackPercentageSnapshots((emittedOrders / totalOrders) * 100),
      links: {},
    },
    {
      indicatorId: "indicator-open-nc-pressure",
      title: "Pressao de NC aberta",
      currentValue: openNc,
      targetValue: 1,
      unitLabel: " NC",
      trendLabel: blockedNc > 0 ? "Critico" : openNc > 1 ? "Em alta" : "Controlado",
      ownerLabel: "Gestao da Qualidade",
      cadenceLabel: "Semanal",
      periodLabel: "Recorte da Qualidade ativa",
      measurementDefinitionLabel: "Quantidade de NCs nao encerradas sobre o tenant persistido.",
      evidenceLabel: `${openNc} NC(s) aberta(s) vinculadas a registros reais.`,
      managementReviewLabel: "Usar este indicador para priorizar follow-up de NCs na analise critica.",
      relatedArtifacts: ["nonconformities", "nonconforming_work_cases"],
      blockers: blockedNc > 0 ? ["Existe pelo menos uma NC critica em aberto."] : [],
      warnings: openNc > 1 ? ["O tenant acumulou mais NCs abertas que a meta."] : [],
      status: blockedNc > 0 ? "blocked" : openNc > 1 ? "attention" : "ready",
      snapshots: buildFallbackCountSnapshots(openNc),
      links: {
        nonconformityId: input.nonconformities[0]?.ncId,
        nonconformityScenarioId: input.nonconformities[0]
          ? mapStatusToNcScenario(input.nonconformities[0].status)
          : undefined,
      },
    },
    {
      indicatorId: "indicator-governance-follow-up",
      title: "Follow-up de governanca da V5",
      currentValue: openAuditCycles + openMeetings + blockedWork + reissuedOrders,
      targetValue: 1,
      unitLabel: " item(ns)",
      trendLabel:
        openAuditCycles + openMeetings + blockedWork + reissuedOrders > 2 ? "Acima do tolerado" : "Sob acompanhamento",
      ownerLabel: "Direcao e Qualidade",
      cadenceLabel: "Mensal",
      periodLabel: "Ciclo gerencial atual",
      measurementDefinitionLabel:
        "Soma de ciclos/atas em aberto, contencoes bloqueadas e reemissoes que exigem follow-up gerencial.",
      evidenceLabel: `${openAuditCycles} auditoria(s), ${openMeetings} reuniao(oes), ${blockedWork} contencao(oes) e ${reissuedOrders} reemissao(oes).`,
      managementReviewLabel: "Consolidar este numero como insumo obrigatorio da analise critica.",
      relatedArtifacts: ["internal_audit_cycles", "management_review_meetings", "certificate_publications"],
      blockers:
        openMeetings > 0 && blockedWork > 0 ? ["Ha follow-up gerencial bloqueante combinado com contencao ativa."] : [],
      warnings:
        openAuditCycles + openMeetings + blockedWork + reissuedOrders > 1
          ? ["O tenant possui mais follow-up gerencial do que a meta da V5."]
          : [],
      status:
        openMeetings > 0 && blockedWork > 0
          ? "blocked"
          : openAuditCycles + openMeetings + blockedWork + reissuedOrders > 1
            ? "attention"
            : "ready",
      snapshots: buildFallbackCountSnapshots(openAuditCycles + openMeetings + blockedWork + reissuedOrders),
      links: {
        nonconformityId: input.nonconformities.find((record) => record.status !== "ready")?.ncId,
        nonconformityScenarioId: input.nonconformities.find((record) => record.status !== "ready")
          ? mapStatusToNcScenario(input.nonconformities.find((record) => record.status !== "ready")!.status)
          : undefined,
      },
    },
  ];

  return indicators.map((indicator) =>
    applyHistoricalSnapshots(indicator, input.indicatorSnapshots.filter((snapshot) => snapshot.indicatorId === indicator.indicatorId)),
  );
}

function buildManagementReviewAutomaticInputs(input: {
  serviceOrders: PersistedServiceOrderRecord[];
  nonconformities: PersistedNonconformityRecord[];
  internalAuditCycles: PersistedInternalAuditCycleRecord[];
  complianceProfile?: PersistedComplianceProfileRecord | null;
}): ManagementReviewAutomaticInput[] {
  const emitted = input.serviceOrders.filter((record) => record.workflowStatus === "emitted").length;
  const openNc = input.nonconformities.filter((record) => record.status !== "ready").length;
  const openAudits = input.internalAuditCycles.filter((record) => record.status !== "ready").length;
  const profile = input.complianceProfile;

  return [
    {
      key: "input-nc",
      label: "Nao conformidades abertas",
      valueLabel: `${openNc} NC(s) em follow-up`,
      sourceLabel: "Qualidade",
      status: openNc > 1 ? "attention" : "ready",
      href: "/quality/nonconformities",
    },
    {
      key: "input-audit",
      label: "Auditoria interna",
      valueLabel: `${openAudits} ciclo(s) com follow-up`,
      sourceLabel: "Auditoria",
      status: openAudits > 0 ? "attention" : "ready",
      href: "/quality/internal-audit",
    },
    {
      key: "input-emission",
      label: "Fluxo operacional",
      valueLabel: `${emitted} certificado(s) emitido(s) no tenant`,
      sourceLabel: "Emissao",
      status: emitted === 0 ? "blocked" : "ready",
      href: "/emission/service-order-review",
    },
    {
      key: "input-regulatory",
      label: "Perfil regulatorio",
      valueLabel: profile ? `${profile.regulatoryProfile} · ${profile.releaseNormVersion}` : "Perfil nao configurado",
      sourceLabel: "Governanca regulatoria",
      status: profile ? (profile.releaseNormStatus.toLowerCase().includes("pending") ? "attention" : "ready") : "blocked",
      href: "/settings/organization",
    },
  ];
}

function buildAuditFindings(
  cycle: PersistedInternalAuditCycleRecord,
  nonconformities: PersistedNonconformityRecord[],
): InternalAuditFindingItem[] {
  const findings = cycle.findingRefs
    .map((findingId) => nonconformities.find((record) => record.ncId === findingId))
    .filter((record): record is PersistedNonconformityRecord => Boolean(record))
    .map((record) => ({
      findingId: record.ncId,
      title: record.title,
      severityLabel: record.severityLabel,
      ownerLabel: record.ownerLabel,
      dueDateLabel: formatDateTime(record.dueAtUtc),
      status: record.status,
      nonconformityId: record.ncId,
    }));

  if (findings.length > 0) {
    return findings;
  }

  return [
    {
      findingId: `${cycle.cycleId}-finding-1`,
      title: cycle.reportLabel,
      severityLabel: cycle.status === "blocked" ? "Critica" : cycle.status === "attention" ? "Moderada" : "Controlada",
      ownerLabel: cycle.auditorLabel,
      dueDateLabel: cycle.nextReviewLabel,
      status: cycle.status,
    },
  ];
}

function toAuditChecklist(checklist: PersistedInternalAuditCycleRecord["checklist"]): InternalAuditChecklistItem[] {
  if (checklist.length > 0) {
    return checklist;
  }

  return [
    {
      key: "fallback-checklist",
      requirementLabel: "Ciclo registrado com evidencia minima",
      evidenceLabel: "Checklist padrao gerado a partir do registro persistido do ciclo.",
      status: "attention",
    },
  ];
}

function summarizeNonconformities(records: PersistedNonconformityRecord[]) {
  const openCount = records.filter((record) => record.status !== "ready").length;
  const criticalCount = records.filter((record) => record.status === "blocked").length;
  const closedCount = records.filter((record) => record.status === "ready").length;
  const status: BuilderStatus = criticalCount > 0 ? "blocked" : openCount > 0 ? "attention" : "ready";
  return { openCount, criticalCount, closedCount, status };
}

function summarizeNonconformingWork(records: PersistedNonconformingWorkRecord[]) {
  const openCount = records.filter((record) => record.status !== "ready").length;
  const blockedCount = records.filter((record) => record.status === "blocked").length;
  const restoredCount = records.filter((record) => record.status === "ready").length;
  const status: BuilderStatus = blockedCount > 0 ? "blocked" : openCount > 0 ? "attention" : "ready";
  return { openCount, blockedCount, restoredCount, status };
}

function summarizeInternalAudits(
  cycles: PersistedInternalAuditCycleRecord[],
  nonconformities: PersistedNonconformityRecord[],
) {
  const blockedCount =
    cycles.filter((cycle) => cycle.status === "blocked").length +
    nonconformities.filter((record) => record.status === "blocked").length;
  const openCount =
    cycles.filter((cycle) => cycle.status !== "ready").length +
    nonconformities.filter((record) => record.status === "attention").length;
  const status: BuilderStatus = blockedCount > 0 ? "blocked" : openCount > 0 ? "attention" : "ready";
  return { status };
}

function summarizeManagementReviews(meetings: PersistedManagementReviewMeetingRecord[]) {
  const blockedCount = meetings.filter((meeting) => meeting.status === "blocked").length;
  const attentionCount = meetings.filter((meeting) => meeting.status === "attention").length;
  const status: BuilderStatus = blockedCount > 0 ? "blocked" : attentionCount > 0 ? "attention" : "ready";
  return { status };
}

function summarizeIndicators(indicators: DerivedIndicator[]) {
  const attentionCount = indicators.filter((indicator) => indicator.status === "attention").length;
  const blockedCount = indicators.filter((indicator) => indicator.status === "blocked").length;
  const status: BuilderStatus = blockedCount > 0 ? "blocked" : attentionCount > 0 ? "attention" : "ready";
  return {
    attentionCount,
    blockedCount,
    status,
    monthlyWindowLabel: describeMonthlyWindow(indicators),
  };
}

function buildFallbackPercentageSnapshots(currentValue: number): DerivedIndicator["snapshots"] {
  const currentStatus: BuilderStatus = currentValue < 60 ? "blocked" : currentValue < 85 ? "attention" : "ready";
  return [
    { monthStartUtc: "2025-11-01T00:00:00.000Z", monthLabel: "M-5", valueLabel: `${round(Math.max(0, currentValue - 10))}%`, status: "attention" as const },
    { monthStartUtc: "2025-12-01T00:00:00.000Z", monthLabel: "M-4", valueLabel: `${round(Math.max(0, currentValue - 7))}%`, status: "attention" as const },
    { monthStartUtc: "2026-01-01T00:00:00.000Z", monthLabel: "M-3", valueLabel: `${round(Math.max(0, currentValue - 5))}%`, status: "ready" as const },
    { monthStartUtc: "2026-02-01T00:00:00.000Z", monthLabel: "M-2", valueLabel: `${round(Math.max(0, currentValue - 3))}%`, status: "ready" as const },
    { monthStartUtc: "2026-03-01T00:00:00.000Z", monthLabel: "M-1", valueLabel: `${round(Math.max(0, currentValue - 1))}%`, status: "ready" as const },
    { monthStartUtc: "2026-04-01T00:00:00.000Z", monthLabel: "Atual", valueLabel: `${round(currentValue)}%`, status: currentStatus },
  ];
}

function buildFallbackCountSnapshots(currentValue: number): DerivedIndicator["snapshots"] {
  return [
    { monthStartUtc: "2025-11-01T00:00:00.000Z", monthLabel: "M-5", valueLabel: `${Math.max(0, currentValue - 1)}`, status: "ready" as const },
    { monthStartUtc: "2025-12-01T00:00:00.000Z", monthLabel: "M-4", valueLabel: `${Math.max(0, currentValue - 1)}`, status: "ready" as const },
    { monthStartUtc: "2026-01-01T00:00:00.000Z", monthLabel: "M-3", valueLabel: `${Math.max(0, currentValue)}`, status: currentValue > 1 ? "attention" as const : "ready" as const },
    { monthStartUtc: "2026-02-01T00:00:00.000Z", monthLabel: "M-2", valueLabel: `${Math.max(0, currentValue + (currentValue > 0 ? 0 : 1))}`, status: currentValue > 2 ? "blocked" as const : currentValue > 1 ? "attention" as const : "ready" as const },
    { monthStartUtc: "2026-03-01T00:00:00.000Z", monthLabel: "M-1", valueLabel: `${Math.max(0, currentValue)}`, status: currentValue > 2 ? "blocked" as const : currentValue > 1 ? "attention" as const : "ready" as const },
    { monthStartUtc: "2026-04-01T00:00:00.000Z", monthLabel: "Atual", valueLabel: `${currentValue}`, status: currentValue > 2 ? "blocked" as const : currentValue > 1 ? "attention" as const : "ready" as const },
  ];
}

function applyHistoricalSnapshots(
  indicator: DerivedIndicator,
  snapshots: PersistedQualityIndicatorSnapshotRecord[],
): DerivedIndicator {
  if (snapshots.length === 0) {
    return {
      ...indicator,
      warnings: mergeUnique(
        indicator.warnings,
        "Ainda nao ha historico mensal persistido para este indicador.",
      ),
    };
  }

  const ordered = [...snapshots]
    .sort((left, right) => left.monthStartUtc.localeCompare(right.monthStartUtc))
    .slice(-6);
  const latest = ordered[ordered.length - 1]!;
  const previous = ordered.length > 1 ? ordered[ordered.length - 2]! : null;
  const latestValue = latest.valueNumeric;
  const latestTarget = latest.targetNumeric ?? indicator.targetValue;
  const normalizedSnapshots = ordered.map((snapshot) => ({
    monthStartUtc: snapshot.monthStartUtc,
    monthLabel: formatMonthLabel(snapshot.monthStartUtc),
    valueLabel: formatIndicatorValue(snapshot.valueNumeric, indicator.unitLabel),
    status: snapshot.status,
  }));

  return {
    ...indicator,
    currentValue: latestValue,
    targetValue: latestTarget,
    status: latest.status,
    trendLabel: describeHistoricalTrend(indicator.unitLabel, previous?.valueNumeric, latestValue, latest.status),
    periodLabel: `Historico mensal persistido de ${formatMonthLabel(ordered[0]!.monthStartUtc)} a ${formatMonthLabel(latest.monthStartUtc)}`,
    evidenceLabel: `${indicator.evidenceLabel} Historico persistido: ${ordered.length} snapshot(s) ate ${formatMonthLabel(latest.monthStartUtc)} (${latest.sourceLabel}).`,
    managementReviewLabel: `Levar a serie consolidada ate ${formatMonthLabel(latest.monthStartUtc)} para a proxima analise critica.`,
    snapshots: normalizedSnapshots,
    blockers:
      latest.status === "blocked"
        ? mergeUnique(indicator.blockers, "O ultimo fechamento mensal consolidado ficou em deriva critica.")
        : indicator.blockers,
    warnings:
      ordered.length < 3
        ? mergeUnique(indicator.warnings, "Historico mensal ainda curto para leitura longitudinal.")
        : indicator.warnings,
  };
}

function describeHistoricalTrend(
  unitLabel: string,
  previousValue: number | undefined,
  currentValue: number,
  status: BuilderStatus,
) {
  if (previousValue === undefined) {
    return status === "blocked"
      ? "Primeiro fechamento mensal em deriva critica"
      : status === "attention"
        ? "Primeiro fechamento mensal em atencao"
        : "Primeiro fechamento mensal registrado";
  }

  const delta = round(currentValue - previousValue);
  const signedDelta = delta > 0 ? `+${delta}` : `${delta}`;
  const normalizedUnit = unitLabel.trim();

  if (normalizedUnit === "%") {
    return `${signedDelta} p.p. vs mes anterior`;
  }

  return `${signedDelta} ${normalizedUnit} vs mes anterior`;
}

function describeMonthlyWindow(indicators: DerivedIndicator[]) {
  const monthStarts = indicators.flatMap((indicator) => indicator.snapshots.map((snapshot) => snapshot.monthStartUtc));
  if (monthStarts.length === 0) {
    return "Sem historico mensal consolidado";
  }

  const ordered = [...monthStarts].sort();
  return `Historico mensal de ${formatMonthLabel(ordered[0]!)} a ${formatMonthLabel(ordered[ordered.length - 1]!)}`;
}

function mergeUnique(values: string[], extra: string) {
  return values.includes(extra) ? values : [...values, extra];
}

function compareStatusThenDate<
  T extends {
    status: BuilderStatus;
    dueAtUtc?: string;
    updatedAtUtc?: string;
    openedAtUtc?: string;
  },
>(left: T, right: T) {
  if (left.status !== right.status) {
    return weight(right.status) - weight(left.status);
  }
  const leftDate = left.dueAtUtc ?? left.updatedAtUtc ?? left.openedAtUtc ?? "";
  const rightDate = right.dueAtUtc ?? right.updatedAtUtc ?? right.openedAtUtc ?? "";
  return leftDate.localeCompare(rightDate);
}

function selectRecord<T extends { ncId?: string; caseId?: string; cycleId?: string; meetingId?: string }>(
  records: T[],
  selectedId?: string,
) {
  const selected =
    records.find((record) =>
      [record.ncId, record.caseId, record.cycleId, record.meetingId].includes(selectedId),
    ) ?? records[0];

  if (!selected) {
    throw new Error("persisted_quality_records_empty");
  }

  return selected;
}

function pickFirstByStatus<T extends { status: BuilderStatus }>(records: T[], status: BuilderStatus) {
  return records.find((record) => record.status === status);
}

function inferQualityScenarioId<T extends string>(
  status: BuilderStatus,
  map: { ready: T; attention: T; blocked: T },
) {
  return map[status];
}

function mapStatusToNcScenario(
  status: BuilderStatus,
): "open-attention" | "critical-response" | "resolved-history" {
  return status === "blocked" ? "critical-response" : status === "attention" ? "open-attention" : "resolved-history";
}

function mapStatusToWorkspaceScenario(
  status: BuilderStatus,
): "release-blocked" | "team-attention" | "baseline-ready" {
  return status === "blocked" ? "release-blocked" : status === "attention" ? "team-attention" : "baseline-ready";
}

function mapStatusToSettingsScenario(
  status: BuilderStatus,
): "profile-change-blocked" | "renewal-attention" | "operational-ready" {
  return status === "blocked"
    ? "profile-change-blocked"
    : status === "attention"
      ? "renewal-attention"
      : "operational-ready";
}

function mapStatusToAuditTrailScenario(
  status: BuilderStatus,
  hasCertificate = false,
): "reissue-attention" | "recent-emission" | "integrity-blocked" {
  if (status === "blocked") {
    return "integrity-blocked";
  }

  if (hasCertificate) {
    return "reissue-attention";
  }

  return "recent-emission";
}

function mapFindingsToNcScenario(
  findings: InternalAuditFindingItem[],
): "open-attention" | "critical-response" | "resolved-history" {
  if (findings.some((finding) => finding.status === "blocked")) {
    return "critical-response";
  }

  if (findings.some((finding) => finding.status === "attention")) {
    return "open-attention";
  }

  return "resolved-history";
}

function formatDateTime(value: string | undefined) {
  if (!value) {
    return "Sem data";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function formatMonthLabel(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function humanizeAge(openedAtUtc: string, resolvedAtUtc?: string) {
  const start = new Date(openedAtUtc).getTime();
  const end = new Date(resolvedAtUtc ?? new Date().toISOString()).getTime();
  const days = Math.max(0, Math.round((end - start) / (24 * 60 * 60 * 1000)));
  return `${days} dia(s)`;
}

function formatIndicatorValue(value: number, unitLabel: string) {
  if (unitLabel === "%") {
    return `${round(value)}%`;
  }
  return `${round(value)}${unitLabel}`;
}

function round(value: number) {
  return Math.round(value * 10) / 10;
}

function weight(status: BuilderStatus) {
  return status === "blocked" ? 3 : status === "attention" ? 2 : 1;
}
