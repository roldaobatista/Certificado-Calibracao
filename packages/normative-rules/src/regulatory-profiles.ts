export type RegulatoryProfileId = "A" | "B" | "C";

export type RegulatoryPdfPolicy = {
  profile: RegulatoryProfileId;
  templateId: "template-a" | "template-b" | "template-c";
  symbolPolicy: "allowed" | "blocked" | "suppressed";
  allowedStandardSources: string[];
  forbiddenFreeTextTerms: string[];
  warnings: string[];
};

const REGULATORY_PROFILE_POLICIES: Record<RegulatoryProfileId, Omit<RegulatoryPdfPolicy, "symbolPolicy" | "warnings">> = {
  A: {
    profile: "A",
    templateId: "template-a",
    allowedStandardSources: ["INM", "RBC", "ILAC_MRA"],
    forbiddenFreeTextTerms: [],
  },
  B: {
    profile: "B",
    templateId: "template-b",
    allowedStandardSources: ["RBC", "INM"],
    forbiddenFreeTextTerms: [],
  },
  C: {
    profile: "C",
    templateId: "template-c",
    allowedStandardSources: ["INM"],
    forbiddenFreeTextTerms: ["RBC", "Cgcre"],
  },
};

export function resolveRegulatoryPdfPolicy(input: {
  profile: RegulatoryProfileId;
  withinAccreditedScope?: boolean;
}): RegulatoryPdfPolicy {
  const policy = REGULATORY_PROFILE_POLICIES[input.profile];
  const warnings: string[] = [];

  if (input.profile === "A" && input.withinAccreditedScope === false) {
    warnings.push("outside_accredited_scope");
  }

  return {
    ...policy,
    symbolPolicy:
      input.profile === "A"
        ? input.withinAccreditedScope === false
          ? "suppressed"
          : "allowed"
        : "blocked",
    warnings,
  };
}

export function validateRegulatoryFreeText(profile: RegulatoryProfileId, text: string): string[] {
  const policy = REGULATORY_PROFILE_POLICIES[profile];
  return policy.forbiddenFreeTextTerms
    .filter((term) => new RegExp(`\\b${escapeRegex(term)}\\b`, "i").test(text))
    .map((term) => `forbidden_term:${term}`);
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
