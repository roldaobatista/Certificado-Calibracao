import type {
  OrganizationSettingsCatalog,
  OrganizationSettingsScenario,
} from "@afere/contracts";

export interface OrganizationSettingsScenarioViewModel extends OrganizationSettingsScenario {
  selectedSection: OrganizationSettingsScenario["sections"][number];
  summaryLabel: string;
}

export interface OrganizationSettingsCatalogViewModel {
  selectedScenario: OrganizationSettingsScenarioViewModel;
  scenarios: OrganizationSettingsScenarioViewModel[];
}

export function buildOrganizationSettingsCatalogView(
  catalog: OrganizationSettingsCatalog,
): OrganizationSettingsCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedSection =
      scenario.sections.find((section) => section.key === scenario.selectedSectionKey) ??
      scenario.sections[0];

    if (!selectedSection) {
      throw new Error("missing_organization_settings_sections");
    }

    return {
      ...scenario,
      selectedSection,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.configuredSections} secoes configuradas para ${scenario.summary.profileLabel}`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.attentionSections} secao(oes) em atencao e ${scenario.summary.blockedSections} bloqueada(s)`
            : `${scenario.summary.blockedSections} secao(oes) bloqueada(s) e mudanca controlada ativa`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_organization_settings_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
