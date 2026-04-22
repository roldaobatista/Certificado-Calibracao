import type { PublicCertificateCatalog, PublicCertificateScenario } from "@afere/contracts";

import { buildPublicCertificatePageModel } from "./public-certificate-page";

export interface PublicCertificateScenarioViewModel extends PublicCertificateScenario {
  page: ReturnType<typeof buildPublicCertificatePageModel>;
}

export interface PublicCertificateCatalogViewModel {
  selectedScenario: PublicCertificateScenarioViewModel;
  scenarios: PublicCertificateScenarioViewModel[];
}

export function buildPublicCertificateCatalogView(
  catalog: PublicCertificateCatalog,
): PublicCertificateCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    page: buildPublicCertificatePageModel(scenario.result),
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_public_certificate_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
