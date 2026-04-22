import type { OnboardingBlockingReason, OnboardingReadinessResult } from "@afere/contracts";

const ONE_HOUR_MS = 60 * 60 * 1000;

export interface OnboardingPrerequisites {
  organizationProfileCompleted: boolean;
  primarySignatoryReady: boolean;
  certificateNumberingConfigured: boolean;
  scopeReviewCompleted: boolean;
  publicQrConfigured: boolean;
}

export interface EvaluateOnboardingReadinessInput {
  startedAtUtc: string;
  completedAtUtc: string;
  prerequisites: OnboardingPrerequisites;
}

export function evaluateOnboardingReadiness(
  input: EvaluateOnboardingReadinessInput,
): OnboardingReadinessResult {
  const blockingReasons: OnboardingBlockingReason[] = [];

  if (!input.prerequisites.primarySignatoryReady) blockingReasons.push("primary_signatory_pending");
  if (!input.prerequisites.certificateNumberingConfigured) {
    blockingReasons.push("certificate_numbering_pending");
  }
  if (!input.prerequisites.scopeReviewCompleted) blockingReasons.push("scope_review_pending");
  if (!input.prerequisites.publicQrConfigured) blockingReasons.push("public_qr_pending");
  if (!input.prerequisites.organizationProfileCompleted) {
    blockingReasons.push("organization_profile_pending");
  }

  const startedAt = Date.parse(input.startedAtUtc);
  const completedAt = Date.parse(input.completedAtUtc);
  const elapsedMs = completedAt - startedAt;
  const completedWithinTarget =
    Number.isFinite(startedAt) &&
    Number.isFinite(completedAt) &&
    elapsedMs >= 0 &&
    elapsedMs <= ONE_HOUR_MS;

  return {
    completedWithinTarget,
    canEmitFirstCertificate: blockingReasons.length === 0,
    blockingReasons,
  };
}
