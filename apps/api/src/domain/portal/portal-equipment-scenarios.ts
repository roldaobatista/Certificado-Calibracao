import type {
  PortalEquipmentCatalog,
  PortalEquipmentCertificateHistoryItem,
  PortalEquipmentDetail,
  PortalEquipmentListItem,
  PortalEquipmentScenario,
  PortalEquipmentScenarioId,
} from "@afere/contracts";

type EquipmentRecord = {
  equipmentId: string;
  tag: string;
  description: string;
  manufacturerLabel: string;
  modelLabel: string;
  serialLabel: string;
  capacityClassLabel: string;
  locationLabel: string;
  certificateHistory: PortalEquipmentCertificateHistoryItem[];
};

type ScenarioEquipmentState = {
  equipmentId: string;
  lastCalibrationLabel: string;
  nextDueLabel: string;
  status: PortalEquipmentListItem["status"];
  recommendedAction: string;
  blockers: string[];
  warnings: string[];
};

type ScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  items: ScenarioEquipmentState[];
  selectedEquipmentId: string;
};

const EQUIPMENTS: Record<string, EquipmentRecord> = {
  "equipment-bal-007": {
    equipmentId: "equipment-bal-007",
    tag: "BAL-007",
    description: "Toledo Prix 3",
    manufacturerLabel: "Toledo",
    modelLabel: "Prix 3",
    serialLabel: "9087654",
    capacityClassLabel: "3 kg / 0,5 g / Classe III",
    locationLabel: "Sala 12 - Sao Paulo",
    certificateHistory: [
      {
        certificateId: "cert-00142",
        issuedAtLabel: "19/04/2026",
        certificateNumber: "CAL-1234/2026/00142",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,15 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00321",
        issuedAtLabel: "18/10/2025",
        certificateNumber: "CAL-1234/2025/00321",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,15 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00102",
        issuedAtLabel: "22/04/2025",
        certificateNumber: "CAL-1234/2025/00102",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,16 g",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "equipment-bal-012": {
    equipmentId: "equipment-bal-012",
    tag: "BAL-012",
    description: "Filizola 15 kg",
    manufacturerLabel: "Filizola",
    modelLabel: "15 kg",
    serialLabel: "FZ150221",
    capacityClassLabel: "15 kg / 5 g / Classe III",
    locationLabel: "Setor C - Sao Paulo",
    certificateHistory: [
      {
        certificateId: "cert-00084",
        issuedAtLabel: "24/02/2026",
        certificateNumber: "CAL-1234/2026/00084",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,50 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00251",
        issuedAtLabel: "22/08/2025",
        certificateNumber: "CAL-1234/2025/00251",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,51 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00044",
        issuedAtLabel: "24/02/2025",
        certificateNumber: "CAL-1234/2025/00044",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,52 g",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "equipment-bal-015": {
    equipmentId: "equipment-bal-015",
    tag: "BAL-015",
    description: "Marte 50 kg",
    manufacturerLabel: "Marte",
    modelLabel: "50 kg",
    serialLabel: "MT500998",
    capacityClassLabel: "50 kg / 10 g / Classe III",
    locationLabel: "Laboratorio B - Sao Paulo",
    certificateHistory: [
      {
        certificateId: "cert-00090",
        issuedAtLabel: "28/02/2026",
        certificateNumber: "CAL-1234/2026/00090",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,80 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00262",
        issuedAtLabel: "28/08/2025",
        certificateNumber: "CAL-1234/2025/00262",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,82 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00050",
        issuedAtLabel: "28/02/2025",
        certificateNumber: "CAL-1234/2025/00050",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,83 g",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "equipment-bal-019": {
    equipmentId: "equipment-bal-019",
    tag: "BAL-019",
    description: "Toledo Prix 15",
    manufacturerLabel: "Toledo",
    modelLabel: "Prix 15",
    serialLabel: "TP150077",
    capacityClassLabel: "15 kg / 5 g / Classe III",
    locationLabel: "Linha 3 - Sao Paulo",
    certificateHistory: [
      {
        certificateId: "cert-00135-r1",
        issuedAtLabel: "14/04/2026",
        certificateNumber: "CAL-1234/2026/00135-R1",
        resultLabel: "Reemitido",
        uncertaintyLabel: "+/-0,47 g",
        verifyScenarioId: "reissued",
      },
      {
        certificateId: "cert-00298",
        issuedAtLabel: "10/10/2025",
        certificateNumber: "CAL-1234/2025/00298",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,48 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00088",
        issuedAtLabel: "11/04/2025",
        certificateNumber: "CAL-1234/2025/00088",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,49 g",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "equipment-bal-021": {
    equipmentId: "equipment-bal-021",
    tag: "BAL-021",
    description: "Marte 20 kg",
    manufacturerLabel: "Marte",
    modelLabel: "20 kg",
    serialLabel: "MT201122",
    capacityClassLabel: "20 kg / 5 g / Classe III",
    locationLabel: "Recebimento - Sao Paulo",
    certificateHistory: [
      {
        certificateId: "cert-00134",
        issuedAtLabel: "13/04/2026",
        certificateNumber: "CAL-1234/2026/00134",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,42 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00302",
        issuedAtLabel: "13/10/2025",
        certificateNumber: "CAL-1234/2025/00302",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,43 g",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00091",
        issuedAtLabel: "13/04/2025",
        certificateNumber: "CAL-1234/2025/00091",
        resultLabel: "Aprovado",
        uncertaintyLabel: "+/-0,44 g",
        verifyScenarioId: "authentic",
      },
    ],
  },
};

const SCENARIOS: Record<PortalEquipmentScenarioId, ScenarioDefinition> = {
  "stable-portfolio": {
    label: "Carteira estavel",
    description: "A lista do cliente permanece saudavel e sem vencimentos imediatos.",
    recommendedAction: "Manter o acompanhamento periodico da carteira e consultar os certificados historicos quando necessario.",
    selectedEquipmentId: "equipment-bal-007",
    items: [
      {
        equipmentId: "equipment-bal-007",
        lastCalibrationLabel: "18/04/2026",
        nextDueLabel: "18/10/2026",
        status: "ready",
        recommendedAction: "Acompanhar a carteira historica.",
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-bal-012",
        lastCalibrationLabel: "24/02/2026",
        nextDueLabel: "24/08/2026",
        status: "ready",
        recommendedAction: "Manter monitoramento padrao.",
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-bal-015",
        lastCalibrationLabel: "28/02/2026",
        nextDueLabel: "28/08/2026",
        status: "ready",
        recommendedAction: "Manter monitoramento padrao.",
        blockers: [],
        warnings: [],
      },
    ],
  },
  "expiring-soon": {
    label: "Vencimentos proximos",
    description: "A lista destaca os equipamentos que vencem nos proximos 30 dias.",
    recommendedAction: "Priorizar o agendamento da proxima calibracao para os itens em atencao.",
    selectedEquipmentId: "equipment-bal-012",
    items: [
      {
        equipmentId: "equipment-bal-007",
        lastCalibrationLabel: "18/04/2026",
        nextDueLabel: "18/05/2026",
        status: "attention",
        recommendedAction: "Solicitar nova calibracao.",
        blockers: [],
        warnings: ["Vence em menos de 30 dias."],
      },
      {
        equipmentId: "equipment-bal-012",
        lastCalibrationLabel: "24/02/2026",
        nextDueLabel: "24/05/2026",
        status: "attention",
        recommendedAction: "Agendar coleta preventiva.",
        blockers: [],
        warnings: ["Vence em menos de 30 dias."],
      },
      {
        equipmentId: "equipment-bal-015",
        lastCalibrationLabel: "28/02/2026",
        nextDueLabel: "28/05/2026",
        status: "attention",
        recommendedAction: "Agendar coleta preventiva.",
        blockers: [],
        warnings: ["Vence em menos de 30 dias."],
      },
    ],
  },
  "overdue-blocked": {
    label: "Equipamento vencido exige acao",
    description: "A lista evidencia quando um item ja perdeu a validade no recorte atual.",
    recommendedAction: "Interromper o uso critico do item vencido e alinhar a regularizacao com o laboratorio.",
    selectedEquipmentId: "equipment-bal-019",
    items: [
      {
        equipmentId: "equipment-bal-019",
        lastCalibrationLabel: "10/10/2025",
        nextDueLabel: "10/04/2026",
        status: "blocked",
        recommendedAction: "Regularizar imediatamente o equipamento vencido.",
        blockers: ["Equipamento sem calibracao valida no recorte atual."],
        warnings: ["Ultimo certificado foi reemitido e merece conferencia adicional."],
      },
      {
        equipmentId: "equipment-bal-021",
        lastCalibrationLabel: "25/03/2026",
        nextDueLabel: "25/05/2026",
        status: "attention",
        recommendedAction: "Programar a proxima calibracao.",
        blockers: [],
        warnings: ["Vence em menos de 30 dias."],
      },
    ],
  },
};

const DEFAULT_SCENARIO: PortalEquipmentScenarioId = "stable-portfolio";

export function listPortalEquipmentScenarios(): PortalEquipmentScenario[] {
  return (Object.keys(SCENARIOS) as PortalEquipmentScenarioId[]).map((scenarioId) =>
    resolvePortalEquipmentScenario(scenarioId),
  );
}

export function resolvePortalEquipmentScenario(
  scenarioId?: string,
  equipmentId?: string,
): PortalEquipmentScenario {
  const definition = resolveDefinition(scenarioId);
  const items = definition.items.map(buildListItem);
  const selectedItem =
    items.find((item) => item.equipmentId === equipmentId) ??
    items.find((item) => item.equipmentId === definition.selectedEquipmentId) ??
    items[0];

  if (!selectedItem) {
    throw new Error("missing_portal_equipment_items");
  }

  const detail = buildDetail(definition, selectedItem.equipmentId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition.recommendedAction, items, detail),
    selectedEquipmentId: selectedItem.equipmentId,
    items,
    detail,
  };
}

export function buildPortalEquipmentCatalog(
  scenarioId?: string,
  equipmentId?: string,
): PortalEquipmentCatalog {
  const selectedScenario = resolvePortalEquipmentScenario(scenarioId, equipmentId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listPortalEquipmentScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildListItem(state: ScenarioEquipmentState): PortalEquipmentListItem {
  const record = getRecord(state.equipmentId);

  return {
    equipmentId: record.equipmentId,
    tag: record.tag,
    description: record.description,
    manufacturerModelLabel: `${record.manufacturerLabel} ${record.modelLabel}`,
    locationLabel: record.locationLabel,
    lastCalibrationLabel: state.lastCalibrationLabel,
    nextDueLabel: state.nextDueLabel,
    status: state.status,
  };
}

function buildDetail(
  definition: ScenarioDefinition,
  equipmentId: string,
): PortalEquipmentDetail {
  const record = getRecord(equipmentId);
  const state = getState(definition, equipmentId);

  return {
    equipmentId: record.equipmentId,
    title: `${record.tag} - ${record.description}`,
    status: state.status,
    manufacturerLabel: record.manufacturerLabel,
    modelLabel: record.modelLabel,
    serialLabel: record.serialLabel,
    capacityClassLabel: record.capacityClassLabel,
    locationLabel: record.locationLabel,
    recommendedAction: state.recommendedAction,
    blockers: state.blockers,
    warnings: state.warnings,
    certificateHistory: record.certificateHistory,
  };
}

function buildSummary(
  recommendedAction: string,
  items: PortalEquipmentListItem[],
  detail: PortalEquipmentDetail,
): PortalEquipmentScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Carteira do cliente pronta para consulta"
        : detail.status === "attention"
          ? "Carteira do cliente com vencimentos proximos"
          : "Equipamento vencido bloqueia a carteira selecionada",
    equipmentCount: items.length,
    attentionCount: items.filter((item) => item.status === "attention").length,
    blockedCount: items.filter((item) => item.status === "blocked").length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function getRecord(equipmentId: string): EquipmentRecord {
  const record = EQUIPMENTS[equipmentId];

  if (!record) {
    throw new Error(`missing_portal_equipment_record:${equipmentId}`);
  }

  return record;
}

function getState(
  definition: ScenarioDefinition,
  equipmentId: string,
): ScenarioEquipmentState {
  const state = definition.items.find((item) => item.equipmentId === equipmentId);

  if (!state) {
    throw new Error(`missing_portal_equipment_state:${equipmentId}`);
  }

  return state;
}

function resolveScenarioId(scenarioId?: string): PortalEquipmentScenarioId {
  return isPortalEquipmentScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isPortalEquipmentScenarioId(value: string | undefined): value is PortalEquipmentScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
