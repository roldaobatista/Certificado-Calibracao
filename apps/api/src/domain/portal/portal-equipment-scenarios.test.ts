import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildPortalEquipmentCatalog,
  listPortalEquipmentScenarios,
  resolvePortalEquipmentScenario,
} from "./portal-equipment-scenarios.js";

test("lists every canonical portal equipment scenario", () => {
  const scenarios = listPortalEquipmentScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["stable-portfolio", "expiring-soon", "overdue-blocked"],
  );
});

test("returns the default portal equipment scenario when the query is unknown", () => {
  const scenario = resolvePortalEquipmentScenario("unknown");

  assert.equal(scenario.id, "stable-portfolio");
  assert.equal(scenario.selectedEquipmentId, "equipment-bal-007");
});

test("keeps the portal equipment detail blocked when the selected item is overdue", () => {
  const scenario = resolvePortalEquipmentScenario("overdue-blocked", "equipment-bal-019");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /sem calibracao valida/i);
  assert.equal(scenario.detail.certificateHistory[0]?.verifyScenarioId, "reissued");
});

test("builds the canonical portal equipment catalog with selected equipment", () => {
  const catalog = buildPortalEquipmentCatalog("expiring-soon", "equipment-bal-012");
  const selectedScenario = catalog.scenarios.find((scenario) => scenario.id === "expiring-soon");

  assert.equal(catalog.selectedScenarioId, "expiring-soon");
  assert.ok(selectedScenario);
  assert.equal(selectedScenario.selectedEquipmentId, "equipment-bal-012");
  assert.equal(selectedScenario.detail.equipmentId, "equipment-bal-012");
});
