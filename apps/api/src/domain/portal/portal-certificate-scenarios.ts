import type {
  PortalCertificateAction,
  PortalCertificateCatalog,
  PortalCertificateDetail,
  PortalCertificateListItem,
  PortalCertificateMetadataField,
  PortalCertificateScenario,
  PortalCertificateScenarioId,
} from "@afere/contracts";

type CertificateRecord = {
  certificateId: string;
  certificateNumber: string;
  equipmentId: string;
  equipmentLabel: string;
  issuedAtLabel: string;
  hashLabel: string;
  signatureLabel: string;
  viewerLabel: string;
  publicLinkLabel: string;
  metadataFields: PortalCertificateMetadataField[];
  verificationSteps: string[];
  equipmentScenarioId: PortalCertificateDetail["equipmentScenarioId"];
  dashboardScenarioId: PortalCertificateDetail["dashboardScenarioId"];
  publicVerifyScenarioId: PortalCertificateDetail["publicVerifyScenarioId"];
};

type ScenarioCertificateState = {
  certificateId: string;
  status: PortalCertificateListItem["status"];
  statusLabel: string;
  recommendedAction: string;
  actions: PortalCertificateAction[];
  blockers: string[];
  warnings: string[];
};

type ScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  items: ScenarioCertificateState[];
  selectedCertificateId: string;
};

const CERTIFICATES: Record<string, CertificateRecord> = {
  "cert-00142": {
    certificateId: "cert-00142",
    certificateNumber: "CAL-1234/2026/00142",
    equipmentId: "equipment-bal-007",
    equipmentLabel: "BAL-007 Toledo Prix 3",
    issuedAtLabel: "19/04/2026",
    hashLabel: "a3f9c12d...",
    signatureLabel: "Assinatura verificada",
    viewerLabel: "Previa integral do PDF disponivel no viewer autenticado.",
    publicLinkLabel: "verifica.afere.com.br/c/a3f9c12d",
    metadataFields: [
      { label: "Laboratorio emissor", value: "Lab. Acme" },
      { label: "Equipamento", value: "BAL-007 Toledo Prix 3" },
      { label: "Status", value: "Valido" },
      { label: "Revisao", value: "R0" },
      { label: "Data de emissao", value: "19/04/2026" },
    ],
    verificationSteps: [
      "Aponte a camera para o QR code da ultima pagina.",
      "Ou acesse o link publico do certificado.",
      "Confirme que o numero e o hash exibidos coincidem com o documento.",
    ],
    equipmentScenarioId: "stable-portfolio",
    dashboardScenarioId: "stable-portfolio",
    publicVerifyScenarioId: "authentic",
  },
  "cert-00135-r1": {
    certificateId: "cert-00135-r1",
    certificateNumber: "CAL-1234/2026/00135-R1",
    equipmentId: "equipment-bal-019",
    equipmentLabel: "BAL-019 Toledo Prix 15",
    issuedAtLabel: "14/04/2026",
    hashLabel: "d44bc871...",
    signatureLabel: "Assinatura verificada com rastreio de reemissao",
    viewerLabel: "Previa integral disponivel, com indicacao clara de reemissao controlada.",
    publicLinkLabel: "verifica.afere.com.br/c/d44bc871",
    metadataFields: [
      { label: "Laboratorio emissor", value: "Lab. Acme" },
      { label: "Equipamento", value: "BAL-019 Toledo Prix 15" },
      { label: "Status", value: "Reemitido" },
      { label: "Revisao", value: "R1" },
      { label: "Data de emissao", value: "14/04/2026" },
    ],
    verificationSteps: [
      "Use o QR da ultima revisao para confirmar a versao atual.",
      "Consulte o viewer para ver a indicacao de reemissao rastreada.",
      "Mantenha a referencia ao certificado anterior apenas como historico.",
    ],
    equipmentScenarioId: "overdue-blocked",
    dashboardScenarioId: "overdue-blocked",
    publicVerifyScenarioId: "reissued",
  },
  "cert-00128": {
    certificateId: "cert-00128",
    certificateNumber: "CAL-1234/2026/00128",
    equipmentId: "equipment-bal-021",
    equipmentLabel: "BAL-021 Marte 20 kg",
    issuedAtLabel: "09/04/2026",
    hashLabel: "9ac11f0b...",
    signatureLabel: "Assinatura indisponivel para visualizacao logada",
    viewerLabel: "Previa integral bloqueada ate o artefato final ser liberado de forma segura.",
    publicLinkLabel: "verifica.afere.com.br/c/9ac11f0b",
    metadataFields: [
      { label: "Laboratorio emissor", value: "Lab. Acme" },
      { label: "Equipamento", value: "BAL-021 Marte 20 kg" },
      { label: "Status", value: "Visualizacao bloqueada" },
      { label: "Revisao", value: "R0" },
      { label: "Data de emissao", value: "09/04/2026" },
    ],
    verificationSteps: [
      "Use o link publico apenas para verificar autenticidade minimizada.",
      "Aguarde a liberacao do viewer integral pelo laboratorio.",
      "Nao considere esta tela como substituta do PDF oficial.",
    ],
    equipmentScenarioId: "overdue-blocked",
    dashboardScenarioId: "overdue-blocked",
    publicVerifyScenarioId: "not-found",
  },
};

const SCENARIOS: Record<PortalCertificateScenarioId, ScenarioDefinition> = {
  "current-valid": {
    label: "Certificado valido",
    description: "O cliente visualiza o certificado autenticado, com hash e instrucoes de verificacao.",
    recommendedAction: "Usar o viewer autenticado para leitura integral e o QR para verificacao publica externa.",
    selectedCertificateId: "cert-00142",
    items: [
      {
        certificateId: "cert-00142",
        status: "ready",
        statusLabel: "Valido",
        recommendedAction: "Ler o certificado integral e manter o link publico para terceiros.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "ready" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "ready" },
          { key: "print_certificate", label: "Imprimir", status: "ready" },
        ],
        blockers: [],
        warnings: [],
      },
      {
        certificateId: "cert-00135-r1",
        status: "attention",
        statusLabel: "Reemitido",
        recommendedAction: "Conferir a indicacao de reemissao antes de compartilhar o documento.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "attention" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "ready" },
          { key: "print_certificate", label: "Imprimir", status: "attention" },
        ],
        blockers: [],
        warnings: ["Certificado reemitido aparece no mesmo recorte para comparacao."],
      },
    ],
  },
  "reissued-history": {
    label: "Reemissao rastreada",
    description: "O viewer destaca a reemissao controlada e orienta o cliente a conferir a ultima revisao.",
    recommendedAction: "Compartilhar apenas a revisao vigente e usar o QR para demonstrar a rastreabilidade.",
    selectedCertificateId: "cert-00135-r1",
    items: [
      {
        certificateId: "cert-00135-r1",
        status: "attention",
        statusLabel: "Reemitido",
        recommendedAction: "Conferir a revisao atual antes de imprimir ou compartilhar o documento.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "attention" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "ready" },
          { key: "print_certificate", label: "Imprimir", status: "attention" },
        ],
        blockers: [],
        warnings: ["Ha uma revisao anterior preservada apenas como historico."],
      },
      {
        certificateId: "cert-00142",
        status: "ready",
        statusLabel: "Valido",
        recommendedAction: "Certificado base do recorte permanece valido.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "ready" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "ready" },
          { key: "print_certificate", label: "Imprimir", status: "ready" },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
  "download-blocked": {
    label: "Visualizacao bloqueada",
    description: "O portal falha fechado quando a previa integral do certificado ainda nao pode ser exibida com seguranca.",
    recommendedAction: "Usar apenas a verificacao publica minimizada enquanto o viewer autenticado permanece bloqueado.",
    selectedCertificateId: "cert-00128",
    items: [
      {
        certificateId: "cert-00128",
        status: "blocked",
        statusLabel: "Visualizacao bloqueada",
        recommendedAction: "Aguardar liberacao segura do viewer integral.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "blocked" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "attention" },
          { key: "print_certificate", label: "Imprimir", status: "blocked" },
        ],
        blockers: ["Viewer integral ainda nao liberado para visualizacao autenticada."],
        warnings: ["A verificacao publica continua disponivel apenas com metadados minimos."],
      },
      {
        certificateId: "cert-00135-r1",
        status: "attention",
        statusLabel: "Reemitido",
        recommendedAction: "Conferir a revisao atual se precisar de evidencia imediata.",
        actions: [
          { key: "download_pdf", label: "Baixar PDF", status: "attention" },
          { key: "share_public_link", label: "Compartilhar link publico", status: "ready" },
          { key: "print_certificate", label: "Imprimir", status: "attention" },
        ],
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: PortalCertificateScenarioId = "current-valid";

export function listPortalCertificateScenarios(): PortalCertificateScenario[] {
  return (Object.keys(SCENARIOS) as PortalCertificateScenarioId[]).map((scenarioId) =>
    resolvePortalCertificateScenario(scenarioId),
  );
}

export function resolvePortalCertificateScenario(
  scenarioId?: string,
  certificateId?: string,
): PortalCertificateScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildListItem);
  const selectedItem =
    items.find((item) => item.certificateId === certificateId) ??
    items.find((item) => item.certificateId === definition.selectedCertificateId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_portal_certificate_items");
  }

  const detail = buildDetail(definition, selectedItem.certificateId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, items, detail),
    selectedCertificateId: selectedItem.certificateId,
    items,
    detail,
  };
}

export function buildPortalCertificateCatalog(
  scenarioId?: string,
  certificateId?: string,
): PortalCertificateCatalog {
  const selectedScenario = resolvePortalCertificateScenario(scenarioId, certificateId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listPortalCertificateScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildListItem(state: ScenarioCertificateState): PortalCertificateListItem {
  const record = getRecord(state.certificateId);

  return {
    certificateId: record.certificateId,
    certificateNumber: record.certificateNumber,
    equipmentLabel: record.equipmentLabel,
    issuedAtLabel: record.issuedAtLabel,
    statusLabel: state.statusLabel,
    verifyScenarioId: record.publicVerifyScenarioId,
    status: state.status,
  };
}

function buildDetail(
  definition: ScenarioDefinition,
  certificateId: string,
): PortalCertificateDetail {
  const record = getRecord(certificateId);
  const state = getState(definition, certificateId);

  return {
    certificateId: record.certificateId,
    title: `${record.certificateNumber} - ${record.equipmentLabel}`,
    status: state.status,
    hashLabel: record.hashLabel,
    signatureLabel: record.signatureLabel,
    viewerLabel: record.viewerLabel,
    publicLinkLabel: record.publicLinkLabel,
    recommendedAction: state.recommendedAction,
    metadataFields: record.metadataFields,
    actions: state.actions,
    verificationSteps: record.verificationSteps,
    blockers: state.blockers,
    warnings: state.warnings,
    equipmentId: record.equipmentId,
    equipmentScenarioId: record.equipmentScenarioId,
    dashboardScenarioId: record.dashboardScenarioId,
    publicVerifyScenarioId: record.publicVerifyScenarioId,
  };
}

function buildSummary(
  recommendedAction: string,
  items: PortalCertificateListItem[],
  detail: PortalCertificateDetail,
): PortalCertificateScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Visualizador do certificado pronto para consulta"
        : detail.status === "attention"
          ? "Reemissao rastreada exige leitura cuidadosa"
          : "Visualizacao integral bloqueada em fail-closed",
    totalCertificates: items.length,
    readyCount: items.filter((item) => item.status === "ready").length,
    attentionCount: items.filter((item) => item.status === "attention").length,
    blockedCount: items.filter((item) => item.status === "blocked").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getRecord(certificateId: string): CertificateRecord {
  const record = CERTIFICATES[certificateId];

  if (!record) {
    throw new Error(`missing_portal_certificate_record:${certificateId}`);
  }

  return record;
}

function getState(
  definition: ScenarioDefinition,
  certificateId: string,
): ScenarioCertificateState {
  const state = definition.items.find((item) => item.certificateId === certificateId);

  if (!state) {
    throw new Error(`missing_portal_certificate_state:${certificateId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): PortalCertificateScenarioId {
  return isPortalCertificateScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isPortalCertificateScenarioId(value: string | undefined): value is PortalCertificateScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
