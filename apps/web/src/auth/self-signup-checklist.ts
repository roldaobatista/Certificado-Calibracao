export type SelfSignupRole = "admin" | "signatory" | "technician";
export type SelfSignupProvider = "email_password" | "google" | "microsoft" | "apple";

const REQUIRED_PROVIDERS: SelfSignupProvider[] = [
  "email_password",
  "google",
  "microsoft",
  "apple",
];

export interface BuildSelfSignupChecklistViewModelInput {
  role: SelfSignupRole;
  enabledProviders: SelfSignupProvider[];
  mfaRequired: boolean;
}

export interface SelfSignupChecklistViewModel {
  status: "ready" | "blocked";
  visibleMethods: SelfSignupProvider[];
  missingMethods: SelfSignupProvider[];
  showMfaStep: boolean;
}

export function buildSelfSignupChecklistViewModel(
  input: BuildSelfSignupChecklistViewModelInput,
): SelfSignupChecklistViewModel {
  const enabledProviders = new Set(input.enabledProviders);
  const missingMethods = REQUIRED_PROVIDERS.filter((provider) => !enabledProviders.has(provider));
  const visibleMethods = REQUIRED_PROVIDERS.filter((provider) => enabledProviders.has(provider));

  return {
    status: missingMethods.length === 0 ? "ready" : "blocked",
    visibleMethods,
    missingMethods,
    showMfaStep: input.mfaRequired,
  };
}
