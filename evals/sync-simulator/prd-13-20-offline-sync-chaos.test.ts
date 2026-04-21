import assert from "node:assert/strict";
import { test } from "node:test";

import * as simulator from "./engine/simulator";

type ChaosOptions = {
  seed: number;
  workOrderCount: number;
  deviceCount: number;
};

type ChaosReport = {
  seed: number;
  workOrderCount: number;
  deviceCount: number;
  expectedAcceptedEvents: number;
  acceptedEvents: number;
  replayEventsInjected: number;
  duplicateReplaysDetected: number;
  auditLogLength: number;
  missingWorkOrders: string[];
  properties: {
    converged: boolean;
    hashChainValid: boolean;
    idempotentReplay: boolean;
  };
};

const CHAOS_SEEDS = [3735928559, 3405691582, 324508639];

test("PRD §13.20: chaos sync processes 1000 OS in 5 devices without loss or duplicate acceptance", () => {
  const runOfflineSyncChaos = (simulator as { runOfflineSyncChaos?: (options: ChaosOptions) => ChaosReport }).runOfflineSyncChaos;

  assert.equal(
    typeof runOfflineSyncChaos,
    "function",
    "runOfflineSyncChaos must be exported by evals/sync-simulator/engine/simulator.ts",
  );

  for (const seed of CHAOS_SEEDS) {
    const report = runOfflineSyncChaos({
      seed,
      workOrderCount: 1000,
      deviceCount: 5,
    });

    assert.equal(report.workOrderCount, 1000, `workOrderCount mismatch for seed ${seed}`);
    assert.equal(report.deviceCount, 5, `deviceCount mismatch for seed ${seed}`);
    assert.equal(report.acceptedEvents, report.expectedAcceptedEvents, `acceptedEvents mismatch for seed ${seed}`);
    assert.equal(report.duplicateReplaysDetected, report.replayEventsInjected, `replay dedup mismatch for seed ${seed}`);
    assert.equal(report.auditLogLength, report.expectedAcceptedEvents, `audit log length mismatch for seed ${seed}`);
    assert.deepEqual(report.missingWorkOrders, [], `missing work orders for seed ${seed}`);
    assert.equal(report.properties.converged, true, `convergence failure for seed ${seed}`);
    assert.equal(report.properties.hashChainValid, true, `hash-chain failure for seed ${seed}`);
    assert.equal(report.properties.idempotentReplay, true, `idempotent replay failure for seed ${seed}`);
  }
});
