import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildProcedureRegistryCatalog,
  listProcedureRegistryScenarios,
  resolveProcedureRegistryScenario,
} from "./procedure-registry-scenarios.js";

test("lists every canonical procedure registry scenario", () => {
  const scenarios = listProcedureRegistryScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "revision-attention", "obsolete-visible"],
  );
});

test("returns the default procedure registry scenario when the query is unknown", () => {
  const scenario = resolveProcedureRegistryScenario("unknown");

  assert.equal(scenario.id, "operational-ready");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps the procedure registry in attention when the selected procedure is pending quality review", () => {
  const scenario = resolveProcedureRegistryScenario("revision-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /revisao da qualidade/i);
  assert.equal(scenario.summary.attentionCount, 1);
});

test("shows the obsolete revision as blocked for new work orders", () => {
  const scenario = resolveProcedureRegistryScenario("obsolete-visible");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /novas OS|obsoleta/i);
  assert.equal(scenario.summary.obsoleteCount, 1);
});

test("allows switching the selected procedure inside the same scenario", () => {
  const scenario = resolveProcedureRegistryScenario("operational-ready", "procedure-pt006-r02");

  assert.equal(scenario.selectedProcedureId, "procedure-pt006-r02");
  assert.equal(scenario.detail.procedureId, "procedure-pt006-r02");
  assert.match(scenario.detail.title, /PT-006/i);
});

test("builds the canonical procedure registry catalog with selected scenario", () => {
  const catalog = buildProcedureRegistryCatalog("revision-attention");

  assert.equal(catalog.selectedScenarioId, "revision-attention");
  assert.equal(catalog.scenarios.length, 3);
});
