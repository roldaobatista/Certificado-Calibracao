import assert from "node:assert/strict";
import { test } from "node:test";

import { GENESIS_HASH, computeAuditHash, type AuditChainEntry } from "./verify.js";
import { verifyTechnicalReviewSignatureAudit } from "./review-signature-audit.js";

function eventEntry(
  id: string,
  prevHash: string,
  action: string,
  overrides: Partial<Record<"actorId" | "timestampUtc" | "deviceId", unknown>> = {},
): AuditChainEntry {
  const payload = {
    action,
    actorId: "user-1",
    timestampUtc: "2026-04-21T10:00:00Z",
    deviceId: "device-1",
    ...overrides,
  };

  return {
    id,
    prevHash,
    payload,
    hash: computeAuditHash(prevHash, payload),
  };
}

test("accepts technical review and signature events when identity, timestamp and device are present", () => {
  const review = eventEntry("evt-1", GENESIS_HASH, "technical_review.completed");
  const signature = eventEntry("evt-2", review.hash, "certificate.signed");

  const result = verifyTechnicalReviewSignatureAudit([review, signature]);

  assert.equal(result.ok, true);
  assert.equal(result.hashChain.ok, true);
  assert.deepEqual(result.missingActions, []);
  assert.deepEqual(result.invalidEntries, []);
});

test("fails closed when technical review or signature is absent from the audit trail", () => {
  const review = eventEntry("evt-1", GENESIS_HASH, "technical_review.completed");

  const result = verifyTechnicalReviewSignatureAudit([review]);

  assert.equal(result.ok, false);
  assert.equal(result.hashChain.ok, true);
  assert.deepEqual(result.missingActions, ["certificate.signed"]);
  assert.deepEqual(result.invalidEntries, []);
});

test("fails closed when required metadata is missing, malformed or when the hash-chain is tampered", () => {
  const review = eventEntry("evt-1", GENESIS_HASH, "technical_review.completed", {
    timestampUtc: "2026-04-21 10:00:00",
  });
  const signature = eventEntry("evt-2", review.hash, "certificate.signed", {
    deviceId: "",
  });

  const metadataResult = verifyTechnicalReviewSignatureAudit([review, signature]);

  assert.equal(metadataResult.ok, false);
  assert.equal(metadataResult.hashChain.ok, true);
  assert.deepEqual(metadataResult.invalidEntries, [
    {
      id: "evt-1",
      action: "technical_review.completed",
      missingFields: [],
      invalidFields: ["timestampUtc"],
    },
    {
      id: "evt-2",
      action: "certificate.signed",
      missingFields: ["deviceId"],
      invalidFields: [],
    },
  ]);

  const validReview = eventEntry("evt-1", GENESIS_HASH, "technical_review.completed");
  const tamperedSignature = {
    ...eventEntry("evt-2", "f".repeat(64), "certificate.signed"),
  };

  const tamperedResult = verifyTechnicalReviewSignatureAudit([validReview, tamperedSignature]);
  assert.equal(tamperedResult.ok, false);
  assert.equal(tamperedResult.hashChain.ok, false);
});
