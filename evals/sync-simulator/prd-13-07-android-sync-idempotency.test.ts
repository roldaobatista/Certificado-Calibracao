import assert from "node:assert/strict";
import { test } from "node:test";

import { runCanonicalScenario } from "./engine/simulator";

const BASE_SEED = 3735928559;
const KNUTH_GOLDEN_RATIO = 2654435761;

function deterministicSeeds(count = 100) {
  return Array.from({ length: count }, (_, index) => BASE_SEED + index * KNUTH_GOLDEN_RATIO);
}

test("PRD §13.7: sync converges after network loss and replay remains idempotent", () => {
  for (const seed of deterministicSeeds()) {
    const partitionResult = runCanonicalScenario("C5", seed);
    const replayResult = runCanonicalScenario("C6", seed);

    assert.equal(partitionResult.properties.converged, true, `C5 must converge after partition heal (${seed})`);
    assert.equal(partitionResult.properties.hashChainValid, true, `C5 hash-chain must stay valid (${seed})`);
    assert.equal(partitionResult.rejections.length, 0, `C5 must not reject healthy edits after reconnect (${seed})`);
    assert.equal(partitionResult.conflicts.length, 0, `C5 must merge independent aggregates without manual review (${seed})`);
    assert.deepEqual(partitionResult.canonicalState.workOrders.OS_001?.fields, {
      humidity: "50",
      pressure: "101.3",
      temperature: "20.1",
    });

    assert.equal(replayResult.properties.idempotentReplay, true, `C6 replay must stay idempotent (${seed})`);
    assert.equal(replayResult.deduplicatedEvents, 1, `C6 must deduplicate replayed event (${seed})`);
    assert.equal(replayResult.auditLog.length, 1, `C6 replay must not duplicate audit entry (${seed})`);
    assert.deepEqual(replayResult.canonicalState.workOrders.OS_001?.fields, {
      mass: "10.04",
    });
  }
});

test("PRD §13.7: offline conflict on reconnect is fail-closed instead of silently dropping risk", () => {
  const result = runCanonicalScenario("C1", BASE_SEED);

  assert.equal(result.conflicts.length, 1);
  assert.equal(result.conflicts[0]?.status, "human_review_required");
  assert.equal(result.conflicts[0]?.class, "C1");
  assert.equal(result.canonicalState.workOrders.OS_001?.blockedForEmission, true);
  assert.equal(result.properties.hashChainValid, true);
});
