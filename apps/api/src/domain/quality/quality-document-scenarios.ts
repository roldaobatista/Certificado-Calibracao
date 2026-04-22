import type {
  QualityDocumentDetail,
  QualityDocumentListItem,
  QualityDocumentRegistryCatalog,
  QualityDocumentRegistryScenario,
  QualityDocumentRegistryScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type DocumentRecord = {
  documentId: string;
  code: string;
  title: string;
  categoryLabel: string;
  revisionLabel: string;
  effectiveSinceLabel: string;
  effectiveUntilLabel?: string;
  lifecycleLabel: string;
  ownerLabel: string;
  approvalLabel: string;
  scopeLabel: string;
  distributionLabel: string;
  revisionPolicyLabel: string;
  evidenceLabel: string;
  relatedArtifacts: string[];
  organizationSettingsScenarioId?: QualityDocumentDetail["links"]["organizationSettingsScenarioId"];
  procedureScenarioId?: QualityDocumentDetail["links"]["procedureScenarioId"];
  procedureId?: QualityDocumentDetail["links"]["procedureId"];
  riskRegisterScenarioId?: QualityDocumentDetail["links"]["riskRegisterScenarioId"];
  riskId?: QualityDocumentDetail["links"]["riskId"];
};

type ScenarioDocumentState = {
  documentId: string;
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

type QualityDocumentScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedDocumentId: string;
  counts: {
    activeCount: number;
    attentionCount: number;
    obsoleteCount: number;
  };
  items: ScenarioDocumentState[];
};

const DOCUMENTS: Record<string, DocumentRecord> = {
  "document-mq001-r03": {
    documentId: "document-mq001-r03",
    code: "MQ-001",
    title: "Manual da Qualidade",
    categoryLabel: "Manual",
    revisionLabel: "03",
    effectiveSinceLabel: "01/2026",
    lifecycleLabel: "Vigente",
    ownerLabel: "Ana Costa",
    approvalLabel: "Aprovado pela direcao em 01/2026",
    scopeLabel:
      "Consolida politica, escopo, responsabilidades, estrutura documental e governanca do SGQ.",
    distributionLabel:
      "Disponivel ao back-office, revisores da Qualidade e dossie regulatorio interno.",
    revisionPolicyLabel:
      "Revisao anual ou extraordinaria quando houver mudanca relevante de processo, escopo ou governanca.",
    evidenceLabel:
      "MQ-001 rev.03, historico de aprovacao e release-norm do ciclo 2026.01 arquivados no dossie da Qualidade.",
    relatedArtifacts: [
      "PG-001 · Controle de documentos",
      "PG-002 · Controle de registros",
      "Release-norm 2026.01",
    ],
    organizationSettingsScenarioId: "operational-ready",
  },
  "document-pg003-r01": {
    documentId: "document-pg003-r01",
    code: "PG-003",
    title: "Imparcialidade",
    categoryLabel: "Gestao",
    revisionLabel: "01",
    effectiveSinceLabel: "01/2024",
    lifecycleLabel: "Vigente",
    ownerLabel: "Ana Costa",
    approvalLabel: "Aprovado pela direcao em 01/2024",
    scopeLabel:
      "Define coleta anual de declaracoes de conflito, analise de atribuicoes e governanca de riscos a imparcialidade.",
    distributionLabel:
      "Disponivel ao gestor da Qualidade, direcao e responsaveis por aprovacao sensivel.",
    revisionPolicyLabel:
      "Revisao anual junto da rodada de declaracoes ou sempre que houver ajuste na matriz de riscos.",
    evidenceLabel:
      "PG-003 rev.01, declaracoes 2026 e matriz de riscos associada arquivadas para auditoria.",
    relatedArtifacts: [
      "Declaracoes anuais 2026",
      "Matriz de riscos a imparcialidade",
      "Ata da revisao de atribuicoes sensiveis",
    ],
    organizationSettingsScenarioId: "renewal-attention",
    riskRegisterScenarioId: "annual-declarations",
    riskId: "risk-003",
  },
  "document-pg005-r02": {
    documentId: "document-pg005-r02",
    code: "PG-005",
    title: "Trabalho nao conforme",
    categoryLabel: "Gestao",
    revisionLabel: "02",
    effectiveSinceLabel: "09/2025",
    lifecycleLabel: "Vigente com revisao preventiva",
    ownerLabel: "Ana Costa",
    approvalLabel: "Aprovado pela direcao em 09/2025",
    scopeLabel:
      "Define congelamento, contencao, tratativa e desbloqueio de atividades afetadas por trabalho nao conforme.",
    distributionLabel:
      "Disponivel a Qualidade, revisores tecnicos e lideres operacionais envolvidos em contencao.",
    revisionPolicyLabel:
      "Revisao semestral ou imediata quando incidentes criticos indicarem ajuste do fluxo de contencao.",
    evidenceLabel:
      "PG-005 rev.02, registros de revisao preventiva e referencias a NC-015 arquivados no dossie.",
    relatedArtifacts: [
      "NC-015 · Caso critico em tratamento",
      "Checklist de contencao",
      "Minuta de revisao preventiva 2026/Q2",
    ],
    organizationSettingsScenarioId: "renewal-attention",
  },
  "document-pt005-r04": {
    documentId: "document-pt005-r04",
    code: "PT-005",
    title: "Calibracao IPNA campo classe III",
    categoryLabel: "Tecnico",
    revisionLabel: "04",
    effectiveSinceLabel: "03/2024",
    lifecycleLabel: "Vigente",
    ownerLabel: "Carlos",
    approvalLabel: "Aprovado por Ana Costa em 03/2024",
    scopeLabel:
      "Procedimento tecnico para balancas IPNA classe III em campo, com 5 pontos de curva e criterios de registro bruto.",
    distributionLabel:
      "Disponivel a tecnicos de campo, revisores e back-office tecnico no recorte da OS correspondente.",
    revisionPolicyLabel:
      "Revisao quando houver ajuste de metodo, curva, padrao aplicavel ou feedback de NC/documento associado.",
    evidenceLabel:
      "PT-005 rev.04, FR-021 e balanco de incerteza correspondente arquivados no cadastro tecnico.",
    relatedArtifacts: [
      "FR-021 · Registro bruto da curva",
      "BAL-UNC-IPNA-III · Balanco de incerteza",
      "IT-005-1 · Checklist de campo",
    ],
    procedureScenarioId: "operational-ready",
    procedureId: "procedure-pt005-r04",
  },
  "document-fr001-r03": {
    documentId: "document-fr001-r03",
    code: "FR-001",
    title: "Registro de calibracao",
    categoryLabel: "Formulario",
    revisionLabel: "03",
    effectiveSinceLabel: "03/2024",
    lifecycleLabel: "Vigente",
    ownerLabel: "Maria Souza",
    approvalLabel: "Aprovado por Ana Costa em 03/2024",
    scopeLabel:
      "Formulario controlado para registrar coleta de dados, observacoes, assinaturas e rastreabilidade da execucao.",
    distributionLabel:
      "Disponivel a tecnicos, revisores tecnicos e dossie de validacao conforme o recorte da OS.",
    revisionPolicyLabel:
      "Revisao sempre que PT/IT relacionados mudarem campos obrigatorios ou regras de preenchimento.",
    evidenceLabel:
      "FR-001 rev.03, historico de emissoes e amostras de uso aprovadas arquivados no dossie documental.",
    relatedArtifacts: [
      "PT-005 rev.04",
      "Checklist de revisao tecnica",
      "Historico de amostras aprovadas",
    ],
    procedureScenarioId: "operational-ready",
    procedureId: "procedure-pt005-r04",
  },
  "document-pg005-r01": {
    documentId: "document-pg005-r01",
    code: "PG-005",
    title: "Trabalho nao conforme",
    categoryLabel: "Gestao",
    revisionLabel: "01",
    effectiveSinceLabel: "01/2024",
    effectiveUntilLabel: "09/2025",
    lifecycleLabel: "Obsoleto",
    ownerLabel: "Ana Costa",
    approvalLabel: "Substituido pela rev.02 em 09/2025",
    scopeLabel:
      "Revisao mantida apenas para rastreabilidade historica; nao sustenta casos novos nem resposta critica atual.",
    distributionLabel:
      "Consulta restrita a auditoria e dossie historico; vedado uso operacional em novos casos.",
    revisionPolicyLabel:
      "Mantido apenas para historico; qualquer uso novo exige migracao imediata para a revisao vigente.",
    evidenceLabel:
      "Ata de substituicao da rev.02 e historico de vigencia preservados no acervo documental do SGQ.",
    relatedArtifacts: [
      "Ata de substituicao da rev.02",
      "Historico de vigencia 2024-2025",
      "Referencia cruzada para PG-005 rev.02",
    ],
    organizationSettingsScenarioId: "profile-change-blocked",
  },
};

const SCENARIOS: Record<
  QualityDocumentRegistryScenarioId,
  QualityDocumentScenarioDefinition
> = {
  "operational-ready": {
    label: "Documentos vigentes e rastreaveis",
    description:
      "Recorte com documentos vigentes, distribuicao controlada e apenas consulta historica para revisoes ja substituidas.",
    recommendedAction:
      "Manter a carteira vigente arquivada, revisar apenas na cadencia prevista e usar o historico obsoleto so para auditoria.",
    selectedDocumentId: "document-mq001-r03",
    counts: {
      activeCount: 24,
      attentionCount: 0,
      obsoleteCount: 4,
    },
    items: [
      { documentId: "document-mq001-r03", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-pg003-r01", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-pg005-r02", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-fr001-r03", status: "ready", blockers: [], warnings: [] },
      {
        documentId: "document-pg005-r01",
        status: "blocked",
        blockers: ["Revisao obsoleta mantida apenas para historico auditavel."],
        warnings: [],
      },
    ],
  },
  "revision-attention": {
    label: "Documento com revisao preventiva em andamento",
    description:
      "Recorte com documento vigente sob revisao preventiva, sem perda de rastreabilidade da versao atual nem do historico obsoleto.",
    recommendedAction:
      "Concluir a revisao preventiva do documento selecionado antes da proxima rodada sensivel de Qualidade.",
    selectedDocumentId: "document-pg005-r02",
    counts: {
      activeCount: 24,
      attentionCount: 1,
      obsoleteCount: 4,
    },
    items: [
      { documentId: "document-mq001-r03", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-pg003-r01", status: "ready", blockers: [], warnings: [] },
      {
        documentId: "document-pg005-r02",
        status: "attention",
        blockers: [],
        warnings: [
          "Revisao preventiva da Qualidade precisa fechar antes do proximo ciclo critico.",
        ],
      },
      { documentId: "document-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-fr001-r03", status: "ready", blockers: [], warnings: [] },
      {
        documentId: "document-pg005-r01",
        status: "blocked",
        blockers: ["Revisao obsoleta mantida apenas para historico auditavel."],
        warnings: [],
      },
    ],
  },
  "obsolete-blocked": {
    label: "Revisao obsoleta bloqueada para uso",
    description:
      "Recorte com uma revisao obsoleta ainda consultavel para auditoria, mas explicitamente bloqueada para novos casos operacionais.",
    recommendedAction:
      "Migrar a consulta operacional para a revisao vigente correspondente e manter a obsoleta apenas como evidencia historica.",
    selectedDocumentId: "document-pg005-r01",
    counts: {
      activeCount: 23,
      attentionCount: 1,
      obsoleteCount: 5,
    },
    items: [
      { documentId: "document-mq001-r03", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-pg003-r01", status: "ready", blockers: [], warnings: [] },
      {
        documentId: "document-pg005-r02",
        status: "attention",
        blockers: [],
        warnings: ["A revisao vigente ainda passa por fechamento preventivo da Qualidade."],
      },
      { documentId: "document-pt005-r04", status: "ready", blockers: [], warnings: [] },
      { documentId: "document-fr001-r03", status: "ready", blockers: [], warnings: [] },
      {
        documentId: "document-pg005-r01",
        status: "blocked",
        blockers: ["Revisao obsoleta nao pode sustentar tratativas novas nem resposta critica atual."],
        warnings: ["Manter apenas para auditoria e rastreabilidade historica."],
      },
    ],
  },
};

const DEFAULT_SCENARIO: QualityDocumentRegistryScenarioId = "revision-attention";

export function listQualityDocumentScenarios(): QualityDocumentRegistryScenario[] {
  return (
    Object.keys(SCENARIOS) as QualityDocumentRegistryScenarioId[]
  ).map((scenarioId) => resolveQualityDocumentScenario(scenarioId));
}

export function resolveQualityDocumentScenario(
  scenarioId?: string,
  documentId?: string,
): QualityDocumentRegistryScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildDocumentListItem);
  const selectedDocument =
    items.find((item) => item.documentId === documentId) ??
    items.find((item) => item.documentId === definition.selectedDocumentId) ??
    items[0];

  if (!selectedDocument) {
    throw new Error("missing_quality_document_items");
  }

  const detail = buildDocumentDetail(definition, selectedDocument.documentId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition, detail),
    selectedDocumentId: selectedDocument.documentId,
    items,
    detail,
  };
}

export function buildQualityDocumentCatalog(
  scenarioId?: string,
  documentId?: string,
): QualityDocumentRegistryCatalog {
  const selectedScenario = resolveQualityDocumentScenario(scenarioId, documentId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listQualityDocumentScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildDocumentListItem(
  state: ScenarioDocumentState,
): QualityDocumentListItem {
  const record = getDocumentRecord(state.documentId);

  return {
    documentId: record.documentId,
    code: record.code,
    title: record.title,
    categoryLabel: record.categoryLabel,
    revisionLabel: record.revisionLabel,
    effectiveSinceLabel: record.effectiveSinceLabel,
    effectiveUntilLabel: record.effectiveUntilLabel,
    lifecycleLabel: record.lifecycleLabel,
    ownerLabel: record.ownerLabel,
    status: state.status,
  };
}

function buildDocumentDetail(
  definition: QualityDocumentScenarioDefinition,
  documentId: string,
): QualityDocumentDetail {
  const record = getDocumentRecord(documentId);
  const state = getDocumentState(definition, documentId);

  return {
    documentId: record.documentId,
    title: `${record.code} rev.${record.revisionLabel} · ${record.title}`,
    status: state.status,
    noticeLabel:
      state.status === "ready"
        ? "Documento vigente, distribuido e pronto para consulta auditavel."
        : state.status === "attention"
          ? "Documento vigente sob revisao preventiva da Qualidade."
          : "Revisao obsoleta bloqueada para uso operacional atual.",
    categoryLabel: record.categoryLabel,
    ownerLabel: record.ownerLabel,
    approvalLabel: record.approvalLabel,
    scopeLabel: record.scopeLabel,
    distributionLabel: record.distributionLabel,
    revisionPolicyLabel: record.revisionPolicyLabel,
    evidenceLabel: record.evidenceLabel,
    relatedArtifacts: record.relatedArtifacts,
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      organizationSettingsScenarioId: record.organizationSettingsScenarioId,
      procedureScenarioId: record.procedureScenarioId,
      procedureId: record.procedureId,
      riskRegisterScenarioId: record.riskRegisterScenarioId,
      riskId: record.riskId,
    },
  };
}

function buildSummary(
  definition: QualityDocumentScenarioDefinition,
  detail: QualityDocumentDetail,
): QualityDocumentRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Documentos vigentes e rastreaveis prontos para auditoria"
        : detail.status === "attention"
          ? "Carteira documental exige revisao preventiva da Qualidade"
          : "Revisao obsoleta bloqueia o uso documental no recorte atual",
    activeCount: definition.counts.activeCount,
    attentionCount: definition.counts.attentionCount,
    obsoleteCount: definition.counts.obsoleteCount,
    recommendedAction: definition.recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getDocumentRecord(documentId: string): DocumentRecord {
  const record = DOCUMENTS[documentId];
  if (!record) {
    throw new Error(`missing_quality_document_record:${documentId}`);
  }

  return record;
}

function getDocumentState(
  definition: QualityDocumentScenarioDefinition,
  documentId: string,
): ScenarioDocumentState {
  const state = definition.items.find((item) => item.documentId === documentId);
  if (!state) {
    throw new Error(`missing_quality_document_state:${documentId}`);
  }

  return state;
}

function resolveScenarioId(
  scenarioId?: string,
): QualityDocumentRegistryScenarioId {
  return isQualityDocumentScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(
  scenarioId?: string,
): QualityDocumentScenarioDefinition {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  if (!definition) {
    throw new Error(`missing_quality_document_scenario:${resolvedScenarioId}`);
  }

  return definition;
}

function isQualityDocumentScenarioId(
  value: string | undefined,
): value is QualityDocumentRegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
