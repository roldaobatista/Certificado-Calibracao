import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildComplaintCatalog,
  listComplaintScenarios,
  resolveComplaintScenario,
} from "./complaint-registry-scenarios.js";

test("lists every canonical complaint scenario", () => {
  const scenarios = listComplaintScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["open-follow-up", "critical-response", "resolved-history"],
  );
});

test("returns the default complaint scenario when the query is unknown", () => {
  const scenario = resolveComplaintScenario("unknown");

  assert.equal(scenario.id, "open-follow-up");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps complaints in attention for an open follow-up case", () => {
  const scenario = resolveComplaintScenario("open-follow-up");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.actions.map((item) => item.label).join(" "), /Resposta formal/i);
});

test("blocks the complaint registry when reissue and formal response remain pending", () => {
  const scenario = resolveComplaintScenario("critical-response");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /reemissao|cliente/i);
  assert.equal(scenario.detail.reissueReasonLabel, "DADO_CADASTRAL");
});

test("allows switching the selected complaint inside the same scenario", () => {
  const scenario = resolveComplaintScenario("resolved-history", "recl-004");

  assert.equal(scenario.selectedComplaintId, "recl-004");
  assert.equal(scenario.detail.complaintId, "recl-004");
});

test("builds the canonical complaint catalog with selected scenario", () => {
  const catalog = buildComplaintCatalog("critical-response", "recl-007");

  assert.equal(catalog.selectedScenarioId, "critical-response");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "critical-response")?.selectedComplaintId,
    "recl-007",
  );
});
