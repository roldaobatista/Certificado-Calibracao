import type { PortalEquipmentCatalog, PortalEquipmentScenario } from "@afere/contracts";

export interface PortalEquipmentScenarioViewModel extends PortalEquipmentScenario {
  selectedEquipment: PortalEquipmentScenario["items"][number];
  summaryLabel: string;
}

export interface PortalEquipmentCatalogViewModel {
  selectedScenario: PortalEquipmentScenarioViewModel;
  scenarios: PortalEquipmentScenarioViewModel[];
}

export function buildPortalEquipmentCatalogView(
  catalog: PortalEquipmentCatalog,
): PortalEquipmentCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedEquipment =
      scenario.items.find((item) => item.equipmentId === scenario.selectedEquipmentId) ??
      scenario.items[0];

    if (!selectedEquipment) {
      throw new Error("missing_portal_equipment_items");
    }

    return {
      ...scenario,
      selectedEquipment,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.equipmentCount} equipamento(s) em carteira sem alertas`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} equipamento(s) em atencao`
            : `${scenario.summary.blockedCount} equipamento(s) bloqueado(s) no recorte`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_portal_equipment_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
