import type {
  ServiceOrderReviewCatalog,
  ServiceOrderReviewScenario,
} from "@afere/contracts";

export interface ServiceOrderReviewScenarioViewModel extends ServiceOrderReviewScenario {
  summaryLabel: string;
  selectedItem: ServiceOrderReviewScenario["items"][number];
}

export interface ServiceOrderReviewCatalogViewModel {
  selectedScenario: ServiceOrderReviewScenarioViewModel;
  scenarios: ServiceOrderReviewScenarioViewModel[];
}

export function buildServiceOrderReviewCatalogView(
  catalog: ServiceOrderReviewCatalog,
): ServiceOrderReviewCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedItem =
      scenario.items.find((item) => item.itemId === scenario.selectedItemId) ?? scenario.items[0];

    if (!selectedItem) {
      throw new Error("missing_service_order_review_items");
    }

    return {
      ...scenario,
      selectedItem,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.awaitingReviewCount} OS aguardando revisao sem bloqueios criticos`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.awaitingReviewCount} OS aguardando revisao e ${scenario.summary.warnings.length} pendencia(s) complementar(es)`
            : `${scenario.summary.blockedCount} OS bloqueada(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_service_order_review_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
