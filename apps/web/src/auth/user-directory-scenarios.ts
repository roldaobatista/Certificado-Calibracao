import type { UserDirectoryCatalog, UserDirectoryScenario } from "@afere/contracts";

export interface UserDirectoryScenarioViewModel extends UserDirectoryScenario {
  summaryLabel: string;
}

export interface UserDirectoryCatalogViewModel {
  selectedScenario: UserDirectoryScenarioViewModel;
  scenarios: UserDirectoryScenarioViewModel[];
}

export function buildUserDirectoryCatalogView(
  catalog: UserDirectoryCatalog,
): UserDirectoryCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => ({
    ...scenario,
    summaryLabel:
      scenario.summary.status === "ready"
        ? `${scenario.summary.activeUsers} usuario(s) ativos e nenhuma competencia critica`
        : `${scenario.summary.expiringCompetencies} competencia(s) expirando, ${scenario.summary.expiredCompetencies} vencida(s) e ${scenario.summary.suspendedUsers} suspenso(s)`,
  }));

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_user_directory_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
