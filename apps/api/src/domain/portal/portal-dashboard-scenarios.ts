import type {
  PortalDashboardCatalog,
  PortalDashboardScenario,
  PortalDashboardScenarioId,
} from "@afere/contracts";

type ScenarioDefinition = {
  label: string;
  description: string;
  summary: Omit<PortalDashboardScenario["summary"], "status">;
  expiringEquipments: PortalDashboardScenario["expiringEquipments"];
  recentCertificates: PortalDashboardScenario["recentCertificates"];
};

const SCENARIOS: Record<PortalDashboardScenarioId, ScenarioDefinition> = {
  "stable-portfolio": {
    label: "Carteira estavel",
    description: "O cliente acompanha a carteira ativa sem vencimentos imediatos no recorte atual.",
    summary: {
      clientName: "Joao das Neves",
      organizationName: "Lab. Acme",
      equipmentCount: 23,
      certificateCount: 142,
      expiringSoonCount: 0,
      overdueCount: 0,
      recommendedAction: "Manter o monitoramento periodico da carteira e acompanhar os certificados recentes.",
      blockers: [],
      warnings: [],
    },
    expiringEquipments: [],
    recentCertificates: [
      {
        certificateId: "cert-00142",
        certificateNumber: "CAL-1234/2026/00142",
        equipmentLabel: "BAL-007 Toledo Prix 3",
        issuedAtLabel: "19/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00141",
        certificateNumber: "CAL-1234/2026/00141",
        equipmentLabel: "BAL-012 Filizola 15 kg",
        issuedAtLabel: "18/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00140",
        certificateNumber: "CAL-1234/2026/00140",
        equipmentLabel: "BAL-015 Marte 50 kg",
        issuedAtLabel: "17/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "expiring-soon": {
    label: "Vencimentos proximos",
    description:
      "O portal destaca os equipamentos que vencem em breve para antecipar o pedido da proxima calibracao.",
    summary: {
      clientName: "Joao das Neves",
      organizationName: "Lab. Acme",
      equipmentCount: 23,
      certificateCount: 142,
      expiringSoonCount: 3,
      overdueCount: 0,
      recommendedAction: "Solicitar nova calibracao dos equipamentos que vencem nos proximos 30 dias.",
      blockers: [],
      warnings: [
        "Tres equipamentos vencem em ate 30 dias.",
        "Acompanhar agenda de coleta para evitar janela sem certificado vigente.",
      ],
    },
    expiringEquipments: [
      {
        equipmentId: "equipment-bal-007",
        tag: "BAL-007",
        description: "Toledo Prix 3",
        locationLabel: "Sala 12",
        lastCalibrationLabel: "18/04/2026",
        dueAtLabel: "18/05/2026",
        status: "attention",
      },
      {
        equipmentId: "equipment-bal-012",
        tag: "BAL-012",
        description: "Filizola 15 kg",
        locationLabel: "Setor C",
        lastCalibrationLabel: "24/02/2026",
        dueAtLabel: "24/05/2026",
        status: "attention",
      },
      {
        equipmentId: "equipment-bal-015",
        tag: "BAL-015",
        description: "Marte 50 kg",
        locationLabel: "Laboratorio B",
        lastCalibrationLabel: "28/02/2026",
        dueAtLabel: "28/05/2026",
        status: "attention",
      },
    ],
    recentCertificates: [
      {
        certificateId: "cert-00142",
        certificateNumber: "CAL-1234/2026/00142",
        equipmentLabel: "BAL-007 Toledo Prix 3",
        issuedAtLabel: "19/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00139",
        certificateNumber: "CAL-1234/2026/00139",
        equipmentLabel: "BAL-003 Urano Pop 30",
        issuedAtLabel: "16/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00138",
        certificateNumber: "CAL-1234/2026/00138",
        equipmentLabel: "BAL-002 Toledo Fit 6",
        issuedAtLabel: "15/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
    ],
  },
  "overdue-blocked": {
    label: "Equipamento vencido exige acao",
    description:
      "O portal destaca quando um equipamento ja ultrapassou a validade e a carteira exige acompanhamento imediato.",
    summary: {
      clientName: "Joao das Neves",
      organizationName: "Lab. Acme",
      equipmentCount: 23,
      certificateCount: 142,
      expiringSoonCount: 1,
      overdueCount: 1,
      recommendedAction: "Abrir atendimento e regularizar imediatamente o equipamento vencido antes do proximo uso critico.",
      blockers: ["BAL-019 sem calibracao valida no recorte atual."],
      warnings: ["Existe um certificado recente reemitido para conferencia adicional do cliente."],
    },
    expiringEquipments: [
      {
        equipmentId: "equipment-bal-019",
        tag: "BAL-019",
        description: "Toledo Prix 15",
        locationLabel: "Linha 3",
        lastCalibrationLabel: "10/10/2025",
        dueAtLabel: "10/04/2026",
        status: "blocked",
      },
      {
        equipmentId: "equipment-bal-021",
        tag: "BAL-021",
        description: "Marte 20 kg",
        locationLabel: "Recebimento",
        lastCalibrationLabel: "25/03/2026",
        dueAtLabel: "25/05/2026",
        status: "attention",
      },
    ],
    recentCertificates: [
      {
        certificateId: "cert-00135-r1",
        certificateNumber: "CAL-1234/2026/00135-R1",
        equipmentLabel: "BAL-019 Toledo Prix 15",
        issuedAtLabel: "14/04/2026",
        statusLabel: "Reemitido",
        verifyScenarioId: "reissued",
      },
      {
        certificateId: "cert-00134",
        certificateNumber: "CAL-1234/2026/00134",
        equipmentLabel: "BAL-021 Marte 20 kg",
        issuedAtLabel: "13/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
      {
        certificateId: "cert-00133",
        certificateNumber: "CAL-1234/2026/00133",
        equipmentLabel: "BAL-010 Filizola 6 kg",
        issuedAtLabel: "12/04/2026",
        statusLabel: "Aprovado",
        verifyScenarioId: "authentic",
      },
    ],
  },
};

const DEFAULT_SCENARIO: PortalDashboardScenarioId = "stable-portfolio";

export function listPortalDashboardScenarios(): PortalDashboardScenario[] {
  return (Object.keys(SCENARIOS) as PortalDashboardScenarioId[]).map((scenarioId) =>
    resolvePortalDashboardScenario(scenarioId),
  );
}

export function resolvePortalDashboardScenario(scenarioId?: string): PortalDashboardScenario {
  const definition = resolveDefinition(scenarioId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: {
      ...definition.summary,
      status:
        definition.summary.overdueCount > 0
          ? "blocked"
          : definition.summary.expiringSoonCount > 0
            ? "attention"
            : "ready",
    },
    expiringEquipments: definition.expiringEquipments,
    recentCertificates: definition.recentCertificates,
  };
}

export function buildPortalDashboardCatalog(scenarioId?: string): PortalDashboardCatalog {
  const selectedScenario = resolvePortalDashboardScenario(scenarioId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listPortalDashboardScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function resolveScenarioId(scenarioId?: string): PortalDashboardScenarioId {
  return isPortalDashboardScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isPortalDashboardScenarioId(value: string | undefined): value is PortalDashboardScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
