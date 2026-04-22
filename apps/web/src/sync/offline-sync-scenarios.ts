import type { OfflineSyncCatalog, OfflineSyncScenario } from "@afere/contracts";

export interface OfflineSyncScenarioViewModel extends OfflineSyncScenario {
  selectedOutboxItem: OfflineSyncScenario["outboxItems"][number];
  selectedConflict: OfflineSyncScenario["conflicts"][number];
  summaryLabel: string;
}

export interface OfflineSyncCatalogViewModel {
  selectedScenario: OfflineSyncScenarioViewModel;
  scenarios: OfflineSyncScenarioViewModel[];
}

export function buildOfflineSyncCatalogView(
  catalog: OfflineSyncCatalog,
): OfflineSyncCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedOutboxItem =
      scenario.outboxItems.find((item) => item.itemId === scenario.selectedOutboxItemId) ??
      scenario.outboxItems[0];
    if (!selectedOutboxItem) {
      throw new Error("missing_offline_sync_outbox_items");
    }

    const selectedConflict =
      scenario.conflicts.find((item) => item.conflictId === scenario.selectedConflictId) ??
      scenario.conflicts[0];
    if (!selectedConflict) {
      throw new Error("missing_offline_sync_conflicts");
    }

    return {
      ...scenario,
      selectedOutboxItem,
      selectedConflict,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.resolvedLast24h} resolvido(s) nas ultimas 24h e nenhuma OS bloqueada`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openConflictCount} conflito(s) aberto(s) e ${scenario.summary.blockedWorkOrders} OS bloqueada(s)`
            : `${scenario.summary.escalatedConflictCount} conflito(s) em escala regulatoria`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_offline_sync_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
