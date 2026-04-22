import type {
  InternalAuditCatalog,
  InternalAuditScenario,
} from "@afere/contracts";

export interface InternalAuditScenarioViewModel extends InternalAuditScenario {
  selectedCycle: InternalAuditScenario["cycles"][number];
  summaryLabel: string;
}

export interface InternalAuditCatalogViewModel {
  selectedScenario: InternalAuditScenarioViewModel;
  scenarios: InternalAuditScenarioViewModel[];
}

export function buildInternalAuditCatalogView(
  catalog: InternalAuditCatalog,
): InternalAuditCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedCycle =
      scenario.cycles.find((cycle) => cycle.cycleId === scenario.selectedCycleId) ??
      scenario.cycles[0];

    if (!selectedCycle) {
      throw new Error("missing_internal_audit_cycles");
    }

    return {
      ...scenario,
      selectedCycle,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.plannedCycleCount} ciclo(s) no programa e sem achado aberto`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openFindingCount} achado(s) em follow-up`
            : "Auditoria extraordinaria pendente",
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ??
    scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_internal_audit_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
