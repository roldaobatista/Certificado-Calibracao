import type { EmissionWorkspaceCatalog, EmissionWorkspaceScenario } from "@afere/contracts";

export interface EmissionWorkspaceScenarioViewModel extends EmissionWorkspaceScenario {
  summaryLabel: string;
}

export interface EmissionWorkspaceCatalogViewModel {
  selectedScenario: EmissionWorkspaceScenarioViewModel;
  scenarios: EmissionWorkspaceScenarioViewModel[];
}

export function buildEmissionWorkspaceCatalogView(
  catalog: EmissionWorkspaceCatalog,
): EmissionWorkspaceCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summaryLabel:
      scenario.summary.status === "ready"
        ? `${scenario.summary.readyModules} modulo(s) prontos e nenhuma pendencia critica`
        : scenario.summary.status === "attention"
          ? `${scenario.summary.attentionModules} modulo(s) em atencao preventiva`
          : `${scenario.summary.blockedModules} modulo(s) bloqueados e ${scenario.summary.blockers.length} bloqueio(s) consolidado(s)`,
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_emission_workspace_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
