import assert from "node:assert/strict";
import { test } from "node:test";

import { listEmissionDryRunScenarios, resolveEmissionDryRunScenario } from "./emission-dry-run-scenarios.js";

test("falls back to the ready dry-run scenario when the query is unknown", () => {
  const scenario = resolveEmissionDryRunScenario("nao-existe");

  assert.equal(scenario.id, "type-b-ready");
  assert.equal(scenario.summary.status, "ready");
  assert.equal(scenario.summary.failedChecks, 0);
});

test("exposes blockers and failed checks for the blocked dry-run scenario", () => {
  const scenario = listEmissionDryRunScenarios().find((item) => item.id === "type-c-blocked");

  assert.ok(scenario);
  assert.equal(scenario.summary.status, "blocked");
  assert.equal(scenario.summary.failedChecks, 5);
  assert.deepEqual(scenario.summary.blockers, [
    "Politica regulatoria do perfil",
    "Cadastro do equipamento",
    "Elegibilidade do padrao",
    "Competencia do signatario",
    "QR publico",
  ]);
});
