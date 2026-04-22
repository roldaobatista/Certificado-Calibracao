import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildEmissionWorkspaceCatalog,
  listEmissionWorkspaceScenarios,
  resolveEmissionWorkspaceScenario,
} from "./emission-workspace-scenarios.js";

test("lists every canonical emission workspace scenario", () => {
  const scenarios = listEmissionWorkspaceScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["baseline-ready", "team-attention", "release-blocked"],
  );
});

test("returns the default emission workspace scenario when the query is unknown", () => {
  const scenario = resolveEmissionWorkspaceScenario("unknown");

  assert.equal(scenario.id, "baseline-ready");
  assert.equal(scenario.summary.status, "ready");
  assert.equal(scenario.summary.blockedModules, 0);
});

test("returns an attention workspace when competencies are expiring", () => {
  const scenario = resolveEmissionWorkspaceScenario("team-attention");

  assert.equal(scenario.summary.status, "attention");
  assert.equal(scenario.summary.attentionModules, 1);
  assert.match(scenario.summary.warnings.join(" "), /competencia\(s\) expirando/i);
});

test("returns a blocked workspace when onboarding and signature are fail-closed", () => {
  const scenario = resolveEmissionWorkspaceScenario("release-blocked");

  assert.equal(scenario.summary.status, "blocked");
  assert.equal(scenario.summary.blockedModules >= 3, true);
  assert.match(scenario.summary.blockers.join(" "), /MFA/i);
});

test("builds the canonical emission workspace catalog with selected scenario", () => {
  const catalog = buildEmissionWorkspaceCatalog("release-blocked");

  assert.equal(catalog.selectedScenarioId, "release-blocked");
  assert.equal(catalog.scenarios.length, 3);
});
