import assert from "node:assert/strict";
import { test } from "node:test";

import { offlineCertificateDraftSchema } from "../../../packages/contracts/src/mobile-offline-calibration.js";
import { buildOfflineSyncOutboxItem } from "./offline-sync.js";

const VALID_DRAFT = offlineCertificateDraftSchema.parse({
  sessionId: "session-android-0047",
  workOrderId: "os-2026-0047",
  certificateNumber: "AFR-000247",
  generatedOnDevice: true,
  syncState: "pending_sync",
  measurementCount: 5,
});

test("builds a ready outbox item when the draft, storage and replay protection are all valid", () => {
  const result = buildOfflineSyncOutboxItem({
    draft: VALID_DRAFT,
    workOrderNumber: "OS-2026-0047",
    deviceId: "device-field-01",
    deviceLabel: "Android campo 01",
    networkState: "online",
    queuedAtLabel: "22/04 08:10",
    lastAttemptLabel: "22/04 08:14",
    storageProtected: true,
    deviceKeyDerived: true,
    events: [
      {
        eventId: "evt-0047-a",
        clientEventId: "client-0047-a",
        aggregateLabel: "massa",
        eventKind: "edit",
        lamport: 1,
        payloadDigest: "sha256:evt-0047-a",
        state: "uploaded",
        replayProtected: true,
      },
      {
        eventId: "evt-0047-b",
        clientEventId: "client-0047-b",
        aggregateLabel: "assinatura",
        eventKind: "sign",
        lamport: 2,
        payloadDigest: "sha256:evt-0047-b",
        state: "deduplicated",
        replayProtected: true,
      },
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(result.item?.status, "ready");
  assert.equal(result.item?.replayProtectedCount, 2);
  assert.match(result.item?.storageLabel ?? "", /SQLCipher ativo/i);
});

test("fails closed when the device storage is not protected", () => {
  const result = buildOfflineSyncOutboxItem({
    draft: VALID_DRAFT,
    workOrderNumber: "OS-2026-0047",
    deviceId: "device-field-01",
    deviceLabel: "Android campo 01",
    networkState: "offline",
    queuedAtLabel: "22/04 08:10",
    lastAttemptLabel: "Aguardando",
    storageProtected: false,
    deviceKeyDerived: false,
    events: [
      {
        eventId: "evt-0047-a",
        clientEventId: "client-0047-a",
        aggregateLabel: "massa",
        eventKind: "edit",
        lamport: 1,
        payloadDigest: "sha256:evt-0047-a",
        state: "queued",
        replayProtected: true,
      },
    ],
  });

  assert.equal(result.ok, false);
  assert.equal(result.reason, "invalid_storage");
});

test("fails closed when any outbox event loses replay protection", () => {
  const result = buildOfflineSyncOutboxItem({
    draft: VALID_DRAFT,
    workOrderNumber: "OS-2026-0047",
    deviceId: "device-field-01",
    deviceLabel: "Android campo 01",
    networkState: "unstable",
    queuedAtLabel: "22/04 08:10",
    lastAttemptLabel: "22/04 08:12",
    storageProtected: true,
    deviceKeyDerived: true,
    pendingConflictClass: "C1",
    events: [
      {
        eventId: "evt-0047-a",
        clientEventId: "client-0047-a",
        aggregateLabel: "massa",
        eventKind: "edit",
        lamport: 1,
        payloadDigest: "sha256:evt-0047-a",
        state: "queued",
        replayProtected: false,
      },
    ],
  });

  assert.equal(result.ok, false);
  assert.equal(result.reason, "missing_replay_protection");
});

test("marks the outbox in attention when a human review conflict is pending", () => {
  const result = buildOfflineSyncOutboxItem({
    draft: VALID_DRAFT,
    workOrderNumber: "OS-2026-0047",
    deviceId: "device-field-01",
    deviceLabel: "Android campo 01",
    networkState: "online",
    queuedAtLabel: "22/04 08:10",
    lastAttemptLabel: "22/04 08:12",
    storageProtected: true,
    deviceKeyDerived: true,
    pendingConflictClass: "C1",
    events: [
      {
        eventId: "evt-0047-a",
        clientEventId: "client-0047-a",
        aggregateLabel: "massa",
        eventKind: "edit",
        lamport: 1,
        payloadDigest: "sha256:evt-0047-a",
        state: "uploaded",
        replayProtected: true,
      },
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(result.item?.status, "attention");
  assert.equal(result.item?.pendingConflictClass, "C1");
  assert.match(result.item?.blockers.join(" ") ?? "", /bloqueada para emissao/i);
});
