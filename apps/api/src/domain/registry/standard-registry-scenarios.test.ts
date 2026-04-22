import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildStandardRegistryCatalog,
  listStandardRegistryScenarios,
  resolveStandardRegistryScenario,
} from "./standard-registry-scenarios.js";

test("lists every canonical standard registry scenario", () => {
  const scenarios = listStandardRegistryScenarios();

  assert.equal(scenarios.length, 3);
  assert.deepEqual(
    scenarios.map((scenario) => scenario.id),
    ["operational-ready", "expiration-attention", "expired-blocked"],
  );
});

test("returns the default standard registry scenario when the query is unknown", () => {
  const scenario = resolveStandardRegistryScenario("unknown");

  assert.equal(scenario.id, "operational-ready");
  assert.equal(scenario.detail.status, "ready");
});

test("keeps the standard registry in attention when the selected standard is near expiration", () => {
  const scenario = resolveStandardRegistryScenario("expiration-attention");

  assert.equal(scenario.detail.status, "attention");
  assert.match(scenario.detail.noticeLabel, /vence em 2 dia/i);
  assert.equal(scenario.summary.expiringSoonCount, 1);
});

test("blocks the standard registry when the selected standard is expired", () => {
  const scenario = resolveStandardRegistryScenario("expired-blocked");

  assert.equal(scenario.detail.status, "blocked");
  assert.match(scenario.detail.blockers.join(" "), /vencido/i);
  assert.equal(scenario.summary.expiredCount, 1);
});

test("allows switching the selected standard inside the same scenario", () => {
  const scenario = resolveStandardRegistryScenario("operational-ready", "standard-002");

  assert.equal(scenario.selectedStandardId, "standard-002");
  assert.equal(scenario.detail.standardId, "standard-002");
  assert.match(scenario.detail.title, /PESO-002/i);
});

test("builds the canonical standard registry catalog with selected scenario", () => {
  const catalog = buildStandardRegistryCatalog("expiration-attention");

  assert.equal(catalog.selectedScenarioId, "expiration-attention");
  assert.equal(catalog.scenarios.length, 3);
});
