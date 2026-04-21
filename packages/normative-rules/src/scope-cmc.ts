import type { RegulatoryProfileId } from "./regulatory-profiles.js";

export type AccreditedScopeCmcEvaluation = {
  profile: RegulatoryProfileId;
  canEmitCertificate: boolean;
  canUseAccreditationSymbol: boolean;
  symbolPolicy: "allowed" | "suppressed" | "blocked";
  blockers: string[];
  warnings: string[];
};

export function evaluateAccreditedScopeCmc(input: {
  profile: RegulatoryProfileId;
  accreditationActive?: boolean;
  hasRegisteredScope?: boolean;
  hasRegisteredCmc?: boolean;
  withinAccreditedScope?: boolean;
  expandedUncertainty?: number;
  declaredCmc?: number;
}): AccreditedScopeCmcEvaluation {
  if (input.profile !== "A") {
    return {
      profile: input.profile,
      canEmitCertificate: true,
      canUseAccreditationSymbol: false,
      symbolPolicy: "blocked",
      blockers: [],
      warnings: ["not_applicable_to_non_accredited_profile"],
    };
  }

  const blockers: string[] = [];
  const warnings: string[] = [];

  if (input.hasRegisteredScope === false) {
    blockers.push("missing_scope_registration");
  }

  if (input.hasRegisteredCmc === false) {
    blockers.push("missing_cmc_registration");
  }

  if (
    typeof input.expandedUncertainty === "number" &&
    typeof input.declaredCmc === "number" &&
    input.expandedUncertainty < input.declaredCmc
  ) {
    blockers.push("uncertainty_below_cmc");
  }

  if (input.accreditationActive === false) {
    warnings.push("accreditation_expired");
  }

  if (input.withinAccreditedScope === false) {
    warnings.push("outside_accredited_scope");
  }

  if (blockers.length > 0) {
    return {
      profile: input.profile,
      canEmitCertificate: false,
      canUseAccreditationSymbol: false,
      symbolPolicy: "blocked",
      blockers,
      warnings,
    };
  }

  if (warnings.length > 0) {
    return {
      profile: input.profile,
      canEmitCertificate: true,
      canUseAccreditationSymbol: false,
      symbolPolicy: "suppressed",
      blockers,
      warnings,
    };
  }

  return {
    profile: input.profile,
    canEmitCertificate: true,
    canUseAccreditationSymbol: true,
    symbolPolicy: "allowed",
    blockers,
    warnings,
  };
}
