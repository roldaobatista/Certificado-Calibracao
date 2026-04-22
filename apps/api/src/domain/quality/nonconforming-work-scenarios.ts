import type {
  NonconformingWorkCatalog,
  NonconformingWorkDetail,
  NonconformingWorkListItem,
  NonconformingWorkScenario,
  NonconformingWorkScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type NonconformingWorkRecord = {
  caseId: string;
  title: string;
  titleLabel: string;
  affectedEntityLabel: string;
  originLabel: string;
  impactLabel: string;
  classificationLabel: string;
  noticeLabel: string;
  containmentLabel: string;
  releaseRuleLabel: string;
  evidenceLabel: string;
  restorationLabel: string;
  links: NonconformingWorkDetail["links"];
};

type ScenarioCaseState = {
  caseId: string;
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

type NonconformingWorkScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedCaseId: string;
  items: ScenarioCaseState[];
};

const RECORDS: Record<string, NonconformingWorkRecord> = {
  "ncw-014": {
    caseId: "ncw-014",
    title: "Trabalho nao conforme em contencao preventiva",
    titleLabel: "PT-005/PT-006/PT-008 sob suspensao preventiva",
    affectedEntityLabel: "PT-005, PT-006 e PT-008",
    originLabel: "Auditoria 2026/Ciclo 1",
    impactLabel: "3 procedimento(s) suspenso(s) para novas OS",
    classificationLabel: "Suspensao preventiva de procedimento",
    noticeLabel:
      "A acao imediata de 7.10 ja foi aplicada, mas a liberacao ainda depende de evidencia tecnica e documental.",
    containmentLabel:
      "Suspender o uso dos PT-005, PT-006 e PT-008 ate o balanco de incerteza estar completo e referenciado no fluxo documental.",
    releaseRuleLabel:
      "Liberar somente apos registrar a revisao minima, anexar a evidencia correspondente e validar o retorno ao uso pelo mesmo recorte da Qualidade.",
    evidenceLabel:
      "Comunicado interno de suspensao, referencia ao PG-005 e pendencia documental da revisao preventiva arquivados no SGQ.",
    restorationLabel:
      "Retornar os procedimentos ao uso apenas quando a revisao controlada estiver registrada e o recorte deixar de depender de interpretacao manual.",
    links: {
      workspaceScenarioId: "team-attention",
      nonconformityScenarioId: "open-attention",
      procedureScenarioId: "revision-attention",
      qualityDocumentScenarioId: "revision-attention",
      documentId: "document-pg005-r02",
    },
  },
  "ncw-015": {
    caseId: "ncw-015",
    title: "Trabalho nao conforme bloqueia liberacao do recorte critico",
    titleLabel: "OS-2026-00147 congelada e sem liberacao para reemissao",
    affectedEntityLabel: "OS-2026-00147 e certificado vinculado",
    originLabel: "Reclamacao critica + trilha divergente",
    impactLabel: "1 OS congelada e 1 liberacao de certificado bloqueada",
    classificationLabel: "Bloqueio de liberacao e reemissao",
    noticeLabel:
      "O recorte critico exige contencao explicita antes de qualquer nova assinatura, liberacao operacional ou reemissao.",
    containmentLabel:
      "Congelar a OS, impedir nova assinatura e manter a resposta final do caso bloqueada ate a validacao conjunta de NC, trilha e reclamacao.",
    releaseRuleLabel:
      "Se a correcao depender de alterar leitura bruta, padrao ou ambiente, a saida nao e reemissao controlada: o PRD exige nova OS e preservacao integral do historico anterior.",
    evidenceLabel:
      "RECL-007, trilha com hash divergente, status da OS bloqueada e parecer preliminar da Qualidade consolidados no mesmo recorte.",
    restorationLabel:
      "Liberar somente apos decisao formal da Qualidade; se o recorte tecnico mudou, abrir nova OS e manter a anterior apenas como historico auditavel.",
    links: {
      workspaceScenarioId: "release-blocked",
      auditTrailScenarioId: "integrity-blocked",
      nonconformityScenarioId: "critical-response",
      complaintScenarioId: "critical-response",
      serviceOrderScenarioId: "review-blocked",
      reviewItemId: "os-2026-00147",
      complaintId: "recl-007",
    },
  },
  "ncw-011": {
    caseId: "ncw-011",
    title: "Historico de trabalho nao conforme encerrado",
    titleLabel: "Contencao historica encerrada e arquivada",
    affectedEntityLabel: "OS-2026-00142 e lote documental correlato",
    originLabel: "Historico SGQ",
    impactLabel: "Nenhuma contencao aberta no recorte atual",
    classificationLabel: "Historico encerrado",
    noticeLabel:
      "O caso foi formalmente encerrado e permanece visivel apenas para rastreabilidade e reaproveitamento de aprendizado.",
    containmentLabel:
      "O lote permaneceu retido ate a conferencia final e a emissao foi revalidada antes do retorno ao fluxo regular.",
    releaseRuleLabel:
      "A liberacao ja foi formalizada; o caso nao reabre o fluxo atual e serve apenas como precedente auditavel do SGQ.",
    evidenceLabel:
      "Ata de encerramento, checklist revisado, historico da OS e registro de treinamento arquivados no dossie da Qualidade.",
    restorationLabel:
      "Sem acoes pendentes. O recorte segue somente como historico e nao exige nova contencao operacional.",
    links: {
      workspaceScenarioId: "baseline-ready",
      auditTrailScenarioId: "recent-emission",
      nonconformityScenarioId: "resolved-history",
      serviceOrderScenarioId: "review-ready",
      reviewItemId: "os-2026-00142",
      qualityDocumentScenarioId: "operational-ready",
      documentId: "document-pg005-r02",
    },
  },
};

const SCENARIOS: Record<NonconformingWorkScenarioId, NonconformingWorkScenarioDefinition> = {
  "contained-attention": {
    label: "Contencao preventiva em acompanhamento",
    description:
      "A acao imediata de 7.10 ja foi registrada, mas o retorno seguro ao fluxo ainda depende de evidencia minima no mesmo recorte da Qualidade.",
    recommendedAction:
      "Manter a suspensao preventiva ate a evidencia documental minima ficar completa e registrar a liberacao no mesmo contexto auditavel.",
    selectedCaseId: "ncw-014",
    items: [
      {
        caseId: "ncw-014",
        status: "attention",
        blockers: [],
        warnings: [
          "A liberacao ainda depende da revisao documental controlada e nao deve voltar por acordo informal.",
        ],
      },
    ],
  },
  "release-blocked": {
    label: "Liberacao bloqueada por trabalho nao conforme",
    description:
      "O recorte critico exige contencao formal, com bloqueio de liberacao e regra explicita para impedir reemissao indevida.",
    recommendedAction:
      "Manter a OS congelada, registrar a decisao formal da Qualidade e abrir nova OS caso a correcao altere o recorte tecnico original.",
    selectedCaseId: "ncw-015",
    items: [
      {
        caseId: "ncw-015",
        status: "blocked",
        blockers: [
          "A liberacao do caso continua vedada enquanto a trilha divergente e a NC critica nao forem saneadas.",
        ],
        warnings: [
          "A resposta ao cliente e a regra de reemissao precisam seguir o mesmo parecer formal da Qualidade.",
        ],
      },
    ],
  },
  "archived-history": {
    label: "Historico arquivado sem contencao aberta",
    description:
      "O caso foi encerrado, liberado e mantido apenas para rastreabilidade, sem contencao operacional ativa no recorte atual.",
    recommendedAction:
      "Manter o historico arquivado, reaproveitar o aprendizado no SGQ e abrir nova contencao apenas se surgir um recorte novo de 7.10.",
    selectedCaseId: "ncw-011",
    items: [
      {
        caseId: "ncw-011",
        status: "ready",
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: NonconformingWorkScenarioId = "contained-attention";

export function listNonconformingWorkScenarios(): NonconformingWorkScenario[] {
  return (Object.keys(SCENARIOS) as NonconformingWorkScenarioId[]).map((scenarioId) =>
    resolveNonconformingWorkScenario(scenarioId),
  );
}

export function resolveNonconformingWorkScenario(
  scenarioId?: string,
  caseId?: string,
): NonconformingWorkScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildListItem);
  const selectedItem =
    items.find((item) => item.caseId === caseId) ??
    items.find((item) => item.caseId === definition.selectedCaseId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_nonconforming_work_items");
  }

  const detail = buildDetail(definition, selectedItem.caseId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, items, detail),
    selectedCaseId: selectedItem.caseId,
    items,
    detail,
  };
}

export function buildNonconformingWorkCatalog(
  scenarioId?: string,
  caseId?: string,
): NonconformingWorkCatalog {
  const selectedScenario = resolveNonconformingWorkScenario(scenarioId, caseId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listNonconformingWorkScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildListItem(state: ScenarioCaseState): NonconformingWorkListItem {
  const record = getRecord(state.caseId);

  return {
    caseId: record.caseId,
    titleLabel: record.titleLabel,
    affectedEntityLabel: record.affectedEntityLabel,
    originLabel: record.originLabel,
    impactLabel: record.impactLabel,
    status: state.status,
  };
}

function buildDetail(
  definition: NonconformingWorkScenarioDefinition,
  caseId: string,
): NonconformingWorkDetail {
  const record = getRecord(caseId);
  const state = getState(definition, caseId);

  return {
    caseId: record.caseId,
    title: record.title,
    status: state.status,
    noticeLabel: record.noticeLabel,
    classificationLabel: record.classificationLabel,
    originLabel: record.originLabel,
    affectedEntityLabel: record.affectedEntityLabel,
    containmentLabel: record.containmentLabel,
    releaseRuleLabel: record.releaseRuleLabel,
    evidenceLabel: record.evidenceLabel,
    restorationLabel: record.restorationLabel,
    blockers: state.blockers,
    warnings: state.warnings,
    links: record.links,
  };
}

function buildSummary(
  recommendedAction: string,
  items: NonconformingWorkListItem[],
  detail: NonconformingWorkDetail,
): NonconformingWorkScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Historico de trabalho nao conforme arquivado e sem contencao aberta"
        : detail.status === "attention"
          ? "Contencao preventiva ativa para trabalho nao conforme"
          : "Trabalho nao conforme bloqueia liberacao e reemissao do recorte critico",
    openCaseCount: items.filter((item) => item.status !== "ready").length,
    blockedReleaseCount: items.filter((item) => item.status === "blocked").length,
    restoredCount: items.filter((item) => item.status === "ready").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getRecord(caseId: string): NonconformingWorkRecord {
  const record = RECORDS[caseId];
  if (!record) {
    throw new Error(`missing_nonconforming_work_record:${caseId}`);
  }

  return record;
}

function getState(
  definition: NonconformingWorkScenarioDefinition,
  caseId: string,
): ScenarioCaseState {
  const state = definition.items.find((item) => item.caseId === caseId);
  if (!state) {
    throw new Error(`missing_nonconforming_work_state:${caseId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): NonconformingWorkScenarioId {
  return isNonconformingWorkScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): NonconformingWorkScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isNonconformingWorkScenarioId(
  value: string | undefined,
): value is NonconformingWorkScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
