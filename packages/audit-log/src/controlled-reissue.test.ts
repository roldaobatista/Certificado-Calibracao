import assert from "node:assert/strict";
import { test } from "node:test";

import { GENESIS_HASH, computeAuditHash, type AuditChainEntry } from "./verify.js";
import { verifyControlledReissueAuditTrail } from "./controlled-reissue.js";

function eventEntry(
  id: string,
  prevHash: string,
  payload: Record<string, unknown>,
): AuditChainEntry {
  return {
    id,
    prevHash,
    payload,
    hash: computeAuditHash(prevHash, payload),
  };
}

test("accepts a controlled reissue trail with two distinct approvals, preserved hash and client notification", () => {
  const approvalOne = eventEntry("evt-1", GENESIS_HASH, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-a",
    timestampUtc: "2026-04-21T12:00:00Z",
  });
  const approvalTwo = eventEntry("evt-2", approvalOne.hash, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-b",
    timestampUtc: "2026-04-21T12:05:00Z",
  });
  const reissued = eventEntry("evt-3", approvalTwo.hash, {
    action: "certificate.reissued",
    previousCertificateHash: "a".repeat(64),
    previousRevision: "R1",
    newRevision: "R2",
  });
  const notified = eventEntry("evt-4", reissued.hash, {
    action: "certificate.reissue.notified",
    recipient: "cliente@example.com",
    timestampUtc: "2026-04-21T12:10:00Z",
  });

  const result = verifyControlledReissueAuditTrail([approvalOne, approvalTwo, reissued, notified]);

  assert.equal(result.ok, true);
  assert.equal(result.hashChain.ok, true);
  assert.deepEqual(result.approvalErrors, []);
  assert.deepEqual(result.missingActions, []);
  assert.deepEqual(result.sequenceErrors, []);
  assert.deepEqual(result.invalidEntries, []);
});

test("fails closed when approvals are fewer than two or not distinct before reissue", () => {
  const approvalOne = eventEntry("evt-1", GENESIS_HASH, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-a",
    timestampUtc: "2026-04-21T12:00:00Z",
  });
  const approvalTwo = eventEntry("evt-2", approvalOne.hash, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-a",
    timestampUtc: "2026-04-21T12:05:00Z",
  });
  const reissued = eventEntry("evt-3", approvalTwo.hash, {
    action: "certificate.reissued",
    previousCertificateHash: "a".repeat(64),
    previousRevision: "R1",
    newRevision: "R2",
  });
  const notified = eventEntry("evt-4", reissued.hash, {
    action: "certificate.reissue.notified",
    recipient: "cliente@example.com",
    timestampUtc: "2026-04-21T12:10:00Z",
  });

  const result = verifyControlledReissueAuditTrail([approvalOne, approvalTwo, reissued, notified]);

  assert.equal(result.ok, false);
  assert.deepEqual(result.approvalErrors, ["approvers_not_distinct"]);

  const oneApprovalOnly = verifyControlledReissueAuditTrail([approvalOne, reissued, notified]);
  assert.equal(oneApprovalOnly.ok, false);
  assert.deepEqual(oneApprovalOnly.approvalErrors, ["approvals_below_minimum"]);
});

test("fails closed when reissue metadata is invalid, notification is absent or ordering is broken", () => {
  const approvalOne = eventEntry("evt-1", GENESIS_HASH, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-a",
    timestampUtc: "2026-04-21T12:00:00Z",
  });
  const approvalTwo = eventEntry("evt-2", approvalOne.hash, {
    action: "certificate.reissue.approved",
    actorId: "reviewer-b",
    timestampUtc: "2026-04-21T12:05:00Z",
  });
  const invalidReissued = eventEntry("evt-3", approvalTwo.hash, {
    action: "certificate.reissued",
    previousCertificateHash: "bad-hash",
    previousRevision: "R1",
    newRevision: "R4",
  });

  const missingNotification = verifyControlledReissueAuditTrail([approvalOne, approvalTwo, invalidReissued]);
  assert.equal(missingNotification.ok, false);
  assert.deepEqual(missingNotification.missingActions, ["certificate.reissue.notified"]);
  assert.deepEqual(missingNotification.invalidEntries, [
    {
      id: "evt-3",
      action: "certificate.reissued",
      missingFields: [],
      invalidFields: ["previousCertificateHash", "newRevision"],
    },
  ]);

  const earlyNotification = eventEntry("evt-3", approvalTwo.hash, {
    action: "certificate.reissue.notified",
    recipient: "cliente@example.com",
    timestampUtc: "2026-04-21T12:06:00Z",
  });
  const validReissued = eventEntry("evt-4", earlyNotification.hash, {
    action: "certificate.reissued",
    previousCertificateHash: "b".repeat(64),
    previousRevision: "R1",
    newRevision: "R2",
  });

  const outOfOrder = verifyControlledReissueAuditTrail([approvalOne, approvalTwo, earlyNotification, validReissued]);
  assert.equal(outOfOrder.ok, false);
  assert.deepEqual(outOfOrder.sequenceErrors, ["notification_must_follow_reissue"]);
});
