import type {
  QualityHubCatalog,
  QualityHubModule,
  QualityHubScenario,
} from "@afere/contracts";

export interface QualityHubScenarioViewModel extends QualityHubScenario {
  selectedModule: QualityHubModule;
  summaryLabel: string;
}

export interface QualityHubCatalogViewModel {
  selectedScenario: QualityHubScenarioViewModel;
  scenarios: QualityHubScenarioViewModel[];
}

export function buildQualityHubCatalogView(
  catalog: QualityHubCatalog,
): QualityHubCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedModule =
      scenario.modules.find((module) => module.key === scenario.selectedModuleKey) ??
      scenario.modules[0];

    if (!selectedModule) {
      throw new Error("missing_quality_hub_modules");
    }

    return {
      ...scenario,
      selectedModule,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.implementedModuleCount} modulo(s) ativos e ${scenario.summary.plannedModuleCount} planejado(s)`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openNonconformities} NC(s) aberta(s), ${scenario.summary.complaintCount} reclamacao(oes) e backlog explicito`
            : `${scenario.summary.blockers.length} bloqueio(s) critico(s) e ${scenario.summary.complaintCount} reclamacao(oes) abertas`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_quality_hub_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
