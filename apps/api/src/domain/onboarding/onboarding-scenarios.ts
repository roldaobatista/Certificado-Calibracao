import type { OnboardingScenarioId as ContractOnboardingScenarioId } from "@afere/contracts";

import {
  evaluateOnboardingReadiness,
  type EvaluateOnboardingReadinessInput,
} from "./onboarding-readiness.js";

type OnboardingScenarioDefinition = {
  label: string;
  description: string;
  input: EvaluateOnboardingReadinessInput;
};

const SCENARIOS = {
  ready: {
    label: "Liberado para emissao",
    description: "Todos os prerequisitos foram concluidos dentro da meta operacional de 1 hora.",
    input: {
      startedAtUtc: "2026-04-21T12:00:00Z",
      completedAtUtc: "2026-04-21T12:45:00Z",
      prerequisites: {
        organizationProfileCompleted: true,
        primarySignatoryReady: true,
        certificateNumberingConfigured: true,
        scopeReviewCompleted: true,
        publicQrConfigured: true,
      },
    },
  },
  blocked: {
    label: "Bloqueado por prerequisitos",
    description: "A primeira emissao segue fechada ate o escopo, a numeracao e o QR publico estarem configurados.",
    input: {
      startedAtUtc: "2026-04-21T12:00:00Z",
      completedAtUtc: "2026-04-21T13:20:00Z",
      prerequisites: {
        organizationProfileCompleted: true,
        primarySignatoryReady: false,
        certificateNumberingConfigured: false,
        scopeReviewCompleted: false,
        publicQrConfigured: false,
      },
    },
  },
} as const satisfies Record<ContractOnboardingScenarioId, OnboardingScenarioDefinition>;

export type OnboardingScenarioId = keyof typeof SCENARIOS;

export interface OnboardingScenario {
  id: OnboardingScenarioId;
  label: string;
  description: string;
  result: ReturnType<typeof evaluateOnboardingReadiness>;
}

const DEFAULT_SCENARIO: OnboardingScenarioId = "ready";

export function resolveOnboardingScenario(scenarioId?: string): OnboardingScenario {
  const id = isOnboardingScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    result: evaluateOnboardingReadiness(scenario.input),
  };
}

export function listOnboardingScenarios(): OnboardingScenario[] {
  return (Object.keys(SCENARIOS) as OnboardingScenarioId[]).map((scenarioId) =>
    resolveOnboardingScenario(scenarioId),
  );
}

function isOnboardingScenarioId(value: string | undefined): value is OnboardingScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
