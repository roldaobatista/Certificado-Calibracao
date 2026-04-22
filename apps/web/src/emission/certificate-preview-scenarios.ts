import type { CertificatePreviewCatalog, CertificatePreviewScenario } from "@afere/contracts";

export interface CertificatePreviewScenarioViewModel extends CertificatePreviewScenario {
  summaryLabel: string;
  returnStepLabel: string;
}

export interface CertificatePreviewCatalogViewModel {
  selectedScenario: CertificatePreviewScenarioViewModel;
  scenarios: CertificatePreviewScenarioViewModel[];
}

export function buildCertificatePreviewCatalogView(
  catalog: CertificatePreviewCatalog,
): CertificatePreviewCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summaryLabel:
      scenario.result.status === "ready"
        ? `${scenario.result.sections.length} secao(oes) prontas para conferencia visual`
        : `${scenario.result.blockers.length} bloqueio(s) ativos na previa`,
    returnStepLabel: scenario.result.suggestedReturnStep
      ? `Voltar ao passo ${scenario.result.suggestedReturnStep}`
      : "Nenhum retorno corretivo sugerido",
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_certificate_preview_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
