import type {
  EmissionDryRunScenarioId,
  EmissionWorkspaceScenarioId,
  ProcedureDetail,
  ProcedureListItem,
  ProcedureRegistryCatalog,
  ProcedureRegistryScenario,
  ProcedureRegistryScenarioId,
  RegistryOperationalStatus,
  ServiceOrderReviewScenarioId,
} from "@afere/contracts";

type ProcedureRecord = {
  procedureId: string;
  code: string;
  title: string;
  typeLabel: string;
  revisionLabel: string;
  effectiveSinceLabel: string;
  effectiveUntilLabel?: string;
  lifecycleLabel: string;
  usageLabel: string;
  scopeLabel: string;
  environmentRangeLabel: string;
  curvePolicyLabel: string;
  standardsPolicyLabel: string;
  approvalLabel: string;
  relatedDocuments: string[];
  workspaceScenarioId?: EmissionWorkspaceScenarioId;
  serviceOrderScenarioId?: ServiceOrderReviewScenarioId;
  reviewItemId?: string;
  dryRunScenarioId?: EmissionDryRunScenarioId;
};

type ScenarioProcedureState = {
  procedureId: string;
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

type ProcedureRegistryScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedProcedureId: string;
  procedures: ScenarioProcedureState[];
};

const PROCEDURE_RECORDS: Record<string, ProcedureRecord> = {
  "procedure-pt005-r04": {
    procedureId: "procedure-pt005-r04",
    code: "PT-005",
    title: "Calibracao IPNA classe III campo",
    typeLabel: "NAWI III",
    revisionLabel: "04",
    effectiveSinceLabel: "desde 03/24",
    lifecycleLabel: "Vigente",
    usageLabel: "Campo controlado e bancada assistida",
    scopeLabel: "Balanças IPNA classe III em faixa ate 300 kg com 5 pontos de curva.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
    curvePolicyLabel: "5 pontos (10% / 25% / 50% / 75% / 100%) com sequencia crescente e decrescente.",
    standardsPolicyLabel: "Peso F1/M1 vigente + auxiliar ambiental TH-003 obrigatorio.",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 03/2024",
    relatedDocuments: [
      "IT-005-1 · Checklist de campo",
      "FR-021 · Registro bruto da curva",
      "BAL-UNC-IPNA-III · Balanco de incerteza",
    ],
    workspaceScenarioId: "baseline-ready",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
    dryRunScenarioId: "type-b-ready",
  },
  "procedure-pt006-r02": {
    procedureId: "procedure-pt006-r02",
    code: "PT-006",
    title: "Calibracao IPNA bancada",
    typeLabel: "NAWI",
    revisionLabel: "02",
    effectiveSinceLabel: "desde 11/23",
    lifecycleLabel: "Vigente",
    usageLabel: "Bancada interna",
    scopeLabel: "Balanças NAWI de bancada com curva reduzida e controle ambiental interno.",
    environmentRangeLabel: "Temp 20C-24C · Umid 40%-60%",
    curvePolicyLabel: "4 pontos (0% / 25% / 50% / 100%) com repetibilidade em 50%.",
    standardsPolicyLabel: "Pesos F1/F2 vigentes conforme capacidade da balança.",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 11/2023",
    relatedDocuments: [
      "IT-006-1 · Preparacao de bancada",
      "FR-022 · Registro de repetibilidade",
    ],
    workspaceScenarioId: "baseline-ready",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00135",
    dryRunScenarioId: "type-b-ready",
  },
  "procedure-pt009-r02": {
    procedureId: "procedure-pt009-r02",
    code: "PT-009",
    title: "Calibracao IPNA ambiente ampliado",
    typeLabel: "NAWI III especial",
    revisionLabel: "02",
    effectiveSinceLabel: "desde 02/24",
    lifecycleLabel: "Vigente com revisao pendente",
    usageLabel: "Campo com condicoes variaveis",
    scopeLabel: "Balanças IPNA classe III com janela de ambiente ampliada e conferencia reforcada.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70% · revisao em curso",
    curvePolicyLabel: "5 pontos com checagem adicional de historico e desvio de metodo documentado.",
    standardsPolicyLabel: "Padroes M1 vigentes e evidencia fotografica obrigatoria.",
    approvalLabel: "Revisao de qualidade aberta para abril/2026",
    relatedDocuments: [
      "IT-009-1 · Lista de desvios controlados",
      "FR-030 · Conferencia de historico",
      "NC-014 · Acao preventiva associada",
    ],
    workspaceScenarioId: "team-attention",
    serviceOrderScenarioId: "review-blocked",
    reviewItemId: "os-2026-00147",
    dryRunScenarioId: "type-c-blocked",
  },
  "procedure-pg001-r01": {
    procedureId: "procedure-pg001-r01",
    code: "PG-001",
    title: "Controle de documentos",
    typeLabel: "Gestao",
    revisionLabel: "01",
    effectiveSinceLabel: "desde 01/24",
    lifecycleLabel: "Vigente",
    usageLabel: "Governanca da qualidade",
    scopeLabel: "Documentos MQ/PG/PT/IT/FR com controle de vigencia e obsolescencia.",
    environmentRangeLabel: "Nao aplicavel",
    curvePolicyLabel: "Nao aplicavel",
    standardsPolicyLabel: "Nao aplicavel",
    approvalLabel: "Aprovado por Ana Costa · vigencia desde 01/2024",
    relatedDocuments: [
      "MQ-001 · Manual da qualidade",
      "IT-DOC-01 · Fluxo de publicacao",
    ],
  },
  "procedure-pt005-r03": {
    procedureId: "procedure-pt005-r03",
    code: "PT-005",
    title: "Calibracao IPNA classe III campo",
    typeLabel: "NAWI III",
    revisionLabel: "03",
    effectiveSinceLabel: "desde 09/23",
    effectiveUntilLabel: "ate 03/24",
    lifecycleLabel: "Obsoleto",
    usageLabel: "Consulta historica apenas",
    scopeLabel: "Revisao mantida apenas para rastreabilidade historica de OS antigas.",
    environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
    curvePolicyLabel: "5 pontos historicos sem os ajustes documentados da rev. 04.",
    standardsPolicyLabel: "Padroes vigentes exigidos somente para consulta de historico.",
    approvalLabel: "Substituido pela rev. 04 em 03/2024",
    relatedDocuments: [
      "FR-021 rev.03 · Registro historico",
      "Ata de substituicao da rev. 04",
    ],
    workspaceScenarioId: "release-blocked",
  },
};

const SCENARIOS: Record<ProcedureRegistryScenarioId, ProcedureRegistryScenarioDefinition> = {
  "operational-ready": {
    label: "Procedimentos vigentes prontos para uso",
    description: "Recorte operacional com procedimentos vigentes, sem revisao critica pendente para o selecionado.",
    recommendedAction: "Seguir com os procedimentos vigentes e manter apenas a vigilancia de rotina da qualidade.",
    selectedProcedureId: "procedure-pt005-r04",
    procedures: [
      { procedureId: "procedure-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pt006-r02", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pg001-r01", status: "ready", blockers: [], warnings: [] },
      {
        procedureId: "procedure-pt009-r02",
        status: "attention",
        blockers: [],
        warnings: ["Revisao da qualidade agendada para 30/04/2026."],
      },
      {
        procedureId: "procedure-pt005-r03",
        status: "blocked",
        blockers: ["Revisao obsoleta mantida apenas para rastreabilidade."],
        warnings: [],
      },
    ],
  },
  "revision-attention": {
    label: "Procedimento com revisao proxima",
    description: "Recorte com procedimento vigente, mas sob atencao por revisao de qualidade e acao preventiva em aberto.",
    recommendedAction: "Concluir a revisao do procedimento selecionado antes da proxima rodada operacional sensivel.",
    selectedProcedureId: "procedure-pt009-r02",
    procedures: [
      { procedureId: "procedure-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pt006-r02", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pg001-r01", status: "ready", blockers: [], warnings: [] },
      {
        procedureId: "procedure-pt009-r02",
        status: "attention",
        blockers: [],
        warnings: [
          "Revisao da qualidade agendada para 30/04/2026.",
          "NC-014 recomenda reforco na conferencia de historico.",
        ],
      },
      {
        procedureId: "procedure-pt005-r03",
        status: "blocked",
        blockers: ["Revisao obsoleta mantida apenas para rastreabilidade."],
        warnings: [],
      },
    ],
  },
  "obsolete-visible": {
    label: "Revisao obsoleta visivel para auditoria",
    description: "Recorte com uma revisao obsoleta ainda consultavel para trilha historica, mas bloqueada para novas OS.",
    recommendedAction: "Usar a revisao vigente correspondente e manter a obsoleta apenas para consulta auditavel.",
    selectedProcedureId: "procedure-pt005-r03",
    procedures: [
      { procedureId: "procedure-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pt006-r02", status: "ready", blockers: [], warnings: [] },
      { procedureId: "procedure-pg001-r01", status: "ready", blockers: [], warnings: [] },
      {
        procedureId: "procedure-pt009-r02",
        status: "attention",
        blockers: [],
        warnings: ["Revisao da qualidade agendada para 30/04/2026."],
      },
      {
        procedureId: "procedure-pt005-r03",
        status: "blocked",
        blockers: ["Revisao obsoleta nao pode ser selecionada para novas OS."],
        warnings: ["Manter apenas como evidencia historica para auditoria."],
      },
    ],
  },
};

const DEFAULT_SCENARIO: ProcedureRegistryScenarioId = "operational-ready";

export function listProcedureRegistryScenarios(): ProcedureRegistryScenario[] {
  return (Object.keys(SCENARIOS) as ProcedureRegistryScenarioId[]).map((scenarioId) =>
    resolveProcedureRegistryScenario(scenarioId),
  );
}

export function resolveProcedureRegistryScenario(
  scenarioId?: string,
  procedureId?: string,
): ProcedureRegistryScenario {
  const definition = SCENARIOS[isProcedureRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO];
  const items = definition.procedures.map(buildProcedureListItem);
  const selectedProcedure =
    items.find((item) => item.procedureId === procedureId) ??
    items.find((item) => item.procedureId === definition.selectedProcedureId) ??
    items[0];

  if (!selectedProcedure) {
    throw new Error("missing_procedure_registry_items");
  }

  const detail = buildProcedureDetail(definition, selectedProcedure.procedureId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildProcedureRegistrySummary(definition.recommendedAction, items, detail),
    selectedProcedureId: selectedProcedure.procedureId,
    items,
    detail,
  };
}

export function buildProcedureRegistryCatalog(
  scenarioId?: string,
  procedureId?: string,
): ProcedureRegistryCatalog {
  const selectedScenario = resolveProcedureRegistryScenario(scenarioId, procedureId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listProcedureRegistryScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildProcedureListItem(state: ScenarioProcedureState): ProcedureListItem {
  const record = getProcedureRecord(state.procedureId);

  return {
    procedureId: record.procedureId,
    code: record.code,
    title: record.title,
    typeLabel: record.typeLabel,
    revisionLabel: record.revisionLabel,
    effectiveSinceLabel: record.effectiveSinceLabel,
    effectiveUntilLabel: record.effectiveUntilLabel,
    lifecycleLabel: record.lifecycleLabel,
    usageLabel: record.usageLabel,
    status: state.status,
  };
}

function buildProcedureDetail(
  definition: ProcedureRegistryScenarioDefinition,
  procedureId: string,
): ProcedureDetail {
  const record = getProcedureRecord(procedureId);
  const state = getScenarioProcedureState(definition, procedureId);

  return {
    procedureId: record.procedureId,
    title: `${record.code} rev.${record.revisionLabel} · ${record.title}`,
    status: state.status,
    noticeLabel: buildProcedureNoticeLabel(state.status, record.lifecycleLabel),
    scopeLabel: record.scopeLabel,
    environmentRangeLabel: record.environmentRangeLabel,
    curvePolicyLabel: record.curvePolicyLabel,
    standardsPolicyLabel: record.standardsPolicyLabel,
    approvalLabel: record.approvalLabel,
    relatedDocuments: record.relatedDocuments,
    blockers: uniqueStrings(state.blockers),
    warnings: uniqueStrings(state.warnings),
    links: {
      workspaceScenarioId: record.workspaceScenarioId,
      serviceOrderScenarioId: record.serviceOrderScenarioId,
      reviewItemId: record.reviewItemId,
      dryRunScenarioId: record.dryRunScenarioId,
    },
  };
}

function buildProcedureRegistrySummary(
  recommendedAction: string,
  items: ProcedureListItem[],
  detail: ProcedureDetail,
): ProcedureRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Procedimentos vigentes prontos para sustentar a operacao"
        : detail.status === "attention"
          ? "Procedimento vigente exige revisao preventiva"
          : "Revisao obsoleta visivel apenas para trilha historica",
    activeCount: items.filter((item) => item.status === "ready").length,
    attentionCount: items.filter((item) => item.status === "attention").length,
    obsoleteCount: items.filter((item) => item.status === "blocked").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function buildProcedureNoticeLabel(
  status: RegistryOperationalStatus,
  lifecycleLabel: string,
): string {
  if (status === "blocked") {
    return `${lifecycleLabel} e indisponivel para novas OS.`;
  }

  if (status === "attention") {
    return `${lifecycleLabel} com revisao de qualidade pendente.`;
  }

  return `${lifecycleLabel} e liberado para uso no recorte atual.`;
}

function getProcedureRecord(procedureId: string): ProcedureRecord {
  const record = PROCEDURE_RECORDS[procedureId];
  if (!record) {
    throw new Error(`missing_procedure_record:${procedureId}`);
  }

  return record;
}

function getScenarioProcedureState(
  definition: ProcedureRegistryScenarioDefinition,
  procedureId: string,
): ScenarioProcedureState {
  const state = definition.procedures.find((item) => item.procedureId === procedureId);
  if (!state) {
    throw new Error(`missing_procedure_state:${procedureId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): ProcedureRegistryScenarioId {
  return isProcedureRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function isProcedureRegistryScenarioId(
  value: string | undefined,
): value is ProcedureRegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}
