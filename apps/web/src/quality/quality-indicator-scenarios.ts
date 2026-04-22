import type {
  QualityIndicatorRegistryCatalog,
  QualityIndicatorRegistryScenario,
} from "@afere/contracts";

export interface QualityIndicatorRegistryScenarioViewModel
  extends QualityIndicatorRegistryScenario {
  selectedIndicator: QualityIndicatorRegistryScenario["indicators"][number];
  summaryLabel: string;
}

export interface QualityIndicatorRegistryCatalogViewModel {
  selectedScenario: QualityIndicatorRegistryScenarioViewModel;
  scenarios: QualityIndicatorRegistryScenarioViewModel[];
}

export function buildQualityIndicatorCatalogView(
  catalog: QualityIndicatorRegistryCatalog,
): QualityIndicatorRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedIndicator =
      scenario.indicators.find((item) => item.indicatorId === scenario.selectedIndicatorId) ??
      scenario.indicators[0];

    if (!selectedIndicator) {
      throw new Error("missing_quality_indicator_items");
    }

    return {
      ...scenario,
      selectedIndicator,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.indicatorCount} indicador(es) dentro da meta`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} alerta(s) preventivo(s) no painel`
            : `${scenario.summary.blockedCount} indicador(es) em deriva critica`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ??
    scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_quality_indicator_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
