import type {
  NonconformityDetail,
  NonconformityListItem,
  NonconformityRegistryCatalog,
  NonconformityRegistryScenario,
  NonconformityRegistryScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type NonconformityRecord = {
  ncId: string;
  title: string;
  summary: string;
  originLabel: string;
  severityLabel: string;
  ownerLabel: string;
  ageLabel: string;
  openedAtLabel: string;
  dueAtLabel: string;
  rootCauseLabel: string;
  containmentLabel: string;
  correctiveActionLabel: string;
  evidenceLabel: string;
  workspaceScenarioId?: NonconformityDetail["links"]["workspaceScenarioId"];
  auditTrailScenarioId?: NonconformityDetail["links"]["auditTrailScenarioId"];
  procedureScenarioId?: NonconformityDetail["links"]["procedureScenarioId"];
  serviceOrderScenarioId?: NonconformityDetail["links"]["serviceOrderScenarioId"];
  reviewItemId?: string;
};

type ScenarioNonconformityState = {
  ncId: string;
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

type NonconformityScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedNcId: string;
  items: ScenarioNonconformityState[];
};

const RECORDS: Record<string, NonconformityRecord> = {
  "nc-014": {
    ncId: "nc-014",
    title: "NC-014 · Padrao usado proximo ao vencimento",
    summary: "Padrao usado proximo ao vencimento em janela operacional critica.",
    originLabel: "Auditoria interna",
    severityLabel: "Media",
    ownerLabel: "Maria Souza",
    ageLabel: "12d",
    openedAtLabel: "10/04/2026",
    dueAtLabel: "24/04/2026",
    rootCauseLabel: "Planejamento preventivo de recalibracao iniciado tarde para o conjunto de padroes M1.",
    containmentLabel: "Uso do padrao mantido somente em OS com dupla conferencia e janela curta de reserva.",
    correctiveActionLabel: "Antecipar reserva da recalibracao e revisar o procedimento PT-009 antes da proxima agenda sensivel.",
    evidenceLabel: "NC-014, FR-030, historico do padrao PESO-005 e ata da qualidade.",
    workspaceScenarioId: "team-attention",
    auditTrailScenarioId: "reissue-attention",
    procedureScenarioId: "revision-attention",
    serviceOrderScenarioId: "history-pending",
    reviewItemId: "os-2026-00141",
  },
  "nc-015": {
    ncId: "nc-015",
    title: "NC-015 · Cliente reportou divergencia de valor",
    summary: "Divergencia reportada pelo cliente com impacto potencial em emissao ja concluida.",
    originLabel: "Reclamacao de cliente",
    severityLabel: "Alta",
    ownerLabel: "Joao Silva",
    ageLabel: "3d",
    openedAtLabel: "19/04/2026",
    dueAtLabel: "22/04/2026",
    rootCauseLabel: "Suspeita de inconsistência entre cadeia de assinatura e historico operacional da OS bloqueada.",
    containmentLabel: "Emissao relacionada congelada, exportacao da trilha bloqueada e cliente notificado de investigacao.",
    correctiveActionLabel: "Executar investigacao de integridade, validar hash-chain e decidir por reexecucao ou cancelamento da OS.",
    evidenceLabel: "Reclamacao formal, trilha da OS-2026-00147 e parecer preliminar do gestor da qualidade.",
    workspaceScenarioId: "release-blocked",
    auditTrailScenarioId: "integrity-blocked",
    procedureScenarioId: "revision-attention",
    serviceOrderScenarioId: "review-blocked",
    reviewItemId: "os-2026-00147",
  },
  "nc-011": {
    ncId: "nc-011",
    title: "NC-011 · Divergencia documental encerrada",
    summary: "Nao conformidade documental encerrada apos ajuste de fluxo e evidencia complementar.",
    originLabel: "Auditoria interna",
    severityLabel: "Baixa",
    ownerLabel: "Ana Costa",
    ageLabel: "Fechada",
    openedAtLabel: "14/03/2026",
    dueAtLabel: "22/03/2026",
    rootCauseLabel: "Ausencia de evidência complementar em um lote já regularizado.",
    containmentLabel: "Lote retido até conferência final e emissão revalidada pelo responsável técnico.",
    correctiveActionLabel: "Checklist documental atualizado e treinamento concluído com a equipe.",
    evidenceLabel: "Ata de encerramento, checklist revisado e evidência de treinamento.",
    workspaceScenarioId: "baseline-ready",
    auditTrailScenarioId: "recent-emission",
    procedureScenarioId: "operational-ready",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
  },
};

const SCENARIOS: Record<NonconformityRegistryScenarioId, NonconformityScenarioDefinition> = {
  "open-attention": {
    label: "NC aberta em acompanhamento",
    description: "Recorte com NC moderada ainda aberta, sob contenção e ação corretiva em andamento.",
    recommendedAction: "Fechar a ação corretiva dentro do prazo e manter a dupla conferencia até a evidência final.",
    selectedNcId: "nc-014",
    items: [
      {
        ncId: "nc-014",
        status: "attention",
        blockers: [],
        warnings: ["Acao corretiva vence em 2 dias e ainda depende de evidência complementar."],
      },
      {
        ncId: "nc-015",
        status: "blocked",
        blockers: ["Reclamacao critica ainda bloqueia o fluxo relacionado."],
        warnings: [],
      },
      {
        ncId: "nc-011",
        status: "ready",
        blockers: [],
        warnings: [],
      },
    ],
  },
  "critical-response": {
    label: "NC critica bloqueante",
    description: "Recorte com uma NC de alta severidade ainda aberta e com impacto direto na operacao.",
    recommendedAction: "Priorizar a investigacao critica e manter bloqueado o fluxo afetado ate decisao formal.",
    selectedNcId: "nc-015",
    items: [
      {
        ncId: "nc-014",
        status: "attention",
        blockers: [],
        warnings: ["Acao corretiva vence em 2 dias e ainda depende de evidência complementar."],
      },
      {
        ncId: "nc-015",
        status: "blocked",
        blockers: ["NC critica aberta com impacto direto no fluxo de emissao."],
        warnings: ["Cliente aguarda posicionamento formal da investigacao."],
      },
      {
        ncId: "nc-011",
        status: "ready",
        blockers: [],
        warnings: [],
      },
    ],
  },
  "resolved-history": {
    label: "Historico de NC encerrada",
    description: "Recorte com NC encerrada e mantida apenas como histórico auditável da qualidade.",
    recommendedAction: "Manter a evidência arquivada e reutilizar o aprendizado no checklist vigente.",
    selectedNcId: "nc-011",
    items: [
      {
        ncId: "nc-014",
        status: "attention",
        blockers: [],
        warnings: ["Acao corretiva vence em 2 dias e ainda depende de evidência complementar."],
      },
      {
        ncId: "nc-015",
        status: "blocked",
        blockers: ["NC critica aberta com impacto direto no fluxo de emissao."],
        warnings: [],
      },
      {
        ncId: "nc-011",
        status: "ready",
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: NonconformityRegistryScenarioId = "open-attention";

export function listNonconformityScenarios(): NonconformityRegistryScenario[] {
  return (Object.keys(SCENARIOS) as NonconformityRegistryScenarioId[]).map((scenarioId) =>
    resolveNonconformityScenario(scenarioId),
  );
}

export function resolveNonconformityScenario(
  scenarioId?: string,
  ncId?: string,
): NonconformityRegistryScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildListItem);
  const selectedItem =
    items.find((item) => item.ncId === ncId) ??
    items.find((item) => item.ncId === definition.selectedNcId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_nonconformity_items");
  }

  const detail = buildDetail(definition, selectedItem.ncId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, items, detail),
    selectedNcId: selectedItem.ncId,
    items,
    detail,
  };
}

export function buildNonconformityCatalog(
  scenarioId?: string,
  ncId?: string,
): NonconformityRegistryCatalog {
  const selectedScenario = resolveNonconformityScenario(scenarioId, ncId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listNonconformityScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildListItem(state: ScenarioNonconformityState): NonconformityListItem {
  const record = getRecord(state.ncId);

  return {
    ncId: record.ncId,
    summary: record.summary,
    originLabel: record.originLabel,
    severityLabel: record.severityLabel,
    ownerLabel: record.ownerLabel,
    ageLabel: record.ageLabel,
    status: state.status,
  };
}

function buildDetail(
  definition: NonconformityScenarioDefinition,
  ncId: string,
): NonconformityDetail {
  const record = getRecord(ncId);
  const state = getState(definition, ncId);

  return {
    ncId: record.ncId,
    title: record.title,
    status: state.status,
    noticeLabel:
      state.status === "ready"
        ? "NC encerrada e mantida apenas para histórico."
        : state.status === "attention"
          ? "NC aberta sob acompanhamento e ação corretiva."
          : "NC crítica aberta com impacto bloqueante na operação.",
    originLabel: record.originLabel,
    severityLabel: record.severityLabel,
    ownerLabel: record.ownerLabel,
    openedAtLabel: record.openedAtLabel,
    dueAtLabel: record.dueAtLabel,
    rootCauseLabel: record.rootCauseLabel,
    containmentLabel: record.containmentLabel,
    correctiveActionLabel: record.correctiveActionLabel,
    evidenceLabel: record.evidenceLabel,
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      workspaceScenarioId: record.workspaceScenarioId,
      auditTrailScenarioId: record.auditTrailScenarioId,
      procedureScenarioId: record.procedureScenarioId,
      serviceOrderScenarioId: record.serviceOrderScenarioId,
      reviewItemId: record.reviewItemId,
    },
  };
}

function buildSummary(
  recommendedAction: string,
  items: NonconformityListItem[],
  detail: NonconformityDetail,
): NonconformityRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Historico de NCs encerradas disponivel para auditoria"
        : detail.status === "attention"
          ? "NC aberta exige acompanhamento da qualidade"
          : "NC critica bloqueia o fluxo operacional relacionado",
    openCount: items.filter((item) => item.status !== "ready").length,
    criticalCount: items.filter((item) => item.status === "blocked").length,
    closedCount: items.filter((item) => item.status === "ready").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getRecord(ncId: string): NonconformityRecord {
  const record = RECORDS[ncId];
  if (!record) {
    throw new Error(`missing_nonconformity_record:${ncId}`);
  }

  return record;
}

function getState(
  definition: NonconformityScenarioDefinition,
  ncId: string,
): ScenarioNonconformityState {
  const state = definition.items.find((item) => item.ncId === ncId);
  if (!state) {
    throw new Error(`missing_nonconformity_state:${ncId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): NonconformityRegistryScenarioId {
  return isNonconformityScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): NonconformityScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isNonconformityScenarioId(
  value: string | undefined,
): value is NonconformityRegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
