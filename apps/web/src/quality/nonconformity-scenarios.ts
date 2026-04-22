import type {
  NonconformityRegistryCatalog,
  NonconformityRegistryScenario,
} from "@afere/contracts";

export interface NonconformityRegistryScenarioViewModel extends NonconformityRegistryScenario {
  selectedNc: NonconformityRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface NonconformityRegistryCatalogViewModel {
  selectedScenario: NonconformityRegistryScenarioViewModel;
  scenarios: NonconformityRegistryScenarioViewModel[];
}

export function buildNonconformityCatalogView(
  catalog: NonconformityRegistryCatalog,
): NonconformityRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedNc =
      scenario.items.find((item) => item.ncId === scenario.selectedNcId) ??
      scenario.items[0];

    if (!selectedNc) {
      throw new Error("missing_nonconformity_items");
    }

    return {
      ...scenario,
      selectedNc,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.closedCount} NC(s) encerrada(s) e historico disponivel`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openCount} NC(s) aberta(s) e acompanhamento em andamento`
            : `${scenario.summary.criticalCount} NC(s) critica(s) e fluxo bloqueado`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_nonconformity_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
