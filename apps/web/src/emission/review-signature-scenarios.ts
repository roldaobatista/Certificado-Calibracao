import type { ReviewSignatureCatalog, ReviewSignatureScenario } from "@afere/contracts";

import {
  buildReviewSignatureSummary,
  type ReviewSignatureSummaryViewModel,
} from "./review-signature-summary";

export interface ReviewSignatureScenarioViewModel extends ReviewSignatureScenario {
  summary: ReviewSignatureSummaryViewModel;
}

export interface ReviewSignatureCatalogViewModel {
  selectedScenario: ReviewSignatureScenarioViewModel;
  scenarios: ReviewSignatureScenarioViewModel[];
}

export function buildReviewSignatureCatalogView(
  catalog: ReviewSignatureCatalog,
): ReviewSignatureCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summary: buildReviewSignatureSummary(scenario.result),
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_review_signature_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
