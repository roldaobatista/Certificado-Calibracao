import type { SignatureQueueCatalog, SignatureQueueScenario } from "@afere/contracts";

export interface SignatureQueueScenarioViewModel extends SignatureQueueScenario {
  summaryLabel: string;
  selectedItem: SignatureQueueScenario["items"][number];
}

export interface SignatureQueueCatalogViewModel {
  selectedScenario: SignatureQueueScenarioViewModel;
  scenarios: SignatureQueueScenarioViewModel[];
}

export function buildSignatureQueueCatalogView(
  catalog: SignatureQueueCatalog,
): SignatureQueueCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedItem =
      scenario.items.find((item) => item.itemId === scenario.selectedItemId) ?? scenario.items[0];

    if (!selectedItem) {
      throw new Error("missing_signature_queue_items");
    }

    return {
      ...scenario,
      selectedItem,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.readyCount} item(ns) pronto(s) para assinar`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} item(ns) em atencao e ${scenario.summary.batchReadyCount} pronto(s) para lote`
            : `${scenario.summary.blockedCount} item(ns) bloqueado(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_signature_queue_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
