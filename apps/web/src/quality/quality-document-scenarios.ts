import type {
  QualityDocumentRegistryCatalog,
  QualityDocumentRegistryScenario,
} from "@afere/contracts";

export interface QualityDocumentRegistryScenarioViewModel
  extends QualityDocumentRegistryScenario {
  selectedDocument: QualityDocumentRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface QualityDocumentRegistryCatalogViewModel {
  selectedScenario: QualityDocumentRegistryScenarioViewModel;
  scenarios: QualityDocumentRegistryScenarioViewModel[];
}

export function buildQualityDocumentCatalogView(
  catalog: QualityDocumentRegistryCatalog,
): QualityDocumentRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedDocument =
      scenario.items.find((item) => item.documentId === scenario.selectedDocumentId) ??
      scenario.items[0];

    if (!selectedDocument) {
      throw new Error("missing_quality_document_items");
    }

    return {
      ...scenario,
      selectedDocument,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.activeCount} documento(s) vigente(s) e acervo rastreavel`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} documento(s) em revisao e ${scenario.summary.obsoleteCount} obsoleto(s) controlado(s)`
            : `${scenario.summary.obsoleteCount} revisao(oes) obsoleta(s) e uso bloqueado no recorte`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ??
    scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_quality_document_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
