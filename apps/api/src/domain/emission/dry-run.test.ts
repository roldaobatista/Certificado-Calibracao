import assert from "node:assert/strict";
import { test } from "node:test";

import {
  listEmissionDryRunScenarios,
  resolveEmissionDryRunScenario,
  resolveEmissionDryRunScenarioByProfile,
} from "./dry-run-scenarios.js";

test("returns a ready dry-run for the canonical type B scenario", () => {
  const scenario = resolveEmissionDryRunScenario("type-b-ready");

  assert.equal(scenario.result.status, "ready");
  assert.equal(scenario.result.artifacts.templateId, "template-b");
  assert.equal(scenario.result.artifacts.symbolPolicy, "blocked");
  assert.equal(scenario.result.artifacts.certificateNumber, "AFR-000124");
  assert.equal(scenario.result.artifacts.qrVerificationStatus, "authentic");
  assert.equal(scenario.result.checks.filter((check) => check.status === "failed").length, 0);
  assert.equal(
    scenario.result.checks.some(
      (check) => check.id === "raw_measurement_capture" && check.status === "passed",
    ),
    true,
  );
});

test("keeps type A emission ready while suppressing the accreditation symbol outside scope", () => {
  const scenario = resolveEmissionDryRunScenarioByProfile("A");

  assert.equal(scenario.id, "type-a-suppressed");
  assert.equal(scenario.result.status, "ready");
  assert.equal(scenario.result.artifacts.templateId, "template-a");
  assert.equal(scenario.result.artifacts.symbolPolicy, "suppressed");
  assert.match(scenario.result.warnings.join("\n"), /simbolo sera suprimido/i);
});

test("returns a blocked dry-run with explicit failed checks for the canonical type C scenario", () => {
  const scenario = resolveEmissionDryRunScenario("type-c-blocked");

  assert.equal(scenario.result.status, "blocked");
  assert.ok(scenario.result.blockers.includes("Politica regulatoria do perfil"));
  assert.ok(scenario.result.blockers.includes("Cadastro do equipamento"));
  assert.ok(scenario.result.blockers.includes("Competencia do signatario"));
  assert.ok(
    scenario.result.checks.some(
      (check) => check.id === "profile_policy" && check.status === "failed",
    ),
  );
  assert.ok(
    scenario.result.checks.some(
      (check) => check.id === "qr_authenticity" && check.status === "failed",
    ),
  );
  assert.ok(
    scenario.result.checks.some(
      (check) => check.id === "raw_measurement_capture" && check.status === "failed",
    ),
  );
});

test("lists every canonical dry-run scenario", () => {
  const scenarios = listEmissionDryRunScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["type-b-ready", "type-a-suppressed", "type-c-blocked"],
  );
});
