import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildNonconformingWorkCatalog,
  listNonconformingWorkScenarios,
  resolveNonconformingWorkScenario,
} from "./nonconforming-work-scenarios.js";

test("lists every canonical nonconforming work scenario", () => {
  const scenarios = listNonconformingWorkScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["contained-attention", "release-blocked", "archived-history"],
  );
});

test("returns the default nonconforming work scenario when the query is unknown", () => {
  const scenario = resolveNonconformingWorkScenario("unknown");

  assert.equal(scenario.id, "contained-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps the module in attention while the preventive containment is still active", () => {
  const scenario = resolveNonconformingWorkScenario("contained-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.containmentLabel, /suspender|PT-005|PT-006|PT-008/i);
});

test("blocks the module when release and reissue are explicitly forbidden", () => {
  const scenario = resolveNonconformingWorkScenario("release-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.releaseRuleLabel, /nova OS|reemissao|leitura bruta/i);
});

test("archives the module when the nonconforming work is already restored", () => {
  const scenario = resolveNonconformingWorkScenario("archived-history");

  assert.equal(scenario.detail.status, "ready");
  assert.match(scenario.detail.restorationLabel, /Sem acoes pendentes|historico/i);
});

test("builds the canonical nonconforming work catalog with selected scenario", () => {
  const catalog = buildNonconformingWorkCatalog("release-blocked", "ncw-015");

  assert.equal(catalog.selectedScenarioId, "release-blocked");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "release-blocked")?.selectedCaseId,
    "ncw-015",
  );
});
