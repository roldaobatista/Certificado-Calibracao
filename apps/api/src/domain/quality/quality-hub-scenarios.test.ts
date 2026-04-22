import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildQualityHubCatalog,
  listQualityHubScenarios,
  resolveQualityHubScenario,
} from "./quality-hub-scenarios.js";

test("lists every canonical quality hub scenario", () => {
  const scenarios = listQualityHubScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-attention", "critical-response", "stable-baseline"],
  );
});

test("returns the default quality hub scenario when the query is unknown", () => {
  const scenario = resolveQualityHubScenario("unknown");

  assert.equal(scenario.id, "operational-attention");
  assert.equal(scenario.summary.status, "attention");
});

test("keeps the hub in attention while distinguishing implemented and planned areas", () => {
  const scenario = resolveQualityHubScenario("operational-attention");

  assert.equal(scenario.selectedModuleKey, "nonconformities");
  assert.equal(scenario.summary.implementedModuleCount, 3);
  assert.equal(scenario.summary.plannedModuleCount, 6);
  assert.equal(scenario.modules.find((module) => module.key === "complaints")?.availability, "implemented");
  assert.match(
    scenario.modules.find((module) => module.key === "complaints")?.href ?? "",
    /quality\/complaints/i,
  );
});

test("blocks the quality hub when the audit trail integrity fails closed", () => {
  const scenario = resolveQualityHubScenario("critical-response", "audit-trail");

  assert.equal(scenario.selectedModuleKey, "audit-trail");
  assert.equal(scenario.summary.status, "blocked");
  assert.match(scenario.summary.blockers.join(" "), /integridade|NC critica/i);
  assert.match(
    scenario.modules.find((module) => module.key === "audit-trail")?.blockers.join(" ") ?? "",
    /Hash-chain/i,
  );
});

test("allows switching the selected module inside the same scenario", () => {
  const scenario = resolveQualityHubScenario("stable-baseline", "documents");

  assert.equal(scenario.selectedModuleKey, "documents");
  assert.equal(scenario.modules.find((module) => module.key === "documents")?.availability, "planned");
});

test("builds the canonical quality hub catalog with selected scenario", () => {
  const catalog = buildQualityHubCatalog("critical-response", "nonconformities");

  assert.equal(catalog.selectedScenarioId, "critical-response");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(catalog.scenarios.find((scenario) => scenario.id === "critical-response")?.selectedModuleKey, "nonconformities");
});
