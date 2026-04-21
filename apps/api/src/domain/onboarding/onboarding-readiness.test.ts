import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateOnboardingReadiness } from "./onboarding-readiness.js";

test("marks onboarding as complete within target and unlocks the first certificate when all prerequisites are done", () => {
  const result = evaluateOnboardingReadiness({
    startedAtUtc: "2026-04-21T12:00:00Z",
    completedAtUtc: "2026-04-21T12:45:00Z",
    prerequisites: {
      organizationProfileCompleted: true,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    },
  });

  assert.equal(result.completedWithinTarget, true);
  assert.equal(result.canEmitFirstCertificate, true);
  assert.deepEqual(result.blockingReasons, []);
});

test("tracks when the onboarding wizard exceeds the one-hour target even if prerequisites are complete", () => {
  const result = evaluateOnboardingReadiness({
    startedAtUtc: "2026-04-21T12:00:00Z",
    completedAtUtc: "2026-04-21T13:15:00Z",
    prerequisites: {
      organizationProfileCompleted: true,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    },
  });

  assert.equal(result.completedWithinTarget, false);
  assert.equal(result.canEmitFirstCertificate, true);
  assert.deepEqual(result.blockingReasons, []);
});

test("blocks the first certificate emission until every mandatory prerequisite is complete", () => {
  const result = evaluateOnboardingReadiness({
    startedAtUtc: "2026-04-21T12:00:00Z",
    completedAtUtc: "2026-04-21T12:20:00Z",
    prerequisites: {
      organizationProfileCompleted: true,
      primarySignatoryReady: false,
      certificateNumberingConfigured: false,
      scopeReviewCompleted: true,
      publicQrConfigured: false,
    },
  });

  assert.equal(result.completedWithinTarget, true);
  assert.equal(result.canEmitFirstCertificate, false);
  assert.deepEqual(result.blockingReasons, [
    "primary_signatory_pending",
    "certificate_numbering_pending",
    "public_qr_pending",
  ]);
});
