import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildInternalAuditCatalog,
  listInternalAuditScenarios,
  resolveInternalAuditScenario,
} from "./internal-audit-scenarios.js";

test("lists every canonical internal audit scenario", () => {
  const scenarios = listInternalAuditScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["program-on-track", "follow-up-attention", "extraordinary-escalation"],
  );
});

test("returns the default internal audit scenario when the query is unknown", () => {
  const scenario = resolveInternalAuditScenario("unknown");

  assert.equal(scenario.id, "follow-up-attention");
  assert.equal(scenario.detail.status, "attention");
});

test("keeps the audit module in attention while cycle findings remain open", () => {
  const scenario = resolveInternalAuditScenario("follow-up-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.findings.map((item) => item.title).join(" "), /NC-013|NC-014/i);
});

test("blocks the internal audit module when an extraordinary cycle is required", () => {
  const scenario = resolveInternalAuditScenario("extraordinary-escalation");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /extraordinaria|liberacao|trilha/i);
});

test("allows switching the selected cycle inside the same scenario", () => {
  const scenario = resolveInternalAuditScenario(
    "program-on-track",
    "audit-cycle-2026-2",
  );

  assert.equal(scenario.selectedCycleId, "audit-cycle-2026-2");
  assert.equal(scenario.detail.cycleId, "audit-cycle-2026-2");
});

test("builds the canonical internal audit catalog with selected scenario", () => {
  const catalog = buildInternalAuditCatalog(
    "extraordinary-escalation",
    "audit-cycle-extra-2026",
  );

  assert.equal(catalog.selectedScenarioId, "extraordinary-escalation");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(
    catalog.scenarios.find((scenario) => scenario.id === "extraordinary-escalation")
      ?.selectedCycleId,
    "audit-cycle-extra-2026",
  );
});
