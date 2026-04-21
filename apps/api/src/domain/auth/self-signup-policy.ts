export type SelfSignupRole = "admin" | "signatory" | "technician";
export type SelfSignupProvider = "email_password" | "google" | "microsoft" | "apple";

const REQUIRED_PROVIDERS: SelfSignupProvider[] = [
  "email_password",
  "google",
  "microsoft",
  "apple",
];

export interface EvaluateSelfSignupPolicyInput {
  role: SelfSignupRole;
  enabledProviders: SelfSignupProvider[];
  enrolledMfaFactors: string[];
}

export interface EvaluateSelfSignupPolicyResult {
  ok: boolean;
  missingProviders: SelfSignupProvider[];
  mfaRequired: boolean;
  reason?: "missing_required_provider" | "mfa_required_for_privileged_role";
}

export function evaluateSelfSignupPolicy(
  input: EvaluateSelfSignupPolicyInput,
): EvaluateSelfSignupPolicyResult {
  const enabledProviders = new Set(input.enabledProviders);
  const missingProviders = REQUIRED_PROVIDERS.filter((provider) => !enabledProviders.has(provider));
  const mfaRequired = input.role === "admin" || input.role === "signatory";

  if (missingProviders.length > 0) {
    return {
      ok: false,
      missingProviders,
      mfaRequired,
      reason: "missing_required_provider",
    };
  }

  if (mfaRequired && input.enrolledMfaFactors.every((factor) => factor.trim().length === 0)) {
    return {
      ok: false,
      missingProviders: [],
      mfaRequired,
      reason: "mfa_required_for_privileged_role",
    };
  }

  return {
    ok: true,
    missingProviders: [],
    mfaRequired,
  };
}
