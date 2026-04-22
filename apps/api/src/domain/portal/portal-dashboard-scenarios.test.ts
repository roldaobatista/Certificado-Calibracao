import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildPortalDashboardCatalog,
  listPortalDashboardScenarios,
  resolvePortalDashboardScenario,
} from "./portal-dashboard-scenarios.js";

test("lists every canonical portal dashboard scenario", () => {
  const scenarios = listPortalDashboardScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["stable-portfolio", "expiring-soon", "overdue-blocked"],
  );
});

test("returns the default portal dashboard scenario when the query is unknown", () => {
  const scenario = resolvePortalDashboardScenario("unknown");

  assert.equal(scenario.id, "stable-portfolio");
  assert.equal(scenario.summary.status, "ready");
});

test("keeps the portal dashboard blocked when an equipment is overdue", () => {
  const scenario = resolvePortalDashboardScenario("overdue-blocked");

  assert.equal(scenario.summary.status, "blocked");
  assert.match(scenario.summary.blockers.join(" "), /BAL-019/i);
  assert.equal(scenario.expiringEquipments.some((item) => item.status === "blocked"), true);
});

test("builds the canonical portal dashboard catalog with selected scenario", () => {
  const catalog = buildPortalDashboardCatalog("expiring-soon");

  assert.equal(catalog.selectedScenarioId, "expiring-soon");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "expiring-soon")?.summary.expiringSoonCount,
    3,
  );
});
