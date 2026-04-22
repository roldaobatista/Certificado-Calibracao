import type { OnboardingBlockingReason, OnboardingWizardSummary } from "@afere/contracts";

import { buildOnboardingWizardSummary } from "./onboarding-wizard-summary";

type OnboardingScenarioDefinition = {
  label: string;
  description: string;
  input: {
    completedWithinTarget: boolean;
    canEmitFirstCertificate: boolean;
    blockingReasons: OnboardingBlockingReason[];
  };
};

const SCENARIOS = {
  ready: {
    label: "Liberado para emissao",
    description: "Todos os prerequisitos foram concluidos dentro da meta operacional de 1 hora.",
    input: {
      completedWithinTarget: true,
      canEmitFirstCertificate: true,
      blockingReasons: [],
    },
  },
  blocked: {
    label: "Bloqueado por prerequisitos",
    description: "A primeira emissao segue fechada ate o escopo, a numeracao e o QR publico estarem configurados.",
    input: {
      completedWithinTarget: false,
      canEmitFirstCertificate: false,
      blockingReasons: [
        "certificate_numbering_pending",
        "scope_review_pending",
        "public_qr_pending",
      ],
    },
  },
} as const satisfies Record<string, OnboardingScenarioDefinition>;

export type OnboardingScenarioId = keyof typeof SCENARIOS;

export interface OnboardingScenario {
  id: OnboardingScenarioId;
  label: string;
  description: string;
  summary: OnboardingWizardSummary;
}

const DEFAULT_SCENARIO: OnboardingScenarioId = "ready";

export function resolveOnboardingScenario(scenarioId?: string): OnboardingScenario {
  const id = isOnboardingScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    summary: buildOnboardingWizardSummary(scenario.input),
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
