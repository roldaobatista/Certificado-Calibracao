import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildSignatureQueueCatalog,
  listSignatureQueueScenarios,
  resolveSignatureQueueScenario,
} from "./signature-queue-scenarios.js";

test("lists every canonical signature queue scenario", () => {
  const scenarios = listSignatureQueueScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["approved-ready", "attention-required", "mfa-blocked"],
  );
});

test("returns the default signature queue scenario when the query is unknown", () => {
  const scenario = resolveSignatureQueueScenario("unknown");

  assert.equal(scenario.id, "approved-ready");
  assert.equal(scenario.summary.status, "ready");
  assert.equal(scenario.approval.canSign, true);
});

test("marks the queue item as attention when the preview suppresses the symbol", () => {
  const scenario = resolveSignatureQueueScenario("attention-required");
  const selectedItem = scenario.items.find((item) => item.itemId === scenario.selectedItemId);

  assert.ok(selectedItem);
  assert.equal(selectedItem.status, "attention");
  assert.match(selectedItem.warnings.join(" "), /suprimido/i);
  assert.equal(scenario.approval.canSign, true);
});

test("blocks signing when MFA and preview gates are not satisfied", () => {
  const scenario = resolveSignatureQueueScenario("mfa-blocked");

  assert.equal(scenario.summary.status, "blocked");
  assert.equal(scenario.approval.canSign, false);
  assert.match(scenario.approval.blockers.join(" "), /MFA/i);
});

test("allows switching the selected queue item within the same scenario", () => {
  const scenario = resolveSignatureQueueScenario("approved-ready", "os-2026-00138");

  assert.equal(scenario.selectedItemId, "os-2026-00138");
  assert.match(scenario.approval.title, /00138/);
});

test("builds the canonical signature queue catalog with selected scenario", () => {
  const catalog = buildSignatureQueueCatalog("attention-required");

  assert.equal(catalog.selectedScenarioId, "attention-required");
  assert.equal(catalog.scenarios.length, 3);
});
