import type {
  RiskMatrixItem,
  RiskRegisterCatalog,
  RiskRegisterScenario,
} from "@afere/contracts";

export interface RiskRegisterScenarioViewModel extends RiskRegisterScenario {
  selectedRisk: RiskMatrixItem;
  summaryLabel: string;
}

export interface RiskRegisterCatalogViewModel {
  selectedScenario: RiskRegisterScenarioViewModel;
  scenarios: RiskRegisterScenarioViewModel[];
}

export function buildRiskRegisterCatalogView(
  catalog: RiskRegisterCatalog,
): RiskRegisterCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedRisk =
      scenario.risks.find((item) => item.riskId === scenario.selectedRiskId) ??
      scenario.risks[0];

    if (!selectedRisk) {
      throw new Error("missing_risk_items");
    }

    return {
      ...scenario,
      selectedRisk,
      summaryLabel:
        scenario.summary.status === "ready"
          ? `${scenario.summary.activeRiskCount} risco(s) monitorado(s) e rodada anual arquivada`
          : scenario.summary.status === "attention"
            ? `${scenario.summary.pendingDeclarationCount} declaracao(oes) pendente(s) e ${scenario.summary.activeRiskCount} risco(s) ativo(s)`
            : `${scenario.summary.highImpactRiskCount} risco(s) de alto impacto e escalacao critica`,
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ?? scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_risk_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
