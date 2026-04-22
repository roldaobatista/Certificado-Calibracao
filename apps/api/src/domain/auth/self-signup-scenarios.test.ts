import assert from "node:assert/strict";
import { test } from "node:test";

import { listSelfSignupScenarios, resolveSelfSignupScenario } from "./self-signup-scenarios.js";

test("returns the default self-signup scenario when the query is unknown", () => {
  const scenario = resolveSelfSignupScenario("nao-existe");

  assert.equal(scenario.id, "signatory-ready");
  assert.equal(scenario.result.ok, true);
  assert.equal(scenario.result.mfaRequired, true);
});

test("returns a blocked technician scenario with missing required providers", () => {
  const scenario = listSelfSignupScenarios().find((item) => item.id === "technician-blocked");

  assert.ok(scenario);
  assert.equal(scenario.result.ok, false);
  assert.deepEqual(scenario.result.missingProviders, ["microsoft", "apple"]);
  assert.equal(scenario.result.reason, "missing_required_provider");
});
