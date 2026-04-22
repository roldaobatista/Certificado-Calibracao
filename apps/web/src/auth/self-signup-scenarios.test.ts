import assert from "node:assert/strict";
import { test } from "node:test";

import { listSelfSignupScenarios, resolveSelfSignupScenario } from "./self-signup-scenarios.js";

test("falls back to the default self-signup scenario when the query is unknown", () => {
  const scenario = resolveSelfSignupScenario("nao-existe");

  assert.equal(scenario.id, "signatory-ready");
  assert.equal(scenario.viewModel.status, "ready");
  assert.equal(scenario.viewModel.showMfaStep, true);
});

test("lists a blocked technician scenario with the missing providers visible", () => {
  const scenario = listSelfSignupScenarios().find((item) => item.id === "technician-blocked");

  assert.ok(scenario);
  assert.equal(scenario.viewModel.status, "blocked");
  assert.deepEqual(scenario.viewModel.missingMethods, ["microsoft", "apple"]);
});
