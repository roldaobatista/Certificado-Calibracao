import type {
  ComplaintAction,
  ComplaintDetail,
  ComplaintListItem,
  ComplaintRegistryCatalog,
  ComplaintRegistryScenario,
  ComplaintRegistryScenarioId,
  RegistryOperationalStatus,
} from "@afere/contracts";

type ComplaintRecord = {
  complaintId: string;
  title: string;
  customerName: string;
  summary: string;
  channelLabel: string;
  severityLabel: string;
  ownerLabel: string;
  receivedAtLabel: string;
  responseDeadlineLabel: string;
  narrative: string;
  linkedNonconformityLabel: string;
  reissueReasonLabel?: string;
  evidenceLabel: string;
  workspaceScenarioId?: ComplaintDetail["links"]["workspaceScenarioId"];
  auditTrailScenarioId?: ComplaintDetail["links"]["auditTrailScenarioId"];
  nonconformityScenarioId?: ComplaintDetail["links"]["nonconformityScenarioId"];
  nonconformityId?: ComplaintDetail["links"]["nonconformityId"];
  serviceOrderScenarioId?: ComplaintDetail["links"]["serviceOrderScenarioId"];
  reviewItemId?: string;
};

type ScenarioComplaintState = {
  complaintId: string;
  status: RegistryOperationalStatus;
  actions: ComplaintAction[];
  blockers: string[];
  warnings: string[];
};

type ComplaintScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedComplaintId: string;
  items: ScenarioComplaintState[];
};

const RECORDS: Record<string, ComplaintRecord> = {
  "recl-004": {
    complaintId: "recl-004",
    title: "RECL-004 · Cliente pede esclarecimento sobre faixa declarada",
    customerName: "Padaria Pao Doce",
    summary: "Cliente solicitou esclarecimento sobre a faixa usada no certificado mais recente.",
    channelLabel: "Portal do cliente",
    severityLabel: "Media",
    ownerLabel: "Ana Costa",
    receivedAtLabel: "15/04/2026 10:18",
    responseDeadlineLabel: "17/04/2026 10:18",
    narrative:
      "\"O certificado da BAL-021 cita a faixa de 20 kg, mas o nosso uso diario ocorre mais proximo de 15 kg. Precisamos confirmar se a faixa aplicada esta correta.\"",
    linkedNonconformityLabel: "Triagem inicial concluiu que a resposta tecnica pode seguir sem abrir NC neste momento.",
    evidenceLabel: "RECL-004, mensagem do portal, consulta ao procedimento PT-005 e minuta da resposta tecnica.",
    workspaceScenarioId: "team-attention",
    auditTrailScenarioId: "recent-emission",
    serviceOrderScenarioId: "history-pending",
    reviewItemId: "os-2026-00141",
  },
  "recl-007": {
    complaintId: "recl-007",
    title: "RECL-007 · Tag incorreta no certificado emitido",
    customerName: "Lab. Acme",
    summary: "Cliente reportou que o certificado foi emitido com a TAG BAL-070 em vez de BAL-007.",
    channelLabel: "E-mail",
    severityLabel: "Alta",
    ownerLabel: "Joao Silva",
    receivedAtLabel: "17/04/2026 14:05",
    responseDeadlineLabel: "21/04/2026 14:05",
    narrative:
      "\"Recebemos certificado da balanca BAL-007 com TAG errado (BAL-070). Precisamos da correcao formal antes da proxima auditoria interna.\"",
    linkedNonconformityLabel: "NC-015 aberta para trilhar a reclamacao e sustentar a decisao de reemissao controlada.",
    reissueReasonLabel: "DADO_CADASTRAL",
    evidenceLabel: "RECL-007, e-mail original, checklist de reemissao, minuta de resposta e parecer preliminar da Qualidade.",
    workspaceScenarioId: "release-blocked",
    auditTrailScenarioId: "reissue-attention",
    nonconformityScenarioId: "critical-response",
    nonconformityId: "nc-015",
    serviceOrderScenarioId: "review-blocked",
    reviewItemId: "os-2026-00147",
  },
  "recl-002": {
    complaintId: "recl-002",
    title: "RECL-002 · Divergencia documental encerrada",
    customerName: "Industria XYZ",
    summary: "Reclamacao documental encerrada apos resposta formal e envio da evidencia complementar.",
    channelLabel: "Telefone + e-mail",
    severityLabel: "Baixa",
    ownerLabel: "Maria Souza",
    receivedAtLabel: "12/03/2026 09:40",
    responseDeadlineLabel: "14/03/2026 09:40",
    narrative:
      "\"O cliente nao localizou a pagina com a assinatura tecnica. A equipe reenviou o documento e explicou o fluxo de verificacao publica.\"",
    linkedNonconformityLabel: "Sem NC aberta no fechamento; caso tratado como orientacao documental encerrada.",
    evidenceLabel: "RECL-002, registro telefonico, e-mail de resposta e confirmacao de aceite do cliente.",
    workspaceScenarioId: "baseline-ready",
    auditTrailScenarioId: "recent-emission",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
  },
};

const SCENARIOS: Record<ComplaintRegistryScenarioId, ComplaintScenarioDefinition> = {
  "open-follow-up": {
    label: "Reclamacao aberta em acompanhamento",
    description: "Recorte com reclamacao aberta, resposta tecnica em preparo e sem reemissao formal iniciada.",
    recommendedAction: "Responder o cliente dentro do prazo e arquivar a justificativa tecnica sem inflar o caso para NC se o impacto continuar baixo.",
    selectedComplaintId: "recl-004",
    items: [
      {
        complaintId: "recl-004",
        status: "attention",
        actions: [
          {
            key: "acknowledge",
            label: "Acuso de recebimento",
            status: "complete",
            detail: "Confirmado ao cliente em 15/04 10:31.",
          },
          {
            key: "technical-response",
            label: "Resposta formal ao cliente",
            status: "pending",
            detail: "Resposta tecnica em preparo pelo responsavel da qualidade.",
          },
          {
            key: "close-complaint",
            label: "Fechar reclamacao",
            status: "pending",
            detail: "Aguardar aceite do cliente apos a resposta tecnica.",
          },
        ],
        blockers: [],
        warnings: ["Prazo de resposta vence em menos de 48h uteis."],
      },
      {
        complaintId: "recl-007",
        status: "blocked",
        actions: [
          {
            key: "acknowledge",
            label: "Acuso de recebimento",
            status: "complete",
            detail: "Enviado ao cliente em 17/04 14:22.",
          },
        ],
        blockers: ["Reemissao controlada ainda nao iniciada para o caso critico."],
        warnings: [],
      },
      {
        complaintId: "recl-002",
        status: "ready",
        actions: [
          {
            key: "close-complaint",
            label: "Fechar reclamacao",
            status: "complete",
            detail: "Encerrada com aceite do cliente.",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
  "critical-response": {
    label: "Reclamacao critica com reemissao pendente",
    description: "Recorte com impacto direto no certificado emitido, NC vinculada e reemissao controlada ainda em aberto.",
    recommendedAction: "Iniciar a reemissao controlada, registrar a resposta formal ao cliente e manter a NC associada como ancora da decisao.",
    selectedComplaintId: "recl-007",
    items: [
      {
        complaintId: "recl-004",
        status: "attention",
        actions: [
          {
            key: "technical-response",
            label: "Resposta formal ao cliente",
            status: "pending",
            detail: "Resposta tecnica segue em preparo.",
          },
        ],
        blockers: [],
        warnings: ["Caso aberto sem impacto direto em emissao."],
      },
      {
        complaintId: "recl-007",
        status: "blocked",
        actions: [
          {
            key: "acknowledge",
            label: "Acuso de recebimento",
            status: "complete",
            detail: "Enviado ao cliente em 17/04 14:22.",
          },
          {
            key: "link-nc",
            label: "NC vinculada",
            status: "complete",
            detail: "NC-015 aberta para sustentar a tratativa formal da reclamacao.",
          },
          {
            key: "start-reissue",
            label: "Iniciar fluxo de reemissao",
            status: "pending",
            detail: "Motivo DADO_CADASTRAL ainda nao formalizado no fluxo canonico de reemissao.",
          },
          {
            key: "formal-response",
            label: "Resposta formal ao cliente",
            status: "pending",
            detail: "Resposta depende da definicao da reemissao e do texto final da qualidade.",
          },
          {
            key: "close-complaint",
            label: "Fechar reclamacao",
            status: "blocked",
            detail: "Encerramento bloqueado ate concluir reemissao e receber aceite formal do cliente.",
          },
        ],
        blockers: [
          "O cliente ainda nao recebeu resposta formal conclusiva.",
          "A reemissao controlada permanece pendente para um erro cadastral no certificado.",
        ],
        warnings: ["Prazo de resposta ultrapassado exige priorizacao da Qualidade."],
      },
      {
        complaintId: "recl-002",
        status: "ready",
        actions: [
          {
            key: "close-complaint",
            label: "Fechar reclamacao",
            status: "complete",
            detail: "Encerrada com aceite do cliente.",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
  "resolved-history": {
    label: "Historico de reclamacao resolvida",
    description: "Recorte com reclamacao encerrada e mantida para historico auditavel da Qualidade.",
    recommendedAction: "Manter a evidencia arquivada e reutilizar o aprendizado em treinamento e checklist documental.",
    selectedComplaintId: "recl-002",
    items: [
      {
        complaintId: "recl-004",
        status: "attention",
        actions: [
          {
            key: "technical-response",
            label: "Resposta formal ao cliente",
            status: "pending",
            detail: "Resposta tecnica segue em preparo.",
          },
        ],
        blockers: [],
        warnings: ["Prazo de resposta vence em menos de 48h uteis."],
      },
      {
        complaintId: "recl-007",
        status: "blocked",
        actions: [
          {
            key: "start-reissue",
            label: "Iniciar fluxo de reemissao",
            status: "pending",
            detail: "Reemissao controlada ainda pendente.",
          },
        ],
        blockers: ["Caso critico segue aberto em paralelo."],
        warnings: [],
      },
      {
        complaintId: "recl-002",
        status: "ready",
        actions: [
          {
            key: "acknowledge",
            label: "Acuso de recebimento",
            status: "complete",
            detail: "Registrado no mesmo dia da abertura.",
          },
          {
            key: "formal-response",
            label: "Resposta formal ao cliente",
            status: "complete",
            detail: "Resposta enviada e aceita pelo cliente.",
          },
          {
            key: "close-complaint",
            label: "Fechar reclamacao",
            status: "complete",
            detail: "Encerramento registrado com evidencias arquivadas.",
          },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: ComplaintRegistryScenarioId = "open-follow-up";

export function listComplaintScenarios(): ComplaintRegistryScenario[] {
  return (Object.keys(SCENARIOS) as ComplaintRegistryScenarioId[]).map((scenarioId) =>
    resolveComplaintScenario(scenarioId),
  );
}

export function resolveComplaintScenario(
  scenarioId?: string,
  complaintId?: string,
): ComplaintRegistryScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildListItem);
  const selectedItem =
    items.find((item) => item.complaintId === complaintId) ??
    items.find((item) => item.complaintId === definition.selectedComplaintId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_complaint_items");
  }

  const detail = buildDetail(definition, selectedItem.complaintId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, items, detail),
    selectedComplaintId: selectedItem.complaintId,
    items,
    detail,
  };
}

export function buildComplaintCatalog(
  scenarioId?: string,
  complaintId?: string,
): ComplaintRegistryCatalog {
  const selectedScenario = resolveComplaintScenario(scenarioId, complaintId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listComplaintScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildListItem(state: ScenarioComplaintState): ComplaintListItem {
  const record = getRecord(state.complaintId);

  return {
    complaintId: record.complaintId,
    customerName: record.customerName,
    summary: record.summary,
    channelLabel: record.channelLabel,
    severityLabel: record.severityLabel,
    ownerLabel: record.ownerLabel,
    receivedAtLabel: record.receivedAtLabel,
    status: state.status,
  };
}

function buildDetail(
  definition: ComplaintScenarioDefinition,
  complaintId: string,
): ComplaintDetail {
  const record = getRecord(complaintId);
  const state = getState(definition, complaintId);

  return {
    complaintId: record.complaintId,
    title: record.title,
    status: state.status,
    noticeLabel:
      state.status === "ready"
        ? "Reclamacao encerrada e mantida apenas para historico auditavel."
        : state.status === "attention"
          ? "Reclamacao aberta em acompanhamento com resposta formal em preparo."
          : "Reclamacao critica aberta com impacto direto no fluxo e na resposta ao cliente.",
    customerName: record.customerName,
    channelLabel: record.channelLabel,
    ownerLabel: record.ownerLabel,
    receivedAtLabel: record.receivedAtLabel,
    responseDeadlineLabel: record.responseDeadlineLabel,
    narrative: record.narrative,
    linkedNonconformityLabel: record.linkedNonconformityLabel,
    reissueReasonLabel: record.reissueReasonLabel,
    evidenceLabel: record.evidenceLabel,
    actions: state.actions,
    blockers: state.blockers,
    warnings: state.warnings,
    links: {
      workspaceScenarioId: record.workspaceScenarioId,
      auditTrailScenarioId: record.auditTrailScenarioId,
      nonconformityScenarioId: record.nonconformityScenarioId,
      nonconformityId: record.nonconformityId,
      serviceOrderScenarioId: record.serviceOrderScenarioId,
      reviewItemId: record.reviewItemId,
    },
  };
}

function buildSummary(
  recommendedAction: string,
  items: ComplaintListItem[],
  detail: ComplaintDetail,
): ComplaintRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Historico de reclamacoes resolvidas disponivel para auditoria"
        : detail.status === "attention"
          ? "Reclamacao aberta exige resposta formal da Qualidade"
          : "Reclamacao critica bloqueia o encerramento e exige reemissao",
    openCount: items.filter((item) => item.status !== "ready").length,
    overdueCount: items.filter((item) => item.status === "blocked").length,
    reissuePendingCount: items.filter((item) => item.status === "blocked").length,
    resolvedLast30d: items.filter((item) => item.status === "ready").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getRecord(complaintId: string): ComplaintRecord {
  const record = RECORDS[complaintId];
  if (!record) {
    throw new Error(`missing_complaint_record:${complaintId}`);
  }

  return record;
}

function getState(
  definition: ComplaintScenarioDefinition,
  complaintId: string,
): ScenarioComplaintState {
  const state = definition.items.find((item) => item.complaintId === complaintId);
  if (!state) {
    throw new Error(`missing_complaint_state:${complaintId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): ComplaintRegistryScenarioId {
  return isComplaintScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ComplaintScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isComplaintScenarioId(
  value: string | undefined,
): value is ComplaintRegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
