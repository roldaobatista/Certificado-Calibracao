import type {
  AuditTrailCatalog,
  AuditTrailScenario,
} from "@afere/contracts";

export interface AuditTrailScenarioViewModel extends AuditTrailScenario {
  selectedEvent: AuditTrailScenario["items"][number];
  summaryLabel: string;
}

export interface AuditTrailCatalogViewModel {
  selectedScenario: AuditTrailScenarioViewModel;
  scenarios: AuditTrailScenarioViewModel[];
}

export function buildAuditTrailCatalogView(
  catalog: AuditTrailCatalog,
): AuditTrailCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedEvent =
      scenario.items.find((item) => item.eventId === scenario.selectedEventId) ??
      scenario.items[0];

    if (!selectedEvent) {
      throw new Error("missing_audit_trail_items");
    }

    return {
      ...scenario,
      selectedEvent,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.totalEvents} evento(s) com cadeia integra e ${scenario.summary.criticalEvents} critico(s)`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.reissueEvents} evento(s) de reemissao e exportacao com ressalva`
            : `${scenario.summary.integrityFailures} falha(s) de integridade e exportacao bloqueada`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_audit_trail_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
