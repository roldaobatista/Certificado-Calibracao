import assert from "node:assert/strict";
import { test } from "node:test";

import { buildUserDirectoryCatalog, listUserDirectoryScenarios, resolveUserDirectoryScenario } from "./user-directory-scenarios.js";

test("lists every canonical user directory scenario", () => {
  const scenarios = listUserDirectoryScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-team", "expiring-competencies", "suspended-access"],
  );
});

test("returns the default user directory scenario when the query is unknown", () => {
  const scenario = resolveUserDirectoryScenario("unknown");

  assert.equal(scenario.id, "operational-team");
  assert.equal(scenario.summary.status, "ready");
});

test("returns an attention scenario when competencies are expiring", () => {
  const scenario = resolveUserDirectoryScenario("expiring-competencies");

  assert.equal(scenario.summary.status, "attention");
  assert.equal(scenario.summary.expiringCompetencies, 1);
});

test("builds the canonical user directory catalog with selected scenario", () => {
  const catalog = buildUserDirectoryCatalog("suspended-access");

  assert.equal(catalog.selectedScenarioId, "suspended-access");
  assert.equal(catalog.scenarios.length, 3);
});
