import assert from "node:assert/strict";
import { test } from "node:test";

import { buildOfflineSyncCatalog, listOfflineSyncScenarios, resolveOfflineSyncScenario } from "./offline-sync-scenarios.js";

test("lists the canonical offline sync scenarios for V2", () => {
  const scenarios = listOfflineSyncScenarios();

  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["stable-upload", "human-review-open", "regulator-escalated"],
  );
});

test("keeps the human review scenario open and blocking emission while C1 is unresolved", () => {
  const scenario = resolveOfflineSyncScenario("human-review-open");

  assert.equal(scenario.summary.status, "attention");
  assert.equal(scenario.detail.class, "C1");
  assert.equal(scenario.detail.status, "open");
  assert.equal(scenario.detail.blockedForEmission, true);
  assert.equal(scenario.outboxItems.find((item) => item.itemId === scenario.selectedOutboxItemId)?.pendingConflictClass, "C1");
});

test("keeps the regulator escalated scenario fail-closed for C4", () => {
  const scenario = resolveOfflineSyncScenario("regulator-escalated");

  assert.equal(scenario.summary.status, "blocked");
  assert.equal(scenario.detail.class, "C4");
  assert.equal(scenario.detail.regulatorEscalationRequired, true);
  assert.equal(
    scenario.detail.resolutionOptions.find((option) => option.action === "escalate_to_regulator")?.allowed,
    true,
  );
  assert.equal(
    scenario.detail.resolutionOptions.filter((option) => option.action !== "escalate_to_regulator" && option.allowed)
      .length,
    0,
  );
});

test("builds a typed catalog centered on the selected sync scenario", () => {
  const catalog = buildOfflineSyncCatalog("human-review-open", "sync-os-2026-0047", "conflict-c1-0047");

  assert.equal(catalog.selectedScenarioId, "human-review-open");
  assert.equal(catalog.scenarios.length, 3);
  assert.equal(catalog.scenarios.find((scenario) => scenario.id === "human-review-open")?.detail.conflictId, "conflict-c1-0047");
});
