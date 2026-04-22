import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildRiskRegisterCatalog,
  listRiskRegisterScenarios,
  resolveRiskRegisterScenario,
} from "./risk-register-scenarios.js";

test("lists every canonical risk register scenario", () => {
  const scenarios = listRiskRegisterScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["annual-declarations", "commercial-pressure", "stable-monitoring"],
  );
});

test("returns the default risk register scenario when the query is unknown", () => {
  const scenario = resolveRiskRegisterScenario("unknown");

  assert.equal(scenario.id, "annual-declarations");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps the register in attention while annual declarations remain pending", () => {
  const scenario = resolveRiskRegisterScenario("annual-declarations");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.actions.map((item) => item.label).join(" "), /declaracoes|assinatura/i);
  assert.equal(scenario.summary.pendingDeclarationCount, 1);
});

test("blocks the register when commercial pressure remains unresolved", () => {
  const scenario = resolveRiskRegisterScenario("commercial-pressure");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /direcao|NC-015|reclamacao/i);
  assert.equal(scenario.detail.links.nonconformityId, "nc-015");
});

test("allows switching the selected risk inside the same scenario", () => {
  const scenario = resolveRiskRegisterScenario("stable-monitoring", "risk-003");

  assert.equal(scenario.selectedRiskId, "risk-003");
  assert.equal(scenario.detail.riskId, "risk-003");
});

test("builds the canonical risk register catalog with selected scenario", () => {
  const catalog = buildRiskRegisterCatalog("commercial-pressure", "risk-001");

  assert.equal(catalog.selectedScenarioId, "commercial-pressure");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "commercial-pressure")?.selectedRiskId,
    "risk-001",
  );
});
