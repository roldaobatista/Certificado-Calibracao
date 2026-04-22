import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildAuditTrailCatalog,
  listAuditTrailScenarios,
  resolveAuditTrailScenario,
} from "./audit-trail-scenarios.js";

test("lists every canonical audit trail scenario", () => {
  const scenarios = listAuditTrailScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["recent-emission", "reissue-attention", "integrity-blocked"],
  );
});

test("returns the default audit trail scenario when the query is unknown", () => {
  const scenario = resolveAuditTrailScenario("unknown");

  assert.equal(scenario.id, "recent-emission");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps the audit trail in attention when the selected chain contains a controlled reissue", () => {
  const scenario = resolveAuditTrailScenario("reissue-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.warnings.join(" "), /reemissao controlada/i);
  assert.equal(scenario.summary.reissueEvents >= 3, true);
});

test("blocks the audit trail when hash-chain integrity diverges", () => {
  const scenario = resolveAuditTrailScenario("integrity-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /Hash-chain divergente/i);
  assert.equal(scenario.summary.integrityFailures, 1);
});

test("allows switching the selected event inside the same scenario", () => {
  const scenario = resolveAuditTrailScenario("recent-emission", "audit-2");

  assert.equal(scenario.selectedEventId, "audit-2");
  assert.equal(scenario.detail.selectedActionLabel, "Todas");
  assert.match(
    scenario.items.find((item) => item.eventId === "audit-2")?.actionLabel ?? "",
    /technical_review/i,
  );
});

test("builds the canonical audit trail catalog with selected scenario", () => {
  const catalog = buildAuditTrailCatalog("reissue-attention");

  assert.equal(catalog.selectedScenarioId, "reissue-attention");
  assert.equal(catalog.scenarios.length, 3);
});
