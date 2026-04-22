import type {
  ComplaintRegistryCatalog,
  ComplaintRegistryScenario,
} from "@afere/contracts";

export interface ComplaintRegistryScenarioViewModel extends ComplaintRegistryScenario {
  selectedComplaint: ComplaintRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface ComplaintRegistryCatalogViewModel {
  selectedScenario: ComplaintRegistryScenarioViewModel;
  scenarios: ComplaintRegistryScenarioViewModel[];
}

export function buildComplaintCatalogView(
  catalog: ComplaintRegistryCatalog,
): ComplaintRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedComplaint =
      scenario.items.find((item) => item.complaintId === scenario.selectedComplaintId) ??
      scenario.items[0];

    if (!selectedComplaint) {
      throw new Error("missing_complaint_items");
    }

    return {
      ...scenario,
      selectedComplaint,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.resolvedLast30d} reclamacao(oes) resolvida(s) e historico auditavel`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openCount} reclamacao(oes) aberta(s) e resposta em andamento`
            : `${scenario.summary.reissuePendingCount} reemissao(oes) pendente(s) e fluxo bloqueado`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_complaint_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
