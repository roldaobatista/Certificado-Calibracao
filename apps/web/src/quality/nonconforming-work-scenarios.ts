import type {
  NonconformingWorkCatalog,
  NonconformingWorkScenario,
} from "@afere/contracts";

export interface NonconformingWorkScenarioViewModel extends NonconformingWorkScenario {
  selectedCase: NonconformingWorkScenario["items"][number];
  summaryLabel: string;
}

export interface NonconformingWorkCatalogViewModel {
  selectedScenario: NonconformingWorkScenarioViewModel;
  scenarios: NonconformingWorkScenarioViewModel[];
}

export function buildNonconformingWorkCatalogView(
  catalog: NonconformingWorkCatalog,
): NonconformingWorkCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedCase =
      scenario.items.find((item) => item.caseId === scenario.selectedCaseId) ??
      scenario.items[0];

    if (!selectedCase) {
      throw new Error("missing_nonconforming_work_items");
    }

    return {
      ...scenario,
      selectedCase,
      summaryLabel:
        scenario.summary.status === "ready"
          ? "Historico arquivado e liberacao formalizada"
          : scenario.summary.status === "attention"
            ? "Contencao preventiva ainda ativa"
            : "Liberacao e reemissao bloqueadas",
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_nonconforming_work_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
