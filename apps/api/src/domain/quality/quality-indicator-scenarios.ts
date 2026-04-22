import type {
  QualityIndicatorCard,
  QualityIndicatorDetail,
  QualityIndicatorRegistryCatalog,
  QualityIndicatorRegistryScenario,
  QualityIndicatorScenarioId,
  QualityIndicatorSnapshot,
  RegistryOperationalStatus,
} from "@afere/contracts";

type IndicatorRecord = {
  indicatorId: string;
  title: string;
  targetLabel: string;
  ownerLabel: string;
  cadenceLabel: string;
  measurementDefinitionLabel: string;
  evidenceLabel: string;
  managementReviewLabel: string;
  relatedArtifacts: string[];
};

type ScenarioIndicatorState = {
  indicatorId: string;
  currentLabel: string;
  trendLabel: string;
  status: RegistryOperationalStatus;
  snapshots: QualityIndicatorSnapshot[];
  blockers: string[];
  warnings: string[];
  complaintScenarioId?: QualityIndicatorDetail["links"]["complaintScenarioId"];
  complaintId?: QualityIndicatorDetail["links"]["complaintId"];
  nonconformityScenarioId?: QualityIndicatorDetail["links"]["nonconformityScenarioId"];
  nonconformityId?: QualityIndicatorDetail["links"]["nonconformityId"];
  riskRegisterScenarioId?: QualityIndicatorDetail["links"]["riskRegisterScenarioId"];
  riskId?: QualityIndicatorDetail["links"]["riskId"];
};

type QualityIndicatorScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedIndicatorId: string;
  indicators: ScenarioIndicatorState[];
};

const PERIOD_LABEL = "Ultimos 12 meses consolidados ate 04/2026";
const MONTHS = [
  "05/2025",
  "06/2025",
  "07/2025",
  "08/2025",
  "09/2025",
  "10/2025",
  "11/2025",
  "12/2025",
  "01/2026",
  "02/2026",
  "03/2026",
  "04/2026",
] as const;

const INDICATORS: Record<string, IndicatorRecord> = {
  "indicator-reissue-free": {
    indicatorId: "indicator-reissue-free",
    title: "% certificados sem reemissao",
    targetLabel: "Meta >= 98,0%",
    ownerLabel: "Ana Costa",
    cadenceLabel: "Mensal",
    measurementDefinitionLabel:
      "Percentual de certificados emitidos no periodo sem reemissao por erro tecnico ou desvio de revisao.",
    evidenceLabel:
      "Snapshot mensal de emissao, amostra de certificados e trilha de reemissao controlada arquivados no dossie da Qualidade.",
    managementReviewLabel:
      "Levar a serie para a analise critica com destaque para desvios tecnicos, retrabalho e necessidade de reforco na revisao.",
    relatedArtifacts: [
      "Painel de certificados emitidos",
      "Registro de reemissoes controladas",
      "Checklist de revisao tecnica",
    ],
  },
  "indicator-nc-rate": {
    indicatorId: "indicator-nc-rate",
    title: "Taxa de NC por area",
    targetLabel: "Meta <= 3 NC por area critica / trimestre",
    ownerLabel: "Ana Costa",
    cadenceLabel: "Mensal",
    measurementDefinitionLabel:
      "Quantidade consolidada de NCs abertas ou reabertas por area critica no recorte rolling usado pela Qualidade.",
    evidenceLabel:
      "Snapshot mensal por area, consolidado de NCs abertas e classificacao de severidade exportavel para dossie.",
    managementReviewLabel:
      "Usar a tendencia por area para priorizar auditoria interna, treinamento, revisao documental e acao corretiva.",
    relatedArtifacts: [
      "Registro de NCs por area",
      "Plano anual de auditoria interna",
      "Treinamentos por area critica",
    ],
  },
  "indicator-os-cycle-time": {
    indicatorId: "indicator-os-cycle-time",
    title: "Tempo medio por OS",
    targetLabel: "Meta <= 35 min",
    ownerLabel: "Carlos",
    cadenceLabel: "Mensal",
    measurementDefinitionLabel:
      "Tempo medio entre inicio da execucao e liberacao para revisao tecnica por ordem de servico concluida.",
    evidenceLabel:
      "Consolidado mensal do workspace, tempos de execucao e amostras por tipo de OS arquivados para auditoria.",
    managementReviewLabel:
      "Apresentar a tendencia operacional com gargalos por tipo de servico e impacto na capacidade de entrega.",
    relatedArtifacts: [
      "Workspace de emissao",
      "Fila de revisao tecnica",
      "Distribuicao por tipo de OS",
    ],
  },
  "indicator-capa-sla": {
    indicatorId: "indicator-capa-sla",
    title: "% acoes corretivas no prazo",
    targetLabel: "Meta >= 90,0%",
    ownerLabel: "Ana Costa",
    cadenceLabel: "Mensal",
    measurementDefinitionLabel:
      "Percentual de acoes corretivas encerradas dentro do prazo aprovado no periodo consolidado.",
    evidenceLabel:
      "Consolidado de NCs, prazos de CAPA e comprovantes de encerramento arquivados no dossie de follow-up.",
    managementReviewLabel:
      "Levar a aderencia ao prazo para a analise critica e revisar responsaveis, recursos ou escalacao quando a meta cair.",
    relatedArtifacts: ["NC-014 e NC-015", "Plano CAPA", "Checklist de follow-up de acoes"],
  },
  "indicator-capa-effectiveness": {
    indicatorId: "indicator-capa-effectiveness",
    title: "Eficacia das acoes corretivas",
    targetLabel: "Meta >= 95,0%",
    ownerLabel: "Ana Costa",
    cadenceLabel: "Trimestral com leitura mensal",
    measurementDefinitionLabel:
      "Percentual de acoes corretivas concluidas sem reincidencia confirmada no periodo de verificacao.",
    evidenceLabel:
      "Historico de reincidencia, verificacoes de eficacia e validacoes da Qualidade arquivadas para auditoria.",
    managementReviewLabel:
      "Avaliar reincidencia e decidir reforco de treinamento, auditoria ou revisao procedimental quando a eficacia cair.",
    relatedArtifacts: [
      "Verificacao de eficacia",
      "Historico de reincidencia",
      "Ata de follow-up de NC",
    ],
  },
  "indicator-client-satisfaction": {
    indicatorId: "indicator-client-satisfaction",
    title: "% satisfacao do cliente",
    targetLabel: "Meta NPS >= 70",
    ownerLabel: "Maria Souza",
    cadenceLabel: "Mensal",
    measurementDefinitionLabel:
      "NPS consolidado das respostas fechadas do periodo, com destaque para feedback critico e reclamacoes formais.",
    evidenceLabel:
      "Pesquisa mensal de NPS, respostas abertas e correlacao com reclamacoes formais arquivadas no dossie.",
    managementReviewLabel:
      "Usar a tendencia para calibrar tempo de resposta, comunicacao com cliente e eficacia percebida da operacao.",
    relatedArtifacts: ["Pesquisa NPS mensal", "Registro de reclamacoes", "Plano de resposta ao cliente"],
  },
};

const SCENARIOS: Record<QualityIndicatorScenarioId, QualityIndicatorScenarioDefinition> = {
  "baseline-ready": {
    label: "Indicadores estaveis e dentro da meta",
    description:
      "Recorte com os ultimos 12 meses controlados, sem deriva critica e pronto para compor a analise critica ordinaria.",
    recommendedAction:
      "Manter a cadencia de coleta, arquivar os snapshots mensais e reutilizar o consolidado na proxima analise critica.",
    selectedIndicatorId: "indicator-reissue-free",
    indicators: [
      {
        indicatorId: "indicator-reissue-free",
        currentLabel: "99,3%",
        trendLabel: "+0,4 p.p. vs media anual",
        status: "ready",
        snapshots: makePercentSnapshots(
          [98.9, 99.0, 99.1, 99.0, 99.2, 99.3, 99.4, 99.1, 99.2, 99.3, 99.4, 99.3],
          98.0,
          97.0,
        ),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-nc-rate",
        currentLabel: "Equipamentos 1 | Pessoal 0",
        trendLabel: "-1 NC vs trimestre anterior",
        status: "ready",
        snapshots: makeTextSnapshots([
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 1 | Pes 1", status: "ready" },
          { valueLabel: "Eq 1 | Pes 1", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
        ]),
        blockers: [],
        warnings: [],
        nonconformityScenarioId: "resolved-history",
        nonconformityId: "nc-011",
      },
      {
        indicatorId: "indicator-os-cycle-time",
        currentLabel: "32 min",
        trendLabel: "-2 min vs media anual",
        status: "ready",
        snapshots: makeUpperBoundMinuteSnapshots([34, 34, 33, 33, 32, 31, 32, 32, 31, 32, 33, 32], 35, 38),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-capa-sla",
        currentLabel: "94,6%",
        trendLabel: "+3,1 p.p. vs trimestre anterior",
        status: "ready",
        snapshots: makePercentSnapshots(
          [90.5, 91.1, 91.8, 92.4, 93.0, 93.2, 93.9, 94.1, 94.2, 94.4, 94.5, 94.6],
          90.0,
          80.0,
        ),
        blockers: [],
        warnings: [],
        nonconformityScenarioId: "resolved-history",
        nonconformityId: "nc-011",
      },
      {
        indicatorId: "indicator-capa-effectiveness",
        currentLabel: "100,0%",
        trendLabel: "Sem reincidencia nos ultimos 12 meses",
        status: "ready",
        snapshots: makePercentSnapshots(
          [95.0, 96.0, 96.5, 97.0, 97.5, 98.0, 98.2, 98.7, 99.1, 99.4, 100.0, 100.0],
          95.0,
          85.0,
        ),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-client-satisfaction",
        currentLabel: "NPS 71",
        trendLabel: "+4 pts vs semestre anterior",
        status: "ready",
        snapshots: makeNpsSnapshots([67, 68, 69, 69, 70, 70, 71, 70, 70, 71, 71, 71]),
        blockers: [],
        warnings: [],
        complaintScenarioId: "resolved-history",
        complaintId: "recl-002",
      },
    ],
  },
  "action-sla-attention": {
    label: "Indicadores com desvio preventivo",
    description:
      "Recorte com SLA de acoes corretivas abaixo da meta e aumento da taxa de NC por area, ainda sem deriva critica irreversivel.",
    recommendedAction:
      "Recuperar o SLA de CAPA, reduzir a taxa de NC recorrente e consolidar o desvio antes da proxima analise critica ordinaria.",
    selectedIndicatorId: "indicator-capa-sla",
    indicators: [
      {
        indicatorId: "indicator-reissue-free",
        currentLabel: "99,0%",
        trendLabel: "+0,2 p.p. vs media anual",
        status: "ready",
        snapshots: makePercentSnapshots(
          [98.7, 98.9, 99.0, 99.0, 99.1, 99.2, 99.0, 98.9, 99.1, 99.0, 99.1, 99.0],
          98.0,
          97.0,
        ),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-nc-rate",
        currentLabel: "Equipamentos 3 | Pessoal 2",
        trendLabel: "+2 NC vs trimestre anterior",
        status: "attention",
        snapshots: makeTextSnapshots([
          { valueLabel: "Eq 1 | Pes 0", status: "ready" },
          { valueLabel: "Eq 1 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 3 | Pes 1", status: "attention" },
          { valueLabel: "Eq 3 | Pes 1", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
        ]),
        blockers: [],
        warnings: ["A taxa por area voltou a subir no mesmo periodo em que a NC-014 permaneceu aberta."],
        nonconformityScenarioId: "open-attention",
        nonconformityId: "nc-014",
      },
      {
        indicatorId: "indicator-os-cycle-time",
        currentLabel: "32 min",
        trendLabel: "Estavel dentro da meta",
        status: "ready",
        snapshots: makeUpperBoundMinuteSnapshots([33, 32, 33, 34, 33, 32, 32, 32, 31, 32, 32, 32], 35, 38),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-capa-sla",
        currentLabel: "87,5%",
        trendLabel: "-2,5 p.p. abaixo da meta",
        status: "attention",
        snapshots: makePercentSnapshots(
          [92.0, 91.5, 90.8, 90.0, 89.6, 89.2, 88.9, 88.4, 88.1, 87.9, 87.7, 87.5],
          90.0,
          80.0,
        ),
        blockers: [],
        warnings: [
          "A NC-014 ainda concentra follow-up pendente e puxa o SLA de CAPA para baixo da meta.",
          "A reclamacao aberta aumenta a pressao para fechamento formal dentro do prazo.",
        ],
        complaintScenarioId: "open-follow-up",
        complaintId: "recl-004",
        nonconformityScenarioId: "open-attention",
        nonconformityId: "nc-014",
      },
      {
        indicatorId: "indicator-capa-effectiveness",
        currentLabel: "96,0%",
        trendLabel: "1 reincidencia monitorada sem reabertura critica",
        status: "ready",
        snapshots: makePercentSnapshots(
          [95.5, 95.2, 95.0, 95.6, 96.0, 96.2, 96.1, 96.0, 96.1, 96.0, 96.0, 96.0],
          95.0,
          85.0,
        ),
        blockers: [],
        warnings: [],
      },
      {
        indicatorId: "indicator-client-satisfaction",
        currentLabel: "NPS 70",
        trendLabel: "Sem desvio material frente ao semestre anterior",
        status: "ready",
        snapshots: makeNpsSnapshots([69, 69, 70, 70, 70, 70, 70, 70, 71, 70, 70, 70]),
        blockers: [],
        warnings: [],
      },
    ],
  },
  "critical-drift": {
    label: "Indicadores em deriva critica",
    description:
      "Recorte com queda abaixo da meta em reemissao, SLA e eficacia CAPA, exigindo resposta extraordinaria da Qualidade.",
    recommendedAction:
      "Congelar o recorte afetado, registrar resposta extraordinaria e usar os indicadores como ancora para NC, reclamacao e risco correlatos.",
    selectedIndicatorId: "indicator-reissue-free",
    indicators: [
      {
        indicatorId: "indicator-reissue-free",
        currentLabel: "96,1%",
        trendLabel: "-1,9 p.p. abaixo da meta",
        status: "blocked",
        snapshots: makePercentSnapshots(
          [98.2, 98.0, 97.8, 97.5, 97.3, 97.0, 96.8, 96.6, 96.5, 96.3, 96.2, 96.1],
          98.0,
          97.0,
        ),
        blockers: ["O indice de reemissao ficou abaixo da meta e coincide com o caso critico em resposta formal."],
        warnings: ["A queda de desempenho reforca a necessidade de revisar o fluxo tecnico antes de nova liberacao."],
        complaintScenarioId: "critical-response",
        complaintId: "recl-007",
        nonconformityScenarioId: "critical-response",
        nonconformityId: "nc-015",
      },
      {
        indicatorId: "indicator-nc-rate",
        currentLabel: "Equipamentos 5 | Pessoal 3",
        trendLabel: "+3 NC vs trimestre anterior",
        status: "attention",
        snapshots: makeTextSnapshots([
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 2 | Pes 1", status: "ready" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 3 | Pes 2", status: "attention" },
          { valueLabel: "Eq 4 | Pes 2", status: "attention" },
          { valueLabel: "Eq 4 | Pes 2", status: "attention" },
          { valueLabel: "Eq 4 | Pes 3", status: "attention" },
          { valueLabel: "Eq 5 | Pes 3", status: "attention" },
          { valueLabel: "Eq 5 | Pes 3", status: "attention" },
          { valueLabel: "Eq 5 | Pes 3", status: "attention" },
          { valueLabel: "Eq 5 | Pes 3", status: "attention" },
        ]),
        blockers: [],
        warnings: ["A distribuicao por area indica concentracao anormal no mesmo recorte da NC critica."],
        nonconformityScenarioId: "critical-response",
        nonconformityId: "nc-015",
      },
      {
        indicatorId: "indicator-os-cycle-time",
        currentLabel: "38 min",
        trendLabel: "+5 min vs media anual",
        status: "attention",
        snapshots: makeUpperBoundMinuteSnapshots([34, 34, 35, 35, 36, 36, 37, 37, 38, 38, 38, 38], 35, 38),
        blockers: [],
        warnings: ["O tempo medio subiu junto da contencao do caso critico e reduz a folga operacional do time."],
      },
      {
        indicatorId: "indicator-capa-sla",
        currentLabel: "62,5%",
        trendLabel: "-27,5 p.p. abaixo da meta",
        status: "blocked",
        snapshots: makePercentSnapshots(
          [88.0, 86.5, 84.0, 81.2, 78.0, 75.0, 72.0, 69.0, 66.0, 64.0, 63.0, 62.5],
          90.0,
          80.0,
        ),
        blockers: ["A maioria das acoes corretivas do recorte critico ja estourou o prazo aprovado pela Qualidade."],
        warnings: ["Sem recuperacao imediata do SLA, o caso precisa entrar formalmente na pauta extraordinaria."],
        nonconformityScenarioId: "critical-response",
        nonconformityId: "nc-015",
      },
      {
        indicatorId: "indicator-capa-effectiveness",
        currentLabel: "62,0%",
        trendLabel: "2 reincidencias no trimestre",
        status: "blocked",
        snapshots: makePercentSnapshots(
          [95.0, 94.2, 92.0, 90.0, 88.0, 85.0, 81.0, 78.0, 74.0, 69.0, 65.0, 62.0],
          95.0,
          85.0,
        ),
        blockers: ["A eficacia despencou e aponta reincidencia material no mesmo recorte de resposta critica."],
        warnings: ["A queda de eficacia reforca a necessidade de revisar causa raiz, risco e treinamento associado."],
        nonconformityScenarioId: "critical-response",
        nonconformityId: "nc-015",
        riskRegisterScenarioId: "commercial-pressure",
        riskId: "risk-001",
      },
      {
        indicatorId: "indicator-client-satisfaction",
        currentLabel: "NPS 41",
        trendLabel: "-22 pts vs semestre anterior",
        status: "attention",
        snapshots: makeNpsSnapshots([68, 67, 66, 65, 63, 60, 58, 55, 52, 49, 45, 41]),
        blockers: [],
        warnings: ["A queda de satisfacao acompanha a reclamacao critica ainda sem desfecho conclusivo."],
        complaintScenarioId: "critical-response",
        complaintId: "recl-007",
      },
    ],
  },
};

const DEFAULT_SCENARIO: QualityIndicatorScenarioId = "action-sla-attention";

export function listQualityIndicatorScenarios(): QualityIndicatorRegistryScenario[] {
  return (Object.keys(SCENARIOS) as QualityIndicatorScenarioId[]).map((scenarioId) =>
    resolveQualityIndicatorScenario(scenarioId),
  );
}

export function resolveQualityIndicatorScenario(
  scenarioId?: string,
  indicatorId?: string,
): QualityIndicatorRegistryScenario {
  const definition = resolveDefinition(scenarioId);
  const indicators = definition.indicators.map(buildIndicatorCard);
  const selectedIndicator =
    indicators.find((item) => item.indicatorId === indicatorId) ??
    indicators.find((item) => item.indicatorId === definition.selectedIndicatorId) ??
    indicators[0];

  if (!selectedIndicator) {
    throw new Error("missing_quality_indicator_items");
  }

  const detail = buildIndicatorDetail(definition, selectedIndicator.indicatorId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition, detail),
    selectedIndicatorId: selectedIndicator.indicatorId,
    indicators,
    detail,
  };
}

export function buildQualityIndicatorCatalog(
  scenarioId?: string,
  indicatorId?: string,
): QualityIndicatorRegistryCatalog {
  const selectedScenario = resolveQualityIndicatorScenario(scenarioId, indicatorId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listQualityIndicatorScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildIndicatorCard(state: ScenarioIndicatorState): QualityIndicatorCard {
  const record = getIndicatorRecord(state.indicatorId);

  return {
    indicatorId: record.indicatorId,
    title: record.title,
    currentLabel: state.currentLabel,
    targetLabel: record.targetLabel,
    trendLabel: state.trendLabel,
    ownerLabel: record.ownerLabel,
    cadenceLabel: record.cadenceLabel,
    status: state.status,
  };
}

function buildIndicatorDetail(
  definition: QualityIndicatorScenarioDefinition,
  indicatorId: string,
): QualityIndicatorDetail {
  const record = getIndicatorRecord(indicatorId);
  const state = getIndicatorState(definition, indicatorId);

  return {
    indicatorId: record.indicatorId,
    title: record.title,
    status: state.status,
    noticeLabel:
      state.status === "ready"
        ? "Indicador dentro da meta e pronto para compor a analise critica ordinaria."
        : state.status === "attention"
          ? "Indicador abaixo da meta, mas ainda em janela de correcao preventiva."
          : "Indicador em deriva critica e exigindo resposta extraordinaria da Qualidade.",
    currentLabel: state.currentLabel,
    targetLabel: record.targetLabel,
    trendLabel: state.trendLabel,
    ownerLabel: record.ownerLabel,
    cadenceLabel: record.cadenceLabel,
    periodLabel: PERIOD_LABEL,
    measurementDefinitionLabel: record.measurementDefinitionLabel,
    evidenceLabel: record.evidenceLabel,
    managementReviewLabel: record.managementReviewLabel,
    snapshots: state.snapshots,
    relatedArtifacts: record.relatedArtifacts,
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      complaintScenarioId: state.complaintScenarioId,
      complaintId: state.complaintId,
      nonconformityScenarioId: state.nonconformityScenarioId,
      nonconformityId: state.nonconformityId,
      riskRegisterScenarioId: state.riskRegisterScenarioId,
      riskId: state.riskId,
    },
  };
}

function buildSummary(
  definition: QualityIndicatorScenarioDefinition,
  detail: QualityIndicatorDetail,
): QualityIndicatorRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Indicadores da qualidade estaveis e prontos para analise critica"
        : detail.status === "attention"
          ? "Painel aponta desvio preventivo em indicadores da qualidade"
          : "Painel mostra deriva critica e exige resposta extraordinaria",
    monthlyWindowLabel: PERIOD_LABEL,
    indicatorCount: definition.indicators.length,
    attentionCount: definition.indicators.filter((item) => item.status === "attention").length,
    blockedCount: definition.indicators.filter((item) => item.status === "blocked").length,
    recommendedAction: definition.recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getIndicatorRecord(indicatorId: string): IndicatorRecord {
  const record = INDICATORS[indicatorId];
  if (!record) {
    throw new Error(`missing_quality_indicator_record:${indicatorId}`);
  }

  return record;
}

function getIndicatorState(
  definition: QualityIndicatorScenarioDefinition,
  indicatorId: string,
): ScenarioIndicatorState {
  const state = definition.indicators.find((item) => item.indicatorId === indicatorId);
  if (!state) {
    throw new Error(`missing_quality_indicator_state:${indicatorId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): QualityIndicatorScenarioId {
  return isQualityIndicatorScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): QualityIndicatorScenarioDefinition {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  if (!definition) {
    throw new Error(`missing_quality_indicator_scenario:${resolvedScenarioId}`);
  }

  return definition;
}

function isQualityIndicatorScenarioId(
  value: string | undefined,
): value is QualityIndicatorScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function makePercentSnapshots(
  values: number[],
  readyFloor: number,
  attentionFloor: number,
): QualityIndicatorSnapshot[] {
  return MONTHS.map((monthLabel, index) => {
    const value = values[index];
    if (typeof value !== "number") {
      throw new Error(`missing_quality_indicator_percent_snapshot:${monthLabel}`);
    }

    const status =
      value >= readyFloor ? "ready" : value >= attentionFloor ? "attention" : "blocked";

    return {
      monthLabel,
      valueLabel: formatPercent(value),
      status,
    };
  });
}

function makeUpperBoundMinuteSnapshots(
  values: number[],
  readyCeiling: number,
  attentionCeiling: number,
): QualityIndicatorSnapshot[] {
  return MONTHS.map((monthLabel, index) => {
    const value = values[index];
    if (typeof value !== "number") {
      throw new Error(`missing_quality_indicator_minute_snapshot:${monthLabel}`);
    }

    const status =
      value <= readyCeiling ? "ready" : value <= attentionCeiling ? "attention" : "blocked";

    return {
      monthLabel,
      valueLabel: `${value} min`,
      status,
    };
  });
}

function makeNpsSnapshots(values: number[]): QualityIndicatorSnapshot[] {
  return MONTHS.map((monthLabel, index) => {
    const value = values[index];
    if (typeof value !== "number") {
      throw new Error(`missing_quality_indicator_nps_snapshot:${monthLabel}`);
    }

    const status = value >= 70 ? "ready" : value >= 55 ? "attention" : "blocked";

    return {
      monthLabel,
      valueLabel: `NPS ${value}`,
      status,
    };
  });
}

function makeTextSnapshots(
  values: Array<{ valueLabel: string; status: RegistryOperationalStatus }>,
): QualityIndicatorSnapshot[] {
  return MONTHS.map((monthLabel, index) => ({
    monthLabel,
    valueLabel: values[index]?.valueLabel ?? "Sem dado",
    status: values[index]?.status ?? "blocked",
  }));
}

function formatPercent(value: number): string {
  return `${value.toFixed(1).replace(".", ",")}%`;
}
