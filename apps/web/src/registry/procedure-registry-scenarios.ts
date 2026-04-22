import type {
  ProcedureRegistryCatalog,
  ProcedureRegistryScenario,
} from "@afere/contracts";

export interface ProcedureRegistryScenarioViewModel extends ProcedureRegistryScenario {
  selectedProcedure: ProcedureRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface ProcedureRegistryCatalogViewModel {
  selectedScenario: ProcedureRegistryScenarioViewModel;
  scenarios: ProcedureRegistryScenarioViewModel[];
}

export function buildProcedureRegistryCatalogView(
  catalog: ProcedureRegistryCatalog,
): ProcedureRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedProcedure =
      scenario.items.find((item) => item.procedureId === scenario.selectedProcedureId) ??
      scenario.items[0];

    if (!selectedProcedure) {
      throw new Error("missing_procedure_registry_items");
    }

    return {
      ...scenario,
      selectedProcedure,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.activeCount} procedimento(s) vigente(s) e ${scenario.summary.attentionCount} em vigilancia`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} procedimento(s) em atencao e ${scenario.summary.obsoleteCount} obsoleto(s) visivel(is)`
            : `${scenario.summary.obsoleteCount} revisao(oes) obsoleta(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_procedure_registry_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
