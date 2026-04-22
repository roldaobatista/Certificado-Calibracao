import type {
  SelfSignupCatalog,
  SelfSignupChecklistViewModel,
  SelfSignupScenario,
} from "@afere/contracts";

import { buildSelfSignupChecklistViewModelFromPolicy } from "./self-signup-checklist";

export interface SelfSignupScenarioViewModel extends SelfSignupScenario {
  viewModel: SelfSignupChecklistViewModel;
}

export interface SelfSignupCatalogViewModel {
  selectedScenario: SelfSignupScenarioViewModel;
  scenarios: SelfSignupScenarioViewModel[];
}

export function buildSelfSignupCatalogView(
  catalog: SelfSignupCatalog,
): SelfSignupCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    viewModel: buildSelfSignupChecklistViewModelFromPolicy(scenario.result),
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_self_signup_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
