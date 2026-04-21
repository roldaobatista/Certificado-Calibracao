import assert from "node:assert/strict";
import { test } from "node:test";

import { GENESIS_HASH, computeAuditHash, type AuditChainEntry } from "./verify.js";
import { verifyCriticalEventAuditTrail } from "./critical-events.js";

function eventEntry(id: string, prevHash: string, action: string): AuditChainEntry {
  const payload = {
    action,
    actorId: "user-1",
    timestampUtc: "2026-04-21T10:00:00Z",
    deviceId: "device-1",
  };

  return {
    id,
    prevHash,
    payload,
    hash: computeAuditHash(prevHash, payload),
  };
}

test("accepts an audit trail containing the critical events for calibration, review, signature and emission", () => {
  const calibration = eventEntry("evt-1", GENESIS_HASH, "calibration.executed");
  const review = eventEntry("evt-2", calibration.hash, "technical_review.completed");
  const signature = eventEntry("evt-3", review.hash, "certificate.signed");
  const emission = eventEntry("evt-4", signature.hash, "certificate.emitted");

  const result = verifyCriticalEventAuditTrail([calibration, review, signature, emission]);

  assert.equal(result.ok, true);
  assert.deepEqual(result.missingActions, []);
  assert.equal(result.hashChain.ok, true);
});

test("fails closed when a required critical event is missing even if the hash-chain is valid", () => {
  const calibration = eventEntry("evt-1", GENESIS_HASH, "calibration.executed");
  const signature = eventEntry("evt-2", calibration.hash, "certificate.signed");
  const emission = eventEntry("evt-3", signature.hash, "certificate.emitted");

  const result = verifyCriticalEventAuditTrail([calibration, signature, emission]);

  assert.equal(result.ok, false);
  assert.deepEqual(result.missingActions, ["technical_review.completed"]);
  assert.equal(result.hashChain.ok, true);
});

test("fails when the underlying hash-chain is invalid or when reissue is required but absent", () => {
  const calibration = eventEntry("evt-1", GENESIS_HASH, "calibration.executed");
  const review = eventEntry("evt-2", calibration.hash, "technical_review.completed");
  const signature = eventEntry("evt-3", review.hash, "certificate.signed");
  const tamperedEmission = {
    ...eventEntry("evt-4", "f".repeat(64), "certificate.emitted"),
  };

  const tamperedResult = verifyCriticalEventAuditTrail([calibration, review, signature, tamperedEmission]);
  assert.equal(tamperedResult.ok, false);
  assert.equal(tamperedResult.hashChain.ok, false);

  const emission = eventEntry("evt-4", signature.hash, "certificate.emitted");
  const noReissueResult = verifyCriticalEventAuditTrail([calibration, review, signature, emission], {
    requireReissue: true,
  });
  assert.equal(noReissueResult.ok, false);
  assert.deepEqual(noReissueResult.missingActions, ["certificate.reissued"]);
});
