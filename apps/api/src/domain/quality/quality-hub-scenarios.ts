import type {
  QualityHubCatalog,
  QualityHubModule,
  QualityHubModuleAvailability,
  QualityHubModuleKey,
  QualityHubScenario,
  QualityHubScenarioId,
  QualityHubSummary,
  RegistryOperationalStatus,
} from "@afere/contracts";

type ModuleMeta = {
  title: string;
  clauseLabel: string;
  ctaLabel: string;
};

type ModuleScenarioState = {
  key: QualityHubModuleKey;
  metricLabel: string;
  summary: string;
  status: RegistryOperationalStatus;
  availability: QualityHubModuleAvailability;
  href?: string;
  nextStepLabel: string;
  blockers: string[];
  warnings: string[];
};

type QualityHubScenarioDefinition = {
  label: string;
  description: string;
  status: RegistryOperationalStatus;
  selectedModuleKey: QualityHubModuleKey;
  links: QualityHubScenario["links"];
  metrics: Omit<
    QualityHubSummary,
    | "status"
    | "implementedModuleCount"
    | "plannedModuleCount"
    | "recommendedAction"
    | "blockers"
    | "warnings"
  >;
  recommendedAction: string;
  blockers: string[];
  warnings: string[];
  modules: ModuleScenarioState[];
};

const MODULE_META: Record<QualityHubModuleKey, ModuleMeta> = {
  nonconformities: {
    title: "NC e acoes corretivas",
    clauseLabel: "ISO/IEC 17025 7.10 e 8.7",
    ctaLabel: "Abrir NCs",
  },
  "audit-trail": {
    title: "Trilha de auditoria",
    clauseLabel: "ISO/IEC 17025 7.5 e 8.4",
    ctaLabel: "Abrir trilha",
  },
  complaints: {
    title: "Reclamacoes",
    clauseLabel: "ISO/IEC 17025 7.9",
    ctaLabel: "Abrir reclamacoes",
  },
  "nonconforming-work": {
    title: "Trabalho nao conforme",
    clauseLabel: "ISO/IEC 17025 7.10",
    ctaLabel: "Planejado",
  },
  "internal-audit": {
    title: "Auditoria interna",
    clauseLabel: "ISO/IEC 17025 8.8",
    ctaLabel: "Planejado",
  },
  "management-review": {
    title: "Analise critica",
    clauseLabel: "ISO/IEC 17025 8.9",
    ctaLabel: "Planejado",
  },
  "risk-impartiality": {
    title: "Imparcialidade e riscos",
    clauseLabel: "ISO/IEC 17025 4.1 e 8.5",
    ctaLabel: "Abrir riscos",
  },
  documents: {
    title: "Documentos da qualidade",
    clauseLabel: "ISO/IEC 17025 8.3 e 8.4",
    ctaLabel: "Abrir documentos",
  },
  indicators: {
    title: "Indicadores",
    clauseLabel: "ISO/IEC 17025 8.9",
    ctaLabel: "Planejado",
  },
};

const SCENARIOS: Record<QualityHubScenarioId, QualityHubScenarioDefinition> = {
  "operational-attention": {
    label: "Qualidade em acompanhamento preventivo",
    description:
      "O gestor acompanha NCs abertas, uma reclamacao ainda em tratamento e backlog planejado das demais areas sem perder o recorte operacional ja implementado.",
    status: "attention",
    selectedModuleKey: "nonconformities",
    links: {
      workspaceScenarioId: "team-attention",
      organizationSettingsScenarioId: "renewal-attention",
      auditTrailScenarioId: "reissue-attention",
      nonconformityScenarioId: "open-attention",
    },
    metrics: {
      organizationName: "Lab. Acme",
      openNonconformities: 2,
      overdueActions: 1,
      auditProgramCount: 4,
      complaintCount: 1,
      activeRiskCount: 7,
      nextManagementReviewLabel: "30/06/2026",
    },
    recommendedAction:
      "Fechar a acao corretiva vencendo, responder a reclamacao aberta e usar trilha/NC como ancora auditavel ate as demais areas ganharem fluxo proprio.",
    blockers: [],
    warnings: [
      "O modulo de reclamacoes segue com uma resposta formal pendente e precisa de fechamento dentro do prazo.",
      "Trabalho nao conforme, auditoria interna, analise critica e indicadores seguem explicitamente planejados.",
    ],
    modules: [
      {
        key: "nonconformities",
        metricLabel: "2 NC abertas · 1 acao vencendo",
        summary: "Modulo canonico ativo para tratar NCs, acao corretiva, evidencias e retorno ao fluxo operacional.",
        status: "attention",
        availability: "implemented",
        href: "/quality/nonconformities?scenario=open-attention&nc=nc-014",
        nextStepLabel: "Fechar a acao corretiva da NC-014 e manter a dupla conferencia ate a evidência final.",
        blockers: [],
        warnings: ["Uma NC critica segue em paralelo e precisa de leitura dedicada quando houver escalacao."],
      },
      {
        key: "audit-trail",
        metricLabel: "1 reemissao com ressalva",
        summary: "A trilha append-only ja materializa eventos sensiveis e serve como ancora de evidencia do hub.",
        status: "attention",
        availability: "implemented",
        href: "/quality/audit-trail?scenario=reissue-attention&event=audit-7",
        nextStepLabel: "Conferir a cadeia com reemissao controlada antes da proxima reuniao da qualidade.",
        blockers: [],
        warnings: ["A cadeia possui reemissao controlada que merece leitura humana cuidadosa."],
      },
      {
        key: "complaints",
        metricLabel: "1 reclamacao aberta",
        summary: "Modulo canonico ativo para relato, prazo de resposta, checklist de acoes e vinculos com NC, trilha e OS.",
        status: "attention",
        availability: "implemented",
        href: "/quality/complaints?scenario=open-follow-up&complaint=recl-004",
        nextStepLabel: "Responder a reclamacao aberta dentro do prazo e escalar apenas os casos com impacto direto em certificado.",
        blockers: [],
        warnings: ["Uma reclamacao aberta segue aguardando resposta formal da Qualidade."],
      },
      {
        key: "nonconforming-work",
        metricLabel: "1 caso derivado de NC",
        summary: "O tratamento de trabalho nao conforme continua representado apenas pelos sinais canonicos de NC e workspace.",
        status: "attention",
        availability: "planned",
        nextStepLabel: "Criar leitura propria para congelamento, contencao e reabertura segura de OS afetadas.",
        blockers: [],
        warnings: ["A classificacao ainda depende da interpretacao cruzada entre workspace e NC."],
      },
      {
        key: "internal-audit",
        metricLabel: "Programa anual: 4 ciclos",
        summary: "O plano anual ainda nao tem rota dedicada, mas o hub preserva a demanda visivel para o gestor.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Materializar plano, execucao e evidencias do programa interno de auditoria.",
        blockers: [],
        warnings: [],
      },
      {
        key: "management-review",
        metricLabel: "Proxima reuniao: 30/06/2026",
        summary: "A pauta consolidada continua planejada e ainda depende da convergencia entre NC, reclamacoes, riscos e indicadores.",
        status: "attention",
        availability: "planned",
        nextStepLabel: "Gerar pauta automatica com entradas vindas das leituras canonicamente implementadas.",
        blockers: [],
        warnings: ["Ainda nao existe ata, deliberação ou workflow dedicados nesta area."],
      },
      {
        key: "risk-impartiality",
        metricLabel: "3 riscos ativos · 1 declaracao pendente",
        summary: "Modulo canonico ativo para declaracoes anuais, matriz de riscos, mitigacoes e exportacao controlada para analise critica.",
        status: "attention",
        availability: "implemented",
        href: "/quality/risk-register?scenario=annual-declarations&risk=risk-003",
        nextStepLabel: "Fechar a rodada anual de declaracoes e manter os conflitos declarados sob revisao da Qualidade.",
        blockers: [],
        warnings: ["Uma declaracao anual segue pendente e exige restricao adicional em atribuicoes sensiveis."],
      },
      {
        key: "documents",
        metricLabel: "24 documentos vigentes · 1 revisao preventiva",
        summary: "Modulo canonico ativo para MQ, PG, PT, IT e FR com vigencia, historico obsoleto e referencias cruzadas ao contexto tecnico.",
        status: "attention",
        availability: "implemented",
        href: "/quality/documents?scenario=revision-attention&document=document-pg005-r02",
        nextStepLabel: "Concluir a revisao preventiva do PG-005 e manter o acervo historico apenas para consulta auditavel.",
        blockers: [],
        warnings: ["Procedimentos tecnicos continuam separados do acervo SGQ, mas agora ligados por contexto canônico."],
      },
      {
        key: "indicators",
        metricLabel: "Indicadores consolidados pendentes",
        summary: "Os indicadores ainda nao possuem dashboard proprio; o hub apenas registra a demanda prevista no PRD.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Materializar painel gerencial com tendencia de NC, reclamacoes, riscos e auditorias.",
        blockers: [],
        warnings: [],
      },
    ],
  },
  "critical-response": {
    label: "Qualidade em resposta critica",
    description:
      "Uma reclamacao com impacto operacional e uma trilha com falha de integridade empurram o hub para bloqueio fail-closed.",
    status: "blocked",
    selectedModuleKey: "audit-trail",
    links: {
      workspaceScenarioId: "release-blocked",
      organizationSettingsScenarioId: "profile-change-blocked",
      auditTrailScenarioId: "integrity-blocked",
      nonconformityScenarioId: "critical-response",
    },
    metrics: {
      organizationName: "Lab. Acme",
      openNonconformities: 1,
      overdueActions: 2,
      auditProgramCount: 4,
      complaintCount: 2,
      activeRiskCount: 9,
      nextManagementReviewLabel: "Hoje · extraordinaria",
    },
    recommendedAction:
      "Congelar o fluxo afetado, validar a hash-chain, usar a NC critica como ancora e preparar analise critica extraordinaria antes de qualquer reemissao.",
    blockers: [
      "Falha de integridade em trilha critica impede liberar o recorte como saudavel.",
      "NC critica aberta com reclamacao correlata exige resposta formal da Qualidade.",
    ],
    warnings: [
      "Trabalho nao conforme, auditoria interna, analise critica e indicadores seguem planejados e precisam nascer sem perder o contexto critico atual.",
    ],
    modules: [
      {
        key: "nonconformities",
        metricLabel: "1 NC critica aberta",
        summary: "O modulo de NC ja concentra a contencao e a acao corretiva do caso mais sensivel do recorte.",
        status: "blocked",
        availability: "implemented",
        href: "/quality/nonconformities?scenario=critical-response&nc=nc-015",
        nextStepLabel: "Formalizar a investigacao critica e manter o fluxo relacionado bloqueado ate decisao conclusiva.",
        blockers: ["NC-015 critica continua bloqueando a operacao relacionada."],
        warnings: ["Cliente externo aguarda posicionamento formal da investigacao."],
      },
      {
        key: "audit-trail",
        metricLabel: "1 falha de integridade",
        summary: "A trilha append-only aponta divergencia estrutural e sustenta o fail-closed deste cenario.",
        status: "blocked",
        availability: "implemented",
        href: "/quality/audit-trail?scenario=integrity-blocked&event=audit-9",
        nextStepLabel: "Investigar a hash-chain e so destravar o fluxo apos evidencia formal da correção.",
        blockers: ["Hash-chain divergente impede considerar o recorte seguro para emissao ou reemissao."],
        warnings: ["A exportacao permanece bloqueada enquanto a divergencia nao for saneada."],
      },
      {
        key: "complaints",
        metricLabel: "2 reclamacoes abertas",
        summary: "Modulo canonico ativo para triar resposta formal, vinculo a NC e gatilho de reemissao controlada.",
        status: "blocked",
        availability: "implemented",
        href: "/quality/complaints?scenario=critical-response&complaint=recl-007",
        nextStepLabel: "Concluir a resposta formal e iniciar a reemissao controlada antes de encerrar o caso critico.",
        blockers: ["O cliente ainda nao recebeu resposta formal conclusiva para o caso critico."],
        warnings: [],
      },
      {
        key: "nonconforming-work",
        metricLabel: "OS congelada por contencao",
        summary: "O tratamento de trabalho nao conforme ainda depende da leitura manual entre workspace, NC e trilha critica.",
        status: "blocked",
        availability: "planned",
        nextStepLabel: "Materializar a triagem de trabalho nao conforme com bloqueio explicito de OS e lote.",
        blockers: ["Sem modulo dedicado, a contencao fica distribuida entre telas operacionais."],
        warnings: [],
      },
      {
        key: "internal-audit",
        metricLabel: "1 ciclo extraordinario sugerido",
        summary: "O programa anual ainda nao foi materializado, mas este cenario ja exige acao extraordinaria da Qualidade.",
        status: "attention",
        availability: "planned",
        nextStepLabel: "Abrir um ciclo extraordinario no futuro modulo de auditoria interna.",
        blockers: [],
        warnings: ["A necessidade de auditoria extraordinaria esta sinalizada sem workflow proprio."],
      },
      {
        key: "management-review",
        metricLabel: "Reuniao extraordinaria hoje",
        summary: "A analise critica formal ainda nao existe no produto, mas o hub registra a urgencia de decisao colegiada.",
        status: "attention",
        availability: "planned",
        nextStepLabel: "Consolidar pauta critica com entradas de NC, trilha, risco e reclamacao.",
        blockers: [],
        warnings: ["Sem ata nem deliberação dedicadas por enquanto."],
      },
      {
        key: "risk-impartiality",
        metricLabel: "1 risco critico escalado",
        summary: "Modulo canonico ativo para escalonar pressao comercial, registrar mitigacoes e manter o fail-closed ancorado em declaracoes e matriz de riscos.",
        status: "blocked",
        availability: "implemented",
        href: "/quality/risk-register?scenario=commercial-pressure&risk=risk-001",
        nextStepLabel: "Registrar decisao colegiada da direcao antes de qualquer liberacao operacional relacionada.",
        blockers: ["Pressao comercial critica continua sem decisao colegiada registrada."],
        warnings: ["A pauta extraordinaria de analise critica ainda precisa ser consolidada."],
      },
      {
        key: "documents",
        metricLabel: "1 revisao obsoleta bloqueada",
        summary: "Modulo canonico ativo para acervo SGQ, com revisao obsoleta explicitamente bloqueada para uso operacional em casos novos.",
        status: "blocked",
        availability: "implemented",
        href: "/quality/documents?scenario=obsolete-blocked&document=document-pg005-r01",
        nextStepLabel: "Migrar qualquer consulta operacional para a revisao vigente correspondente antes de prosseguir com o caso critico.",
        blockers: ["Revisao obsoleta do PG-005 nao pode sustentar tratativas novas nem resposta critica atual."],
        warnings: ["A revisao vigente ainda segue em fechamento preventivo da Qualidade."],
      },
      {
        key: "indicators",
        metricLabel: "Indicadores criticos sem painel",
        summary: "Ainda nao existe dashboard dedicado para acompanhar impacto do incidente no sistema de gestao.",
        status: "attention",
        availability: "planned",
        nextStepLabel: "Criar painel com severidade, tempo de resposta e reincidencia dos casos criticos.",
        blockers: [],
        warnings: [],
      },
    ],
  },
  "stable-baseline": {
    label: "Qualidade em baseline estavel",
    description:
      "O recorte atual nao apresenta bloqueio critico e o hub destaca quais leituras ja estao prontas para auditoria e quais areas continuam planejadas.",
    status: "ready",
    selectedModuleKey: "audit-trail",
    links: {
      workspaceScenarioId: "baseline-ready",
      organizationSettingsScenarioId: "operational-ready",
      auditTrailScenarioId: "recent-emission",
      nonconformityScenarioId: "resolved-history",
    },
    metrics: {
      organizationName: "Lab. Acme",
      openNonconformities: 0,
      overdueActions: 0,
      auditProgramCount: 3,
      complaintCount: 0,
      activeRiskCount: 4,
      nextManagementReviewLabel: "30/06/2026",
    },
    recommendedAction:
      "Manter as leituras implementadas verdes, usar o hub como porta de entrada do gestor e seguir expandindo as areas ainda planejadas sem drift de contexto.",
    blockers: [],
    warnings: ["As areas ainda planejadas permanecem visiveis como backlog regulado e nao como dados ficticios."],
    modules: [
      {
        key: "nonconformities",
        metricLabel: "Historico sem NC aberta",
        summary: "O modulo de NC esta verde e preserva o historico encerrado para consulta e auditoria.",
        status: "ready",
        availability: "implemented",
        href: "/quality/nonconformities?scenario=resolved-history&nc=nc-011",
        nextStepLabel: "Manter as evidencias encerradas arquivadas e reutilizar o aprendizado no checklist vigente.",
        blockers: [],
        warnings: [],
      },
      {
        key: "audit-trail",
        metricLabel: "Hash-chain integra",
        summary: "A trilha append-only esta pronta para consulta e funciona como ancora de evidencia do hub estavel.",
        status: "ready",
        availability: "implemented",
        href: "/quality/audit-trail?scenario=recent-emission&event=audit-4",
        nextStepLabel: "Usar a trilha integra como ponto de partida para auditoria interna e revisoes rotineiras.",
        blockers: [],
        warnings: [],
      },
      {
        key: "complaints",
        metricLabel: "Sem reclamacoes abertas",
        summary: "Modulo canonico ativo apenas para historico; o recorte atual nao aponta backlog critico de reclamacoes.",
        status: "ready",
        availability: "implemented",
        href: "/quality/complaints?scenario=resolved-history&complaint=recl-002",
        nextStepLabel: "Manter as evidencias resolvidas arquivadas e reutilizar o aprendizado em treinamento e resposta documental.",
        blockers: [],
        warnings: [],
      },
      {
        key: "nonconforming-work",
        metricLabel: "Sem OS congelada",
        summary: "O tratamento especifico de trabalho nao conforme permanece planejado, sem caso aberto no recorte atual.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Criar o modulo dedicado antes do primeiro caso recorrente depender de rastreio manual.",
        blockers: [],
        warnings: [],
      },
      {
        key: "internal-audit",
        metricLabel: "Programa anual: 3 ciclos",
        summary: "A area segue planejada, com o programa anual apenas visivel pelo hub e sem execucao dedicada.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Materializar plano anual, execução e pareceres de auditoria interna.",
        blockers: [],
        warnings: [],
      },
      {
        key: "management-review",
        metricLabel: "Proxima reuniao: 30/06/2026",
        summary: "A analise critica ainda nao ganhou fluxo proprio, mas o hub ja preserva a proxima janela de revisao.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Transformar as leituras existentes em pauta automatica e ata versionada.",
        blockers: [],
        warnings: [],
      },
      {
        key: "risk-impartiality",
        metricLabel: "2 riscos monitorados",
        summary: "Modulo canonico ativo com declaracoes anuais arquivadas e riscos mantidos apenas em monitoramento rotineiro.",
        status: "ready",
        availability: "implemented",
        href: "/quality/risk-register?scenario=stable-monitoring&risk=risk-002",
        nextStepLabel: "Manter a revisao mensal da matriz e reutilizar o consolidado na analise critica ordinaria.",
        blockers: [],
        warnings: [],
      },
      {
        key: "documents",
        metricLabel: "24 documentos vigentes",
        summary: "Modulo canonico ativo com acervo SGQ vigente, historico obsoleto rastreavel e referencias cruzadas ao cadastro tecnico.",
        status: "ready",
        availability: "implemented",
        href: "/quality/documents?scenario=operational-ready&document=document-mq001-r03",
        nextStepLabel: "Manter o acervo vigente arquivado e seguir a cadencia anual de revisao do SGQ.",
        blockers: [],
        warnings: [],
      },
      {
        key: "indicators",
        metricLabel: "Painel gerencial planejado",
        summary: "O hub ainda nao tem dashboard dedicado de indicadores, mas preserva a necessidade como backlog auditavel.",
        status: "ready",
        availability: "planned",
        nextStepLabel: "Criar painel com tendencia de NC, reclamacoes, riscos e auditorias.",
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: QualityHubScenarioId = "operational-attention";

export function listQualityHubScenarios(): QualityHubScenario[] {
  return (Object.keys(SCENARIOS) as QualityHubScenarioId[]).map((scenarioId) =>
    resolveQualityHubScenario(scenarioId),
  );
}

export function resolveQualityHubScenario(
  scenarioId?: string,
  moduleKey?: string,
): QualityHubScenario {
  const resolvedScenarioId = resolveScenarioId(scenarioId);
  const definition = resolveDefinition(resolvedScenarioId);
  const modules = definition.modules.map(buildModule);
  const selectedModule =
    modules.find((module) => module.key === moduleKey) ??
    modules.find((module) => module.key === definition.selectedModuleKey) ??
    modules[0];

  if (!selectedModule) {
    throw new Error("missing_quality_hub_modules");
  }

  return {
    id: resolvedScenarioId,
    label: definition.label,
    description: definition.description,
    selectedModuleKey: selectedModule.key,
    summary: buildSummary(definition, modules),
    links: definition.links,
    modules,
  };
}

export function buildQualityHubCatalog(
  scenarioId?: string,
  moduleKey?: string,
): QualityHubCatalog {
  const selectedScenario = resolveQualityHubScenario(scenarioId, moduleKey);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listQualityHubScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildModule(state: ModuleScenarioState): QualityHubModule {
  const meta = getModuleMeta(state.key);

  return {
    key: state.key,
    title: meta.title,
    clauseLabel: meta.clauseLabel,
    metricLabel: state.metricLabel,
    summary: state.summary,
    status: state.status,
    availability: state.availability,
    href: state.href,
    ctaLabel: state.href ? meta.ctaLabel : "Planejado",
    nextStepLabel: state.nextStepLabel,
    blockers: state.blockers,
    warnings: state.warnings,
  };
}

function buildSummary(
  definition: QualityHubScenarioDefinition,
  modules: QualityHubModule[],
): QualityHubSummary {
  return {
    status: definition.status,
    ...definition.metrics,
    implementedModuleCount: modules.filter((module) => module.availability === "implemented").length,
    plannedModuleCount: modules.filter((module) => module.availability === "planned").length,
    recommendedAction: definition.recommendedAction,
    blockers: definition.blockers,
    warnings: definition.warnings,
  };
}

function resolveScenarioId(scenarioId?: string): QualityHubScenarioId {
  return isQualityHubScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId: QualityHubScenarioId): QualityHubScenarioDefinition {
  return SCENARIOS[scenarioId];
}

function getModuleMeta(key: QualityHubModuleKey): ModuleMeta {
  return MODULE_META[key];
}

function isQualityHubScenarioId(value: string | undefined): value is QualityHubScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
