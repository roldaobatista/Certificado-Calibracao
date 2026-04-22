import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildNonconformityCatalog,
  listNonconformityScenarios,
  resolveNonconformityScenario,
} from "./nonconformity-scenarios.js";

test("lists every canonical nonconformity scenario", () => {
  const scenarios = listNonconformityScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["open-attention", "critical-response", "resolved-history"],
  );
});

test("returns the default nonconformity scenario when the query is unknown", () => {
  const scenario = resolveNonconformityScenario("unknown");

  assert.equal(scenario.id, "open-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps the nonconformity registry in attention for an open moderate NC", () => {
  const scenario = resolveNonconformityScenario("open-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /acao corretiva vence/i);
});

test("blocks the registry when a critical NC is selected", () => {
  const scenario = resolveNonconformityScenario("critical-response");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /critica aberta/i);
});

test("allows switching the selected NC inside the same scenario", () => {
  const scenario = resolveNonconformityScenario("resolved-history", "nc-014");

  assert.equal(scenario.selectedNcId, "nc-014");
  assert.equal(scenario.detail.ncId, "nc-014");
  assert.match(scenario.detail.title, /NC-014/i);
});

test("builds the canonical nonconformity catalog with selected scenario", () => {
  const catalog = buildNonconformityCatalog("critical-response");

  assert.equal(catalog.selectedScenarioId, "critical-response");
  assert.equal(catalog.scenarios.length, 3);
});
