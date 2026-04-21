import assert from "node:assert/strict";
import { test } from "node:test";

import { buildOnboardingWizardSummary } from "./onboarding-wizard-summary.js";

test("shows a ready summary when onboarding is within the target and first emission is unlocked", () => {
  const summary = buildOnboardingWizardSummary({
    completedWithinTarget: true,
    canEmitFirstCertificate: true,
    blockingReasons: [],
  });

  assert.equal(summary.status, "ready");
  assert.equal(summary.title, "Onboarding pronto para primeira emissao");
  assert.equal(summary.timeTargetLabel, "Dentro da meta de 1 hora");
  assert.deepEqual(summary.blockingSteps, []);
});

test("shows blocked steps and warns when onboarding exceeds the target time", () => {
  const summary = buildOnboardingWizardSummary({
    completedWithinTarget: false,
    canEmitFirstCertificate: false,
    blockingReasons: ["scope_review_pending", "public_qr_pending"],
  });

  assert.equal(summary.status, "blocked");
  assert.equal(summary.title, "Emissao bloqueada ate concluir o onboarding");
  assert.equal(summary.timeTargetLabel, "Acima da meta de 1 hora");
  assert.deepEqual(summary.blockingSteps, ["Escopo e CMC", "QR publico"]);
});
