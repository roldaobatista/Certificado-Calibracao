import type {
  StandardRegistryCatalog,
  StandardRegistryScenario,
} from "@afere/contracts";

export interface StandardRegistryScenarioViewModel extends StandardRegistryScenario {
  selectedStandard: StandardRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface StandardRegistryCatalogViewModel {
  selectedScenario: StandardRegistryScenarioViewModel;
  scenarios: StandardRegistryScenarioViewModel[];
}

export function buildStandardRegistryCatalogView(
  catalog: StandardRegistryCatalog,
): StandardRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedStandard =
      scenario.items.find((item) => item.standardId === scenario.selectedStandardId) ??
      scenario.items[0];

    if (!selectedStandard) {
      throw new Error("missing_standard_registry_items");
    }

    return {
      ...scenario,
      selectedStandard,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.activeCount} padrao(es) ativo(s) e ${scenario.summary.expiringSoonCount} em vigilancia preventiva`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.expiringSoonCount} padrao(es) em atencao e ${scenario.summary.expirationPanel[0]?.dueInLabel ?? "0d"} no painel de vencimento`
            : `${scenario.summary.expiredCount} padrao(es) bloqueado(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_standard_registry_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
