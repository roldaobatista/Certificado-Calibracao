import {
  evaluateStandardEligibility,
  type StandardEligibilityDecision,
} from "@afere/normative-rules";
import type {
  EmissionDryRunScenarioId,
  RegistryOperationalStatus,
  RegistryScenarioId,
  ServiceOrderReviewScenarioId,
  StandardCalibrationHistoryEntry,
  StandardDetail,
  StandardExpirationMarker,
  StandardListItem,
  StandardRecentWorkOrder,
  StandardRegistryCatalog,
  StandardRegistryScenario,
  StandardRegistryScenarioId,
} from "@afere/contracts";

type StandardRecord = {
  standardId: string;
  title: string;
  markerLabel: string;
  kindLabel: string;
  nominalClassLabel: string;
  sourceLabel: string;
  certificateLabel: string;
  manufacturerLabel: string;
  modelLabel: string;
  serialNumberLabel: string;
  nominalValueLabel: string;
  classLabel: string;
  usageRangeLabel: string;
  uncertaintyLabel: string;
  correctionFactorLabel: string;
  history: StandardCalibrationHistoryEntry[];
  recentWorkOrders: StandardRecentWorkOrder[];
  registryScenarioId?: RegistryScenarioId;
  selectedEquipmentId?: string;
  serviceOrderScenarioId?: ServiceOrderReviewScenarioId;
  reviewItemId?: string;
  dryRunScenarioId?: EmissionDryRunScenarioId;
};

type ScenarioStandardState = {
  standardId: string;
  calibrationDate: string;
  hasValidCertificate: boolean;
  certificateValidUntil?: string;
  measurementValue: number;
  applicableRange: {
    minimum: number;
    maximum: number;
  };
  blockers: string[];
  warnings: string[];
};

type StandardRegistryScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedStandardId: string;
  standards: ScenarioStandardState[];
};

const TODAY = "2026-04-22";

const STANDARD_RECORDS: Record<string, StandardRecord> = {
  "standard-001": {
    standardId: "standard-001",
    title: "PESO-001 · Peso padrão 1 kg · classe F1",
    markerLabel: "PESO-001",
    kindLabel: "Peso",
    nominalClassLabel: "1 kg · F1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/081",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M1K",
    serialNumberLabel: "9-22-101",
    nominalValueLabel: "1,000 kg",
    classLabel: "F1",
    usageRangeLabel: "Cargas ate 1 kg",
    uncertaintyLabel: "+/- 8 mg",
    correctionFactorLabel: "+0,001 g",
    history: [
      {
        calibratedAtLabel: "12/08/2025",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/25/081",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 8 mg",
        validUntilLabel: "12/08/2026",
      },
      {
        calibratedAtLabel: "10/08/2024",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/24/063",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 8 mg",
        validUntilLabel: "10/08/2025",
      },
    ],
    recentWorkOrders: [
      { workOrderNumber: "OS-2026-00142", usedAtLabel: "19/04" },
      { workOrderNumber: "OS-2026-00139", usedAtLabel: "18/04" },
    ],
    registryScenarioId: "operational-ready",
    selectedEquipmentId: "equipment-001",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
    dryRunScenarioId: "type-b-ready",
  },
  "standard-002": {
    standardId: "standard-002",
    title: "PESO-002 · Peso padrão 2 kg · classe F1",
    markerLabel: "PESO-002",
    kindLabel: "Peso",
    nominalClassLabel: "2 kg · F1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/082",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M2K",
    serialNumberLabel: "9-22-102",
    nominalValueLabel: "2,000 kg",
    classLabel: "F1",
    usageRangeLabel: "Cargas ate 2 kg",
    uncertaintyLabel: "+/- 9 mg",
    correctionFactorLabel: "+0,002 g",
    history: [
      {
        calibratedAtLabel: "12/08/2025",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/25/082",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 9 mg",
        validUntilLabel: "12/08/2026",
      },
    ],
    recentWorkOrders: [
      { workOrderNumber: "OS-2026-00135", usedAtLabel: "17/04" },
    ],
    registryScenarioId: "operational-ready",
    selectedEquipmentId: "equipment-002",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00135",
    dryRunScenarioId: "type-b-ready",
  },
  "standard-005": {
    standardId: "standard-005",
    title: "PESO-005 · Peso padrão 5 kg · classe M1",
    markerLabel: "PESO-005",
    kindLabel: "Peso",
    nominalClassLabel: "5 kg · M1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/088",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M5K",
    serialNumberLabel: "9-22-115",
    nominalValueLabel: "5,000 kg",
    classLabel: "M1",
    usageRangeLabel: "Cargas ate 5 kg",
    uncertaintyLabel: "+/- 12 mg",
    correctionFactorLabel: "+0,003 g",
    history: [
      {
        calibratedAtLabel: "24/04/2025",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/25/088",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 12 mg",
        validUntilLabel: "24/04/2026",
      },
      {
        calibratedAtLabel: "14/04/2024",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/24/072",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 13 mg",
        validUntilLabel: "14/04/2025",
      },
      {
        calibratedAtLabel: "02/03/2023",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/23/053",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 13 mg",
        validUntilLabel: "02/03/2024",
      },
    ],
    recentWorkOrders: [
      { workOrderNumber: "OS-2026-00141", usedAtLabel: "19/04" },
      { workOrderNumber: "OS-2026-00138", usedAtLabel: "18/04" },
      { workOrderNumber: "OS-2026-00135", usedAtLabel: "17/04" },
    ],
    registryScenarioId: "certificate-attention",
    selectedEquipmentId: "equipment-003",
    serviceOrderScenarioId: "history-pending",
    reviewItemId: "os-2026-00141",
    dryRunScenarioId: "type-b-ready",
  },
  "standard-010": {
    standardId: "standard-010",
    title: "PESO-010 · Peso padrão 10 kg · classe M1",
    markerLabel: "PESO-010",
    kindLabel: "Peso",
    nominalClassLabel: "10 kg · M1",
    sourceLabel: "RBC-1234",
    certificateLabel: "1234/25/099",
    manufacturerLabel: "Coelmatic",
    modelLabel: "M10K",
    serialNumberLabel: "9-22-130",
    nominalValueLabel: "10,000 kg",
    classLabel: "M1",
    usageRangeLabel: "Cargas ate 10 kg",
    uncertaintyLabel: "+/- 18 mg",
    correctionFactorLabel: "+0,005 g",
    history: [
      {
        calibratedAtLabel: "02/04/2025",
        laboratoryLabel: "Lab Cal-1234",
        certificateLabel: "1234/25/099",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 18 mg",
        validUntilLabel: "02/04/2026",
      },
    ],
    recentWorkOrders: [
      { workOrderNumber: "OS-2026-00147", usedAtLabel: "19/04" },
    ],
    registryScenarioId: "registration-blocked",
    selectedEquipmentId: "equipment-004",
    serviceOrderScenarioId: "review-blocked",
    reviewItemId: "os-2026-00147",
    dryRunScenarioId: "type-c-blocked",
  },
  "standard-th003": {
    standardId: "standard-th003",
    title: "TH-003 · Termohigrometro de referencia",
    markerLabel: "TH-003",
    kindLabel: "Termohigr",
    nominalClassLabel: "-",
    sourceLabel: "RBC-9876",
    certificateLabel: "9876/25/044",
    manufacturerLabel: "Testo",
    modelLabel: "TH-610",
    serialNumberLabel: "TH-610-44",
    nominalValueLabel: "Referencia ambiental",
    classLabel: "Instrumento auxiliar",
    usageRangeLabel: "18C-25C / 30%-70%",
    uncertaintyLabel: "+/- 0,2 C / 1,5%",
    correctionFactorLabel: "Compensacao automatica ativa",
    history: [
      {
        calibratedAtLabel: "30/06/2025",
        laboratoryLabel: "Lab Cal-9876",
        certificateLabel: "9876/25/044",
        sourceLabel: "RBC",
        uncertaintyLabel: "+/- 0,2 C / 1,5%",
        validUntilLabel: "30/06/2026",
      },
    ],
    recentWorkOrders: [
      { workOrderNumber: "OS-2026-00142", usedAtLabel: "19/04" },
      { workOrderNumber: "OS-2026-00135", usedAtLabel: "17/04" },
    ],
    registryScenarioId: "operational-ready",
    selectedEquipmentId: "equipment-001",
    serviceOrderScenarioId: "review-ready",
    reviewItemId: "os-2026-00142",
    dryRunScenarioId: "type-b-ready",
  },
};

const SCENARIOS: Record<StandardRegistryScenarioId, StandardRegistryScenarioDefinition> = {
  "operational-ready": {
    label: "Padroes ativos e consistentes",
    description: "Recorte operacional com conjunto de padroes valido e sem vencimento critico na janela curta.",
    recommendedAction: "Seguir com a reserva normal dos padroes e monitorar o calendario preventivo.",
    selectedStandardId: "standard-001",
    standards: [
      {
        standardId: "standard-001",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 1,
        applicableRange: { minimum: 0, maximum: 1 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-002",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 2,
        applicableRange: { minimum: 0, maximum: 2 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-005",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-24",
        measurementValue: 5,
        applicableRange: { minimum: 0, maximum: 5 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-th003",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-06-30",
        measurementValue: 22.4,
        applicableRange: { minimum: 18, maximum: 25 },
        blockers: [],
        warnings: [],
      },
    ],
  },
  "expiration-attention": {
    label: "Padrao entrando em janela critica",
    description: "Recorte com padrao ainda elegivel, mas ja na janela de vencimento que exige acao preventiva imediata.",
    recommendedAction: "Solicitar nova calibracao do padrao selecionado antes da proxima janela operacional.",
    selectedStandardId: "standard-005",
    standards: [
      {
        standardId: "standard-001",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 1,
        applicableRange: { minimum: 0, maximum: 1 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-002",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 2,
        applicableRange: { minimum: 0, maximum: 2 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-005",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-04-24",
        measurementValue: 5,
        applicableRange: { minimum: 0, maximum: 5 },
        blockers: [],
        warnings: ["Padrao vence em 2 dias e deve ser retirado da agenda seguinte."],
      },
      {
        standardId: "standard-th003",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-06-30",
        measurementValue: 22.4,
        applicableRange: { minimum: 18, maximum: 25 },
        blockers: [],
        warnings: [],
      },
    ],
  },
  "expired-blocked": {
    label: "Padrao vencido e bloqueado",
    description: "Recorte com padrao expirado e inelegivel para nova reserva em OS ate nova calibracao.",
    recommendedAction: "Retirar o padrao expirado da operacao e anexar nova calibracao antes de reusar em emissao.",
    selectedStandardId: "standard-010",
    standards: [
      {
        standardId: "standard-001",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 1,
        applicableRange: { minimum: 0, maximum: 1 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-002",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-08-12",
        measurementValue: 2,
        applicableRange: { minimum: 0, maximum: 2 },
        blockers: [],
        warnings: [],
      },
      {
        standardId: "standard-010",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-04-02",
        measurementValue: 10,
        applicableRange: { minimum: 0, maximum: 10 },
        blockers: ["Padrao vencido deve sair da reserva antes da proxima OS."],
        warnings: [],
      },
      {
        standardId: "standard-th003",
        calibrationDate: TODAY,
        hasValidCertificate: true,
        certificateValidUntil: "2026-06-30",
        measurementValue: 22.4,
        applicableRange: { minimum: 18, maximum: 25 },
        blockers: [],
        warnings: [],
      },
    ],
  },
};

const DEFAULT_SCENARIO: StandardRegistryScenarioId = "operational-ready";

export function listStandardRegistryScenarios(): StandardRegistryScenario[] {
  return (Object.keys(SCENARIOS) as StandardRegistryScenarioId[]).map((scenarioId) =>
    resolveStandardRegistryScenario(scenarioId),
  );
}

export function resolveStandardRegistryScenario(
  scenarioId?: string,
  standardId?: string,
): StandardRegistryScenario {
  const definition = SCENARIOS[isStandardRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO];
  const items = definition.standards.map(buildStandardListItem);
  const selectedItem =
    items.find((item) => item.standardId === standardId) ??
    items.find((item) => item.standardId === definition.selectedStandardId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_standard_registry_items");
  }

  const detail = buildStandardDetail(definition, selectedItem.standardId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildStandardRegistrySummary(definition.recommendedAction, items, detail),
    selectedStandardId: selectedItem.standardId,
    items,
    detail,
  };
}

export function buildStandardRegistryCatalog(
  scenarioId?: string,
  standardId?: string,
): StandardRegistryCatalog {
  const selectedScenario = resolveStandardRegistryScenario(scenarioId, standardId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listStandardRegistryScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildStandardListItem(state: ScenarioStandardState): StandardListItem {
  const record = getStandardRecord(state.standardId);
  const evaluation = evaluate(state);

  return {
    standardId: record.standardId,
    kindLabel: record.kindLabel,
    nominalClassLabel: record.nominalClassLabel,
    sourceLabel: record.sourceLabel,
    certificateLabel: record.certificateLabel,
    validUntilLabel: state.certificateValidUntil ?? "Nao informada",
    status: resolveStatus(evaluation, state.certificateValidUntil),
  };
}

function buildStandardDetail(
  definition: StandardRegistryScenarioDefinition,
  standardId: string,
): StandardDetail {
  const state = getScenarioStandardState(definition, standardId);
  const record = getStandardRecord(standardId);
  const evaluation = evaluate(state);
  const status = resolveStatus(evaluation, state.certificateValidUntil);
  const blockers = uniqueStrings([
    ...state.blockers,
    ...evaluation.blockers.map(renderStandardBlocker),
  ]);
  const warnings = uniqueStrings([...state.warnings, ...evaluation.warnings]);
  const daysUntilExpiration = getDaysUntilExpiration(state.certificateValidUntil);

  return {
    standardId: record.standardId,
    title: record.title,
    status,
    noticeLabel: buildNoticeLabel(status, daysUntilExpiration),
    manufacturerLabel: record.manufacturerLabel,
    modelLabel: record.modelLabel,
    serialNumberLabel: record.serialNumberLabel,
    nominalValueLabel: record.nominalValueLabel,
    classLabel: record.classLabel,
    usageRangeLabel: record.usageRangeLabel,
    uncertaintyLabel: record.uncertaintyLabel,
    correctionFactorLabel: record.correctionFactorLabel,
    history: record.history,
    recentWorkOrders: record.recentWorkOrders,
    blockers,
    warnings,
    links: {
      registryScenarioId: record.registryScenarioId,
      selectedEquipmentId: record.selectedEquipmentId,
      serviceOrderScenarioId: record.serviceOrderScenarioId,
      reviewItemId: record.reviewItemId,
      dryRunScenarioId: record.dryRunScenarioId,
    },
  };
}

function buildStandardRegistrySummary(
  recommendedAction: string,
  items: StandardListItem[],
  detail: StandardDetail,
): StandardRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Padroes validos e disponiveis para reserva"
        : detail.status === "attention"
          ? "Padrao em janela critica de vencimento"
          : "Padrao bloqueado por elegibilidade ou validade",
    activeCount: items.filter((item) => item.status !== "blocked").length,
    expiringSoonCount: items.filter((item) => item.status === "attention").length,
    expiredCount: items.filter((item) => item.status === "blocked").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
    expirationPanel: items.map((item) => buildExpirationMarker(item)),
  };
}

function buildExpirationMarker(item: StandardListItem): StandardExpirationMarker {
  return {
    standardId: item.standardId,
    label: item.standardId.replace("standard-", "").toUpperCase(),
    dueInLabel: renderDueInLabel(item.validUntilLabel),
    status: item.status,
  };
}

function evaluate(state: ScenarioStandardState): StandardEligibilityDecision {
  return evaluateStandardEligibility({
    calibrationDate: state.calibrationDate,
    hasValidCertificate: state.hasValidCertificate,
    certificateValidUntil: state.certificateValidUntil,
    measurementValue: state.measurementValue,
    applicableRange: state.applicableRange,
  });
}

function resolveStatus(
  evaluation: StandardEligibilityDecision,
  certificateValidUntil: string | undefined,
): RegistryOperationalStatus {
  if (!evaluation.eligible) {
    return "blocked";
  }

  const daysUntilExpiration = getDaysUntilExpiration(certificateValidUntil);
  if (daysUntilExpiration !== null && daysUntilExpiration <= 30) {
    return "attention";
  }

  return "ready";
}

function buildNoticeLabel(
  status: RegistryOperationalStatus,
  daysUntilExpiration: number | null,
): string {
  if (status === "blocked") {
    return "Este padrao esta vencido ou inelegivel para uso.";
  }

  if (status === "attention" && daysUntilExpiration !== null) {
    return `Este padrao vence em ${daysUntilExpiration} dia(s).`;
  }

  return "Padrao valido e liberado para uso no recorte atual.";
}

function renderDueInLabel(validUntilLabel: string): string {
  const daysUntilExpiration = getDaysUntilExpiration(validUntilLabel);
  if (daysUntilExpiration === null) {
    return "validade desconhecida";
  }

  if (daysUntilExpiration < 0) {
    return `${Math.abs(daysUntilExpiration)}d vencido`;
  }

  return `${daysUntilExpiration}d`;
}

function getDaysUntilExpiration(validUntilLabel: string | undefined): number | null {
  if (typeof validUntilLabel !== "string" || validUntilLabel.trim().length === 0) {
    return null;
  }

  const today = Date.parse(`${TODAY}T00:00:00Z`);
  const validUntil = Date.parse(`${validUntilLabel}T00:00:00Z`);

  if (!Number.isFinite(today) || !Number.isFinite(validUntil)) {
    return null;
  }

  return Math.round((validUntil - today) / (24 * 60 * 60 * 1000));
}

function renderStandardBlocker(code: string): string {
  switch (code) {
    case "missing_valid_certificate":
      return "Padrao sem certificado valido";
    case "missing_certificate_validity":
      return "Validade do certificado ausente";
    case "expired_certificate":
      return "Certificado do padrao vencido";
    case "standard_out_of_applicable_range":
      return "Padrao fora da faixa aplicavel";
    case "missing_applicable_range":
      return "Faixa aplicavel ausente";
    case "missing_measurement_value":
      return "Valor de medicao ausente";
    case "invalid_calibration_date":
      return "Data de calibracao invalida";
    case "invalid_applicable_range":
      return "Faixa aplicavel invalida";
    default:
      return code;
  }
}

function getStandardRecord(standardId: string): StandardRecord {
  const record = STANDARD_RECORDS[standardId];
  if (!record) {
    throw new Error(`missing_standard_record:${standardId}`);
  }

  return record;
}

function getScenarioStandardState(
  definition: StandardRegistryScenarioDefinition,
  standardId: string,
): ScenarioStandardState {
  const state = definition.standards.find((item) => item.standardId === standardId);
  if (!state) {
    throw new Error(`missing_standard_state:${standardId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): StandardRegistryScenarioId {
  return isStandardRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function isStandardRegistryScenarioId(
  value: string | undefined,
): value is StandardRegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}
