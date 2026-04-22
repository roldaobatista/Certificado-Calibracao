import type {
  SelfSignupRole,
  SelfSignupScenarioId as ContractSelfSignupScenarioId,
} from "@afere/contracts";

import { evaluateSelfSignupPolicy, type EvaluateSelfSignupPolicyInput } from "./self-signup-policy.js";

type SelfSignupScenarioDefinition = {
  label: string;
  description: string;
  role: SelfSignupRole;
  input: EvaluateSelfSignupPolicyInput;
};

const SCENARIOS = {
  "signatory-ready": {
    label: "Signatario pronto",
    description: "Todos os provedores estao habilitados e o passo de MFA aparece antes da ativacao.",
    role: "signatory",
    input: {
      role: "signatory",
      enabledProviders: ["email_password", "google", "microsoft", "apple"],
      enrolledMfaFactors: ["totp"],
    },
  },
  "admin-guided": {
    label: "Admin guiado",
    description: "Onboarding completo de administrador com todos os metodos visiveis e MFA mandataria.",
    role: "admin",
    input: {
      role: "admin",
      enabledProviders: ["email_password", "google", "microsoft", "apple"],
      enrolledMfaFactors: ["totp"],
    },
  },
  "technician-blocked": {
    label: "Tecnico bloqueado",
    description: "Fluxo propositalmente incompleto para evidenciar bloqueio quando faltam provedores obrigatorios.",
    role: "technician",
    input: {
      role: "technician",
      enabledProviders: ["email_password", "google"],
      enrolledMfaFactors: [],
    },
  },
} as const satisfies Record<ContractSelfSignupScenarioId, SelfSignupScenarioDefinition>;

export type SelfSignupScenarioId = keyof typeof SCENARIOS;

export interface SelfSignupScenario {
  id: SelfSignupScenarioId;
  label: string;
  description: string;
  role: SelfSignupRole;
  result: ReturnType<typeof evaluateSelfSignupPolicy>;
}

const DEFAULT_SCENARIO: SelfSignupScenarioId = "signatory-ready";

export function resolveSelfSignupScenario(scenarioId?: string): SelfSignupScenario {
  const id = isSelfSignupScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    role: scenario.role,
    result: evaluateSelfSignupPolicy(scenario.input),
  };
}

export function listSelfSignupScenarios(): SelfSignupScenario[] {
  return (Object.keys(SCENARIOS) as SelfSignupScenarioId[]).map((scenarioId) =>
    resolveSelfSignupScenario(scenarioId),
  );
}

function isSelfSignupScenarioId(value: string | undefined): value is SelfSignupScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}
