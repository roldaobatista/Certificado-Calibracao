import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateSelfSignupPolicy } from "./self-signup-policy.js";

test("allows self-signup when all required providers are enabled and a privileged role has MFA", () => {
  const result = evaluateSelfSignupPolicy({
    role: "admin",
    enabledProviders: ["email_password", "google", "microsoft", "apple"],
    enrolledMfaFactors: ["totp"],
  });

  assert.equal(result.ok, true);
  assert.equal(result.mfaRequired, true);
  assert.deepEqual(result.missingProviders, []);
  assert.equal(result.reason, undefined);
});

test("allows a non-privileged role without MFA once all required self-signup providers exist", () => {
  const result = evaluateSelfSignupPolicy({
    role: "technician",
    enabledProviders: ["email_password", "google", "microsoft", "apple"],
    enrolledMfaFactors: [],
  });

  assert.equal(result.ok, true);
  assert.equal(result.mfaRequired, false);
  assert.deepEqual(result.missingProviders, []);
});

test("fails closed when a required provider is missing or when a privileged role has no MFA", () => {
  const missingProvider = evaluateSelfSignupPolicy({
    role: "technician",
    enabledProviders: ["email_password", "google", "apple"],
    enrolledMfaFactors: [],
  });

  assert.equal(missingProvider.ok, false);
  assert.equal(missingProvider.reason, "missing_required_provider");
  assert.deepEqual(missingProvider.missingProviders, ["microsoft"]);

  const missingMfa = evaluateSelfSignupPolicy({
    role: "signatory",
    enabledProviders: ["email_password", "google", "microsoft", "apple"],
    enrolledMfaFactors: [],
  });

  assert.equal(missingMfa.ok, false);
  assert.equal(missingMfa.reason, "mfa_required_for_privileged_role");
  assert.equal(missingMfa.mfaRequired, true);
});
