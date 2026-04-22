import type {
  ConflictDeclarationItem,
  RiskAction,
  RiskDetail,
  RiskMatrixItem,
  RiskRegisterCatalog,
  RiskRegisterScenario,
  RiskRegisterScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type DeclarationRecord = {
  declarationId: string;
  actorName: string;
};

type ScenarioDeclarationState = {
  declarationId: string;
  dateLabel: string;
  summary: string;
  status: RegistryOperationalStatus;
  statusLabel: string;
  documentLabel: string;
};

type RiskRecord = {
  riskId: string;
  title: string;
  categoryLabel: string;
  probabilityLabel: string;
  impactLabel: string;
  ownerLabel: string;
  description: string;
  mitigationPlanLabel: string;
  evidenceLabel: string;
};

type ScenarioRiskState = {
  riskId: string;
  status: RegistryOperationalStatus;
  statusLabel: string;
  lastReviewedAtLabel: string;
  reviewCadenceLabel: string;
  linkedDeclarationLabel: string;
  managementReviewLabel: string;
  actions: RiskAction[];
  blockers: string[];
  warnings: string[];
  organizationSettingsScenarioId?: RiskDetail["links"]["organizationSettingsScenarioId"];
  complaintScenarioId?: RiskDetail["links"]["complaintScenarioId"];
  complaintId?: RiskDetail["links"]["complaintId"];
  nonconformityScenarioId?: RiskDetail["links"]["nonconformityScenarioId"];
  nonconformityId?: RiskDetail["links"]["nonconformityId"];
};

type RiskScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedRiskId: string;
  declarations: ScenarioDeclarationState[];
  risks: ScenarioRiskState[];
};

const DECLARATIONS: Record<string, DeclarationRecord> = {
  "decl-ana-2026": {
    declarationId: "decl-ana-2026",
    actorName: "Ana Costa",
  },
  "decl-maria-2026": {
    declarationId: "decl-maria-2026",
    actorName: "Maria Souza",
  },
  "decl-joao-2026": {
    declarationId: "decl-joao-2026",
    actorName: "Joao Silva",
  },
};

const RISKS: Record<string, RiskRecord> = {
  "risk-001": {
    riskId: "risk-001",
    title: "Pressao comercial para acelerar reemissao antes da conclusao da NC",
    categoryLabel: "Imparcialidade",
    probabilityLabel: "Media",
    impactLabel: "Alta",
    ownerLabel: "Direcao",
    description:
      "Um pedido de urgencia comercial tenta antecipar a reemissao do certificado enquanto a NC critica e a trilha append-only ainda exigem conclusao formal da Qualidade.",
    mitigationPlanLabel:
      "Exigir decisao colegiada registrada, manter segregacao de papeis e bloquear qualquer liberacao enquanto NC, trilha e resposta formal ao cliente permanecerem pendentes.",
    evidenceLabel:
      "E-mail do comercial, registro de escalacao, referencia a NC-015, reclamação critica e trilha do caso.",
  },
  "risk-002": {
    riskId: "risk-002",
    title: "Padrao reserva emprestado de fornecedor",
    categoryLabel: "Operacao",
    probabilityLabel: "Baixa",
    impactLabel: "Alta",
    ownerLabel: "Carlos",
    description:
      "O laboratorio recorre a um padrao reserva emprestado por curto periodo. O risco permanece aceitavel apenas com termo especifico, rastreabilidade vigente e uso estritamente controlado.",
    mitigationPlanLabel:
      "Manter termo especifico atualizado, validar certificado vigente do padrao e limitar o uso ao periodo aprovado pela Qualidade.",
    evidenceLabel:
      "Termo de uso assinado, certificado do padrao reserva e log de utilizacao arquivado no dossie do equipamento.",
  },
  "risk-003": {
    riskId: "risk-003",
    title: "Rodada anual de declaracoes de conflito incompleta",
    categoryLabel: "Imparcialidade",
    probabilityLabel: "Media",
    impactLabel: "Media",
    ownerLabel: "Ana Costa",
    description:
      "Nem todos os envolvidos devolveram a rodada anual de declaracoes de conflito. Enquanto a coleta nao fecha, atribuicoes sensiveis exigem revisao adicional pela Qualidade.",
    mitigationPlanLabel:
      "Solicitar nova rodada, cobrar assinatura pendente e restringir aprovacoes sensiveis ate concluir a pasta anual de declaracoes.",
    evidenceLabel:
      "Controle de adesao da rodada 2026, historico de notificacoes e pasta das declaracoes assinadas.",
  },
};

const SCENARIOS: Record<RiskRegisterScenarioId, RiskScenarioDefinition> = {
  "annual-declarations": {
    label: "Rodada anual de declaracoes em acompanhamento",
    description:
      "Recorte com conflito declarado, uma assinatura anual ainda pendente e matriz de riscos mantida em monitoramento pela Qualidade.",
    recommendedAction:
      "Concluir a rodada anual, revisar atribuicoes para quem declarou conflito e manter a matriz pronta para a proxima analise critica ordinaria.",
    selectedRiskId: "risk-003",
    declarations: [
      {
        declarationId: "decl-ana-2026",
        dateLabel: "12/01/2026",
        summary: "Sem conflito declarado.",
        status: "ready",
        statusLabel: "Vigente",
        documentLabel: "Declaracao 2026 assinada [PDF]",
      },
      {
        declarationId: "decl-maria-2026",
        dateLabel: "12/01/2026",
        summary: "Conflito relatado: cliente ABC.",
        status: "attention",
        statusLabel: "Conflito declarado",
        documentLabel: "Declaracao 2026 com ressalva [PDF]",
      },
      {
        declarationId: "decl-joao-2026",
        dateLabel: "Sem retorno ate 20/04/2026",
        summary: "Nova declaracao anual ainda nao arquivada.",
        status: "blocked",
        statusLabel: "Nova rodada pendente",
        documentLabel: "Solicitacao reenviada em 20/04/2026",
      },
    ],
    risks: [
      {
        riskId: "risk-001",
        status: "attention",
        statusLabel: "Monitorado",
        lastReviewedAtLabel: "18/04/2026",
        reviewCadenceLabel: "Semanal",
        linkedDeclarationLabel:
          "Maria Souza declarou conflito com cliente ABC; atribuicoes semelhantes exigem dupla revisao pela Qualidade.",
        managementReviewLabel:
          "Risco apto a entrar na pauta ordinaria da analise critica sem necessidade de reuniao extraordinaria.",
        actions: [
          {
            key: "register-monitoring",
            label: "Registrar monitoramento",
            status: "complete",
            detail: "Risco mantido no registro com responsavel e frequencia definidos.",
          },
          {
            key: "review-assignments",
            label: "Revisar atribuicoes relacionadas",
            status: "pending",
            detail: "Revisar se atribuicoes sensiveis precisam de segregacao adicional.",
          },
          {
            key: "export-review",
            label: "Exportar para analise critica",
            status: "pending",
            detail: "Levar o consolidado para a pauta ordinaria do trimestre.",
          },
        ],
        blockers: [],
        warnings: ["Conflito declarado segue exigindo revisao de atribuicoes antes do proximo ciclo."],
        organizationSettingsScenarioId: "renewal-attention",
      },
      {
        riskId: "risk-002",
        status: "ready",
        statusLabel: "Mitigado",
        lastReviewedAtLabel: "16/04/2026",
        reviewCadenceLabel: "Mensal",
        linkedDeclarationLabel:
          "Sem conflito pessoal declarado; a mitigacao depende de termo formal e rastreabilidade do padrao reserva.",
        managementReviewLabel: "Leitura pronta para compor o consolidado ordinario da direcao.",
        actions: [
          {
            key: "renew-term",
            label: "Renovar termo especifico",
            status: "complete",
            detail: "Termo atualizado e anexado ao dossie do padrao reserva.",
          },
          {
            key: "review-certificate",
            label: "Revalidar certificado do padrao",
            status: "complete",
            detail: "Certificado vigente conferido na ultima revisao mensal.",
          },
        ],
        blockers: [],
        warnings: [],
        organizationSettingsScenarioId: "renewal-attention",
      },
      {
        riskId: "risk-003",
        status: "attention",
        statusLabel: "Rodada pendente",
        lastReviewedAtLabel: "20/04/2026",
        reviewCadenceLabel: "Diario ate concluir",
        linkedDeclarationLabel: "Joao Silva segue sem declaracao 2026 arquivada no dossie anual.",
        managementReviewLabel:
          "Se a rodada nao fechar no prazo interno, a pendencia deve entrar explicitamente na proxima analise critica.",
        actions: [
          {
            key: "request-round",
            label: "Solicitar nova rodada de declaracoes",
            status: "complete",
            detail: "Lembrete disparado aos envolvidos em 20/04/2026.",
          },
          {
            key: "collect-signature",
            label: "Cobrar assinatura pendente",
            status: "pending",
            detail: "Aguardando retorno e arquivamento da declaracao 2026 de Joao Silva.",
          },
          {
            key: "restrict-sensitive-approvals",
            label: "Restringir aprovacoes sensiveis",
            status: "pending",
            detail: "Manter dupla conferencia nas decisoes sensiveis enquanto a rodada nao fecha.",
          },
        ],
        blockers: ["Joao Silva ainda nao reenviou a declaracao 2026 assinada para decisoes sensiveis."],
        warnings: ["Uma declaracao com conflito relatado continua exigindo revisao de atribuicoes."],
        organizationSettingsScenarioId: "renewal-attention",
      },
    ],
  },
  "commercial-pressure": {
    label: "Risco critico de pressao comercial escalado",
    description:
      "Recorte com risco critico de imparcialidade ja registrado, relacionamento com NC/reclamacao em aberto e decisao colegiada ainda pendente.",
    recommendedAction:
      "Manter fail-closed, registrar a decisao da direcao e exportar o caso para analise critica extraordinaria antes de qualquer liberacao operacional.",
    selectedRiskId: "risk-001",
    declarations: [
      {
        declarationId: "decl-ana-2026",
        dateLabel: "12/01/2026",
        summary: "Sem conflito declarado.",
        status: "ready",
        statusLabel: "Vigente",
        documentLabel: "Declaracao 2026 assinada [PDF]",
      },
      {
        declarationId: "decl-maria-2026",
        dateLabel: "12/01/2026",
        summary: "Conflito relatado: cliente ABC.",
        status: "attention",
        statusLabel: "Conflito declarado",
        documentLabel: "Declaracao 2026 com ressalva [PDF]",
      },
      {
        declarationId: "decl-joao-2026",
        dateLabel: "12/01/2026",
        summary: "Sem conflito declarado.",
        status: "ready",
        statusLabel: "Vigente",
        documentLabel: "Declaracao 2026 assinada [PDF]",
      },
    ],
    risks: [
      {
        riskId: "risk-001",
        status: "blocked",
        statusLabel: "Escalado",
        lastReviewedAtLabel: "21/04/2026",
        reviewCadenceLabel: "Diario enquanto o caso estiver aberto",
        linkedDeclarationLabel:
          "A segregacao de papeis substitui qualquer aprovacao individual enquanto a pressao comercial permanecer ativa.",
        managementReviewLabel:
          "Exportacao extraordinaria pendente para a reuniao critica da direcao, com NC e reclamacao anexadas.",
        actions: [
          {
            key: "register-critical-risk",
            label: "Registrar risco critico",
            status: "complete",
            detail: "Risco classificado como alto impacto e anexado ao dossie da Qualidade.",
          },
          {
            key: "escalate-direction",
            label: "Escalonar para a direcao",
            status: "complete",
            detail: "Escalonamento aberto com trilha e anexos do caso critico.",
          },
          {
            key: "record-collegiate-decision",
            label: "Registrar decisao colegiada",
            status: "pending",
            detail: "A direcao ainda nao registrou a deliberacao formal sobre o caso.",
          },
          {
            key: "export-extraordinary-review",
            label: "Exportar para analise critica extraordinaria",
            status: "pending",
            detail: "A pauta extraordinaria ainda nao foi consolidada a partir do sistema.",
          },
          {
            key: "release-reissue",
            label: "Liberar reemissao",
            status: "blocked",
            detail: "A liberacao permanece bloqueada ate decisao colegiada, NC e trilha saneadas.",
          },
        ],
        blockers: [
          "A direcao ainda nao registrou decisao colegiada sobre a pressao comercial.",
          "NC-015 e a reclamacao critica permanecem abertas no mesmo recorte.",
        ],
        warnings: ["Qualquer liberacao sem trilha integra e dupla aprovacao viola o fail-closed."],
        organizationSettingsScenarioId: "profile-change-blocked",
        complaintScenarioId: "critical-response",
        complaintId: "recl-007",
        nonconformityScenarioId: "critical-response",
        nonconformityId: "nc-015",
      },
      {
        riskId: "risk-002",
        status: "attention",
        statusLabel: "Monitorado",
        lastReviewedAtLabel: "18/04/2026",
        reviewCadenceLabel: "Mensal",
        linkedDeclarationLabel:
          "Sem conflito pessoal declarado; a mitigacao continua dependente de rastreabilidade documental.",
        managementReviewLabel: "Manter no consolidado ordinario enquanto o caso critico nao contamina este risco.",
        actions: [
          {
            key: "review-term",
            label: "Revalidar termo e certificado",
            status: "complete",
            detail: "Termo e certificado conferidos na ultima revisao.",
          },
        ],
        blockers: [],
        warnings: [],
        organizationSettingsScenarioId: "renewal-attention",
      },
    ],
  },
  "stable-monitoring": {
    label: "Monitoramento estavel e rastreavel",
    description:
      "Recorte com declaracoes anuais arquivadas, conflitos conhecidos ja tratados e matriz de riscos mantida apenas para acompanhamento rotineiro.",
    recommendedAction:
      "Manter a revisao mensal da matriz, arquivar evidencias e reutilizar o consolidado na analise critica ordinaria.",
    selectedRiskId: "risk-002",
    declarations: [
      {
        declarationId: "decl-ana-2026",
        dateLabel: "12/01/2026",
        summary: "Sem conflito declarado.",
        status: "ready",
        statusLabel: "Vigente",
        documentLabel: "Declaracao 2026 assinada [PDF]",
      },
      {
        declarationId: "decl-maria-2026",
        dateLabel: "12/01/2026",
        summary: "Conflito relatado e tratado com reatribuicao preventiva.",
        status: "ready",
        statusLabel: "Tratado",
        documentLabel: "Declaracao 2026 com ressalva [PDF]",
      },
      {
        declarationId: "decl-joao-2026",
        dateLabel: "12/01/2026",
        summary: "Sem conflito declarado.",
        status: "ready",
        statusLabel: "Vigente",
        documentLabel: "Declaracao 2026 assinada [PDF]",
      },
    ],
    risks: [
      {
        riskId: "risk-002",
        status: "ready",
        statusLabel: "Mitigado",
        lastReviewedAtLabel: "18/04/2026",
        reviewCadenceLabel: "Mensal",
        linkedDeclarationLabel:
          "Sem conflito pessoal declarado; o risco fica restrito a termo especifico e rastreabilidade do padrao.",
        managementReviewLabel: "Leitura pronta para a pauta ordinaria da direcao.",
        actions: [
          {
            key: "renew-term",
            label: "Renovar termo especifico",
            status: "complete",
            detail: "Termo atualizado e revisado no ultimo ciclo mensal.",
          },
          {
            key: "archive-evidence",
            label: "Arquivar evidencias",
            status: "complete",
            detail: "Certificado e log de uso arquivados no dossie do risco.",
          },
        ],
        blockers: [],
        warnings: [],
        organizationSettingsScenarioId: "operational-ready",
      },
      {
        riskId: "risk-003",
        status: "ready",
        statusLabel: "Rodada concluida",
        lastReviewedAtLabel: "12/01/2026",
        reviewCadenceLabel: "Anual",
        linkedDeclarationLabel: "Todas as declaracoes 2026 foram arquivadas e revisadas pela Qualidade.",
        managementReviewLabel: "Rodada encerrada; apenas consolidar o indicador de aderencia na pauta ordinaria.",
        actions: [
          {
            key: "collect-round",
            label: "Concluir rodada anual",
            status: "complete",
            detail: "Todas as declaracoes 2026 foram recebidas e arquivadas.",
          },
          {
            key: "review-conflicts",
            label: "Revisar conflitos declarados",
            status: "complete",
            detail: "Conflitos tratados com reatribuicao preventiva e registro em ata.",
          },
        ],
        blockers: [],
        warnings: [],
        organizationSettingsScenarioId: "operational-ready",
      },
    ],
  },
};

const DEFAULT_SCENARIO: RiskRegisterScenarioId = "annual-declarations";

export function listRiskRegisterScenarios(): RiskRegisterScenario[] {
  return (Object.keys(SCENARIOS) as RiskRegisterScenarioId[]).map((scenarioId) =>
    resolveRiskRegisterScenario(scenarioId),
  );
}

export function resolveRiskRegisterScenario(
  scenarioId?: string,
  riskId?: string,
): RiskRegisterScenario {
  const definition = resolveDefinition(scenarioId);
  const declarations = definition.declarations.map(buildDeclarationItem);
  const risks = definition.risks.map(buildRiskItem);
  const selectedRisk =
    risks.find((item) => item.riskId === riskId) ??
    risks.find((item) => item.riskId === definition.selectedRiskId) ??
    risks[0];

  if (!selectedRisk) {
    throw new Error("missing_risk_items");
  }

  const detail = buildDetail(definition, selectedRisk.riskId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, declarations, risks, detail),
    selectedRiskId: selectedRisk.riskId,
    declarations,
    risks,
    detail,
  };
}

export function buildRiskRegisterCatalog(
  scenarioId?: string,
  riskId?: string,
): RiskRegisterCatalog {
  const selectedScenario = resolveRiskRegisterScenario(scenarioId, riskId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listRiskRegisterScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildDeclarationItem(state: ScenarioDeclarationState): ConflictDeclarationItem {
  const record = getDeclarationRecord(state.declarationId);

  return {
    declarationId: record.declarationId,
    actorName: record.actorName,
    dateLabel: state.dateLabel,
    summary: state.summary,
    status: state.status,
    statusLabel: state.statusLabel,
    documentLabel: state.documentLabel,
  };
}

function buildRiskItem(state: ScenarioRiskState): RiskMatrixItem {
  const record = getRiskRecord(state.riskId);

  return {
    riskId: record.riskId,
    title: record.title,
    categoryLabel: record.categoryLabel,
    probabilityLabel: record.probabilityLabel,
    impactLabel: record.impactLabel,
    ownerLabel: record.ownerLabel,
    status: state.status,
    statusLabel: state.statusLabel,
  };
}

function buildDetail(definition: RiskScenarioDefinition, riskId: string): RiskDetail {
  const record = getRiskRecord(riskId);
  const state = getRiskState(definition, riskId);

  return {
    riskId: record.riskId,
    title: record.title,
    status: state.status,
    noticeLabel:
      state.status === "ready"
        ? "Risco monitorado com mitigacao formalizada e sem bloqueios adicionais neste recorte."
        : state.status === "attention"
          ? "Risco em acompanhamento pela Qualidade, com mitigacoes e revisoes ainda em curso."
          : "Risco critico exige decisao colegiada e bloqueia liberacao silenciosa do fluxo relacionado.",
    categoryLabel: record.categoryLabel,
    probabilityLabel: record.probabilityLabel,
    impactLabel: record.impactLabel,
    ownerLabel: record.ownerLabel,
    lastReviewedAtLabel: state.lastReviewedAtLabel,
    reviewCadenceLabel: state.reviewCadenceLabel,
    description: record.description,
    mitigationPlanLabel: record.mitigationPlanLabel,
    evidenceLabel: record.evidenceLabel,
    linkedDeclarationLabel: state.linkedDeclarationLabel,
    managementReviewLabel: state.managementReviewLabel,
    actions: state.actions,
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      organizationSettingsScenarioId: state.organizationSettingsScenarioId,
      complaintScenarioId: state.complaintScenarioId,
      complaintId: state.complaintId,
      nonconformityScenarioId: state.nonconformityScenarioId,
      nonconformityId: state.nonconformityId,
    },
  };
}

function buildSummary(
  recommendedAction: string,
  declarations: ConflictDeclarationItem[],
  risks: RiskMatrixItem[],
  detail: RiskDetail,
): RiskRegisterScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Declaracoes vigentes e riscos monitorados prontos para auditoria"
        : detail.status === "attention"
          ? "Declaracoes e riscos exigem acompanhamento da Qualidade"
          : "Risco critico exige decisao colegiada e fail-closed",
    declarationCount: declarations.length,
    pendingDeclarationCount: declarations.filter((item) => item.status === "blocked").length,
    conflictDeclarationCount: declarations.filter((item) => item.status === "attention").length,
    activeRiskCount: risks.length,
    highImpactRiskCount: risks.filter((item) => item.impactLabel === "Alta").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getDeclarationRecord(declarationId: string): DeclarationRecord {
  const record = DECLARATIONS[declarationId];
  if (!record) {
    throw new Error(`missing_declaration_record:${declarationId}`);
  }

  return record;
}

function getRiskRecord(riskId: string): RiskRecord {
  const record = RISKS[riskId];
  if (!record) {
    throw new Error(`missing_risk_record:${riskId}`);
  }

  return record;
}

function getRiskState(
  definition: RiskScenarioDefinition,
  riskId: string,
): ScenarioRiskState {
  const state = definition.risks.find((item) => item.riskId === riskId);
  if (!state) {
    throw new Error(`missing_risk_state:${riskId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): RiskRegisterScenarioId {
  return isRiskRegisterScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): RiskScenarioDefinition {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = SCENARIOS[resolvedScenarioId];

  if (!definition) {
    throw new Error(`missing_risk_scenario:${resolvedScenarioId}`);
  }

  return definition;
}

function isRiskRegisterScenarioId(
  value: string | undefined,
): value is RiskRegisterScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
