import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildQualityIndicatorCatalog,
  listQualityIndicatorScenarios,
  resolveQualityIndicatorScenario,
} from "./quality-indicator-scenarios.js";

test("lists every canonical quality indicator scenario", () => {
  const scenarios = listQualityIndicatorScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["baseline-ready", "action-sla-attention", "critical-drift"],
  );
});

test("returns the default quality indicator scenario when the query is unknown", () => {
  const scenario = resolveQualityIndicatorScenario("unknown");

  assert.equal(scenario.id, "action-sla-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps indicators in attention while the corrective action SLA remains below target", () => {
  const scenario = resolveQualityIndicatorScenario("action-sla-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /SLA|reclamacao|NC-014/i);
});

test("blocks the indicator panel when critical drift is selected", () => {
  const scenario = resolveQualityIndicatorScenario("critical-drift");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /reemissao|meta|critico/i);
});

test("allows switching the selected indicator inside the same scenario", () => {
  const scenario = resolveQualityIndicatorScenario(
    "baseline-ready",
    "indicator-client-satisfaction",
  );

  assert.equal(scenario.selectedIndicatorId, "indicator-client-satisfaction");
  assert.equal(scenario.detail.indicatorId, "indicator-client-satisfaction");
});

test("builds the canonical quality indicator catalog with selected scenario", () => {
  const catalog = buildQualityIndicatorCatalog(
    "critical-drift",
    "indicator-capa-effectiveness",
  );

  assert.equal(catalog.selectedScenarioId, "critical-drift");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "critical-drift")
      ?.selectedIndicatorId,
    "indicator-capa-effectiveness",
  );
});
