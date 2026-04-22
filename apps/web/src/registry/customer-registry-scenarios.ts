import type {
  CustomerRegistryCatalog,
  CustomerRegistryScenario,
} from "@afere/contracts";

export interface CustomerRegistryScenarioViewModel extends CustomerRegistryScenario {
  selectedCustomer: CustomerRegistryScenario["customers"][number];
  summaryLabel: string;
}

export interface CustomerRegistryCatalogViewModel {
  selectedScenario: CustomerRegistryScenarioViewModel;
  scenarios: CustomerRegistryScenarioViewModel[];
}

export function buildCustomerRegistryCatalogView(
  catalog: CustomerRegistryCatalog,
): CustomerRegistryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedCustomer =
      scenario.customers.find((item) => item.customerId === scenario.selectedCustomerId) ??
      scenario.customers[0];

    if (!selectedCustomer) {
      throw new Error("missing_customer_registry_customers");
    }

    return {
      ...scenario,
      selectedCustomer,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.activeCustomers} cliente(s) ativos e ${scenario.summary.totalEquipment} equipamento(s) no recorte canonico`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionCustomers} cliente(s) em atencao e ${scenario.summary.dueSoonCount} vencimento(s) proximo(s)`
            : `${scenario.summary.blockedCustomers} cliente(s) bloqueado(s) e ${scenario.summary.blockers.length} bloqueio(s) ativo(s)`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_customer_registry_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
