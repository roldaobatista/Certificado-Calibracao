import assert from "node:assert/strict";
import { test } from "node:test";

import { buildSelfSignupChecklistViewModel } from "./self-signup-checklist.js";

test("shows every required self-signup method and the MFA step for privileged roles", () => {
  const viewModel = buildSelfSignupChecklistViewModel({
    role: "signatory",
    enabledProviders: ["email_password", "google", "microsoft", "apple"],
    mfaRequired: true,
  });

  assert.equal(viewModel.status, "ready");
  assert.deepEqual(viewModel.visibleMethods, ["email_password", "google", "microsoft", "apple"]);
  assert.deepEqual(viewModel.missingMethods, []);
  assert.equal(viewModel.showMfaStep, true);
});

test("keeps the wizard blocked when a required provider is missing and MFA is not needed", () => {
  const viewModel = buildSelfSignupChecklistViewModel({
    role: "technician",
    enabledProviders: ["email_password", "google"],
    mfaRequired: false,
  });

  assert.equal(viewModel.status, "blocked");
  assert.deepEqual(viewModel.missingMethods, ["microsoft", "apple"]);
  assert.equal(viewModel.showMfaStep, false);
});
