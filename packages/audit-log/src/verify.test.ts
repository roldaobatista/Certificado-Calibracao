import assert from "node:assert/strict";
import { test } from "node:test";
import { GENESIS_HASH, computeAuditHash, verifyAuditHashChain, type AuditChainEntry } from "./verify.js";

function entry(id: string, prevHash: string, payload: unknown): AuditChainEntry {
  return {
    id,
    prevHash,
    payload,
    hash: computeAuditHash(prevHash, payload),
  };
}

test("verifies a valid append-only audit hash chain", () => {
  const first = entry("evt-1", GENESIS_HASH, { action: "certificate.created", organizationId: "org-a" });
  const second = entry("evt-2", first.hash, { action: "certificate.approved", organizationId: "org-a" });

  const result = verifyAuditHashChain([first, second]);

  assert.equal(result.ok, true);
  assert.equal(result.checked, 2);
  assert.equal(result.firstInvalid, undefined);
});

test("detects tampered payload at the first divergent record", () => {
  const first = entry("evt-1", GENESIS_HASH, { action: "certificate.created", organizationId: "org-a" });
  const second = entry("evt-2", first.hash, { action: "certificate.approved", organizationId: "org-a" });
  const tampered = { ...second, payload: { action: "certificate.rejected", organizationId: "org-a" } };

  const result = verifyAuditHashChain([first, tampered]);

  assert.equal(result.ok, false);
  assert.equal(result.checked, 2);
  assert.equal(result.firstInvalid?.index, 1);
  assert.equal(result.firstInvalid?.id, "evt-2");
  assert.equal(result.firstInvalid?.reason, "hash_mismatch");
});

test("detects broken prevHash linkage before recomputing payload hash", () => {
  const first = entry("evt-1", GENESIS_HASH, { action: "certificate.created", organizationId: "org-a" });
  const second = entry("evt-2", "f".repeat(64), { action: "certificate.approved", organizationId: "org-a" });

  const result = verifyAuditHashChain([first, second]);

  assert.equal(result.ok, false);
  assert.equal(result.firstInvalid?.index, 1);
  assert.equal(result.firstInvalid?.reason, "prev_hash_mismatch");
  assert.equal(result.firstInvalid?.expectedPrevHash, first.hash);
});

test("canonicalizes payload object keys before hashing", () => {
  const hashA = computeAuditHash(GENESIS_HASH, { b: 2, a: { d: 4, c: 3 } });
  const hashB = computeAuditHash(GENESIS_HASH, { a: { c: 3, d: 4 }, b: 2 });

  assert.equal(hashA, hashB);
});
