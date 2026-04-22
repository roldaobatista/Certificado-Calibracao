import type { EmissionDryRunCatalog, EmissionDryRunScenario } from "@afere/contracts";

import {
  buildEmissionDryRunSummary,
  type EmissionDryRunSummaryViewModel,
} from "./emission-dry-run-summary";

export interface EmissionDryRunScenarioViewModel extends EmissionDryRunScenario {
  summary: EmissionDryRunSummaryViewModel;
}

export interface EmissionDryRunCatalogViewModel {
  selectedScenario: EmissionDryRunScenarioViewModel;
  scenarios: EmissionDryRunScenarioViewModel[];
}

export function buildEmissionDryRunCatalogView(
  catalog: EmissionDryRunCatalog,
): EmissionDryRunCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summary: buildEmissionDryRunSummary(scenario.result),
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_emission_dry_run_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
