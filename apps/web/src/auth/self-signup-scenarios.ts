import type { SelfSignupChecklistViewModel, SelfSignupProvider, SelfSignupRole } from "@afere/contracts";

import { buildSelfSignupChecklistViewModel } from "./self-signup-checklist";

type SelfSignupScenarioDefinition = {
  label: string;
  description: string;
  input: {
    role: SelfSignupRole;
    enabledProviders: SelfSignupProvider[];
    mfaRequired: boolean;
  };
};

const SCENARIOS = {
  "signatory-ready": {
    label: "Signatario pronto",
    description: "Todos os provedores estao habilitados e o passo de MFA aparece antes da ativacao.",
    input: {
      role: "signatory",
      enabledProviders: ["email_password", "google", "microsoft", "apple"],
      mfaRequired: true,
    },
  },
  "admin-guided": {
    label: "Admin guiado",
    description: "Onboarding completo de administrador com todos os metodos visiveis e MFA mandataria.",
    input: {
      role: "admin",
      enabledProviders: ["email_password", "google", "microsoft", "apple"],
      mfaRequired: true,
    },
  },
  "technician-blocked": {
    label: "Tecnico bloqueado",
    description: "Fluxo propositalmente incompleto para evidenciar bloqueio quando faltam provedores obrigatorios.",
    input: {
      role: "technician",
      enabledProviders: ["email_password", "google"],
      mfaRequired: false,
    },
  },
} as const satisfies Record<string, SelfSignupScenarioDefinition>;

export type SelfSignupScenarioId = keyof typeof SCENARIOS;

export interface SelfSignupScenario {
  id: SelfSignupScenarioId;
  label: string;
  description: string;
  viewModel: SelfSignupChecklistViewModel;
}

const DEFAULT_SCENARIO: SelfSignupScenarioId = "signatory-ready";

export function resolveSelfSignupScenario(scenarioId?: string): SelfSignupScenario {
  const id = isSelfSignupScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
  const scenario = SCENARIOS[id];

  return {
    id,
    label: scenario.label,
    description: scenario.description,
    viewModel: buildSelfSignupChecklistViewModel(scenario.input),
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
