import assert from "node:assert/strict";
import { test } from "node:test";

import { listOnboardingScenarios, resolveOnboardingScenario } from "./onboarding-scenarios.js";

test("returns the default onboarding scenario when the query is unknown", () => {
  const scenario = resolveOnboardingScenario("desconhecido");

  assert.equal(scenario.id, "ready");
  assert.equal(scenario.result.canEmitFirstCertificate, true);
  assert.equal(scenario.result.completedWithinTarget, true);
});

test("returns a blocked onboarding scenario with explicit missing prerequisites", () => {
  const scenario = listOnboardingScenarios().find((item) => item.id === "blocked");

  assert.ok(scenario);
  assert.equal(scenario.result.canEmitFirstCertificate, false);
  assert.equal(scenario.result.completedWithinTarget, false);
  assert.deepEqual(scenario.result.blockingReasons, [
    "primary_signatory_pending",
    "certificate_numbering_pending",
    "scope_review_pending",
    "public_qr_pending",
  ]);
});
