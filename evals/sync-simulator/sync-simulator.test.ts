import assert from "node:assert/strict";
import { test } from "node:test";

import { CANONICAL_SCENARIOS, runCanonicalScenario, runAllCanonicalScenarios } from "./engine/simulator";

test("runs all canonical C1-C8 sync scenarios deterministically", () => {
  const results = runAllCanonicalScenarios(3735928559);

  assert.deepEqual(
    results.map((result) => result.scenarioId),
    CANONICAL_SCENARIOS.map((scenario) => scenario.id),
  );
  assert.equal(results.length, 8);
  for (const result of results) {
    assert.equal(result.properties.converged, true, result.scenarioId);
    assert.equal(result.properties.hashChainValid, true, result.scenarioId);
    assert.equal(result.properties.signatureLockHeld, true, result.scenarioId);
    assert.equal(result.properties.idempotentReplay, true, result.scenarioId);
  }
});

test("runs 100 deterministic seeds across C1-C8", () => {
  for (let index = 0; index < 100; index += 1) {
    const seed = 3735928559 + index * 2654435761;
    const results = runAllCanonicalScenarios(seed);

    assert.equal(results.length, 8);
    for (const result of results) {
      assert.equal(result.properties.converged, true, `${result.scenarioId}:${seed}`);
      assert.equal(result.properties.hashChainValid, true, `${result.scenarioId}:${seed}`);
      assert.equal(result.properties.signatureLockHeld, true, `${result.scenarioId}:${seed}`);
      assert.equal(result.properties.idempotentReplay, true, `${result.scenarioId}:${seed}`);
    }
  }
});

test("C1 sends offline edit conflict to human review queue", () => {
  const result = runCanonicalScenario("C1", 3735928559);

  assert.equal(result.conflicts.length, 1);
  assert.equal(result.conflicts[0]?.status, "human_review_required");
  assert.equal(result.conflicts[0]?.class, "C1");
  assert.equal(result.canonicalState.workOrders.OS_001?.blockedForEmission, true);
});

test("C2 rejects edits after signature lock", () => {
  const result = runCanonicalScenario("C2", 3735928559);

  assert.equal(result.rejections.length, 1);
  assert.equal(result.rejections[0]?.code, "OS_LOCKED_FOR_SIGNATURE");
  assert.equal(result.canonicalState.workOrders.OS_001?.signedBy, "device-a");
});

test("C6 replay keeps server state and audit hash stable", () => {
  const result = runCanonicalScenario("C6", 3735928559);

  assert.equal(result.deduplicatedEvents, 1);
  assert.equal(result.properties.idempotentReplay, true);
  assert.equal(result.auditLog.length, 1);
});

test("C8 normalizes future client clock and records divergence", () => {
  const result = runCanonicalScenario("C8", 3735928559);

  assert.equal(result.clockSkewEvents.length, 1);
  assert.equal(result.clockSkewEvents[0]?.normalized, true);
  assert.equal(result.auditLog[0]?.payload.serverTime, 1);
});
