import type {
  EquipmentRegistryCatalog,
  EquipmentRegistryScenario,
} from "@afere/contracts";

export interface EquipmentRegistryScenarioViewModel extends EquipmentRegistryScenario {
  selectedEquipment: EquipmentRegistryScenario["items"][number];
  summaryLabel: string;
}

export interface EquipmentRegistryCatalogViewModel {
  selectedScenario: EquipmentRegistryScenarioViewModel;
  scenarios: EquipmentRegistryScenarioViewModel[];
}

export function buildEquipmentRegistryCatalogView(
  catalog: EquipmentRegistryCatalog,
): EquipmentRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedEquipment =
      scenario.items.find((item) => item.equipmentId === scenario.selectedEquipmentId) ??
      scenario.items[0];

    if (!selectedEquipment) {
      throw new Error("missing_equipment_registry_items");
    }

    return {
      ...scenario,
      selectedEquipment,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.readyCount} equipamento(s) pronto(s) e ${scenario.summary.totalEquipment} no recorte canonico`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCount} equipamento(s) em atencao e ${scenario.summary.dueSoonCount} vencimento(s) proximo(s)`
            : `${scenario.summary.blockedCount} equipamento(s) bloqueado(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_equipment_registry_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
