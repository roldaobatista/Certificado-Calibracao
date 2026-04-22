import type { PortalDashboardCatalog, PortalDashboardScenario } from "@afere/contracts";

export interface PortalDashboardScenarioViewModel extends PortalDashboardScenario {
  summaryLabel: string;
}

export interface PortalDashboardCatalogViewModel {
  selectedScenario: PortalDashboardScenarioViewModel;
  scenarios: PortalDashboardScenarioViewModel[];
}

export function buildPortalDashboardCatalogView(
  catalog: PortalDashboardCatalog,
): PortalDashboardCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summaryLabel:
      scenario.summary.status === "ready"
        ? `${scenario.summary.equipmentCount} equipamento(s) ativos e carteira estavel`
        : scenario.summary.status === "attention"
          ? `${scenario.summary.expiringSoonCount} equipamento(s) vencendo em breve`
          : `${scenario.summary.overdueCount} equipamento(s) vencido(s) e acompanhamento obrigatorio`,
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_portal_dashboard_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
