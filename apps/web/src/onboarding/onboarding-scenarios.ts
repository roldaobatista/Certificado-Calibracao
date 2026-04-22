import type {
  OnboardingCatalog,
  OnboardingScenario,
  OnboardingWizardSummary,
} from "@afere/contracts";

import { buildOnboardingWizardSummary } from "./onboarding-wizard-summary";

export interface OnboardingScenarioViewModel extends OnboardingScenario {
  summary: OnboardingWizardSummary;
}

export interface OnboardingCatalogViewModel {
  selectedScenario: OnboardingScenarioViewModel;
  scenarios: OnboardingScenarioViewModel[];
}

export function buildOnboardingCatalogView(
  catalog: OnboardingCatalog,
): OnboardingCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summary: buildOnboardingWizardSummary(scenario.result),
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_onboarding_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
