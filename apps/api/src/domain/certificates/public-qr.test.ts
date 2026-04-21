import assert from "node:assert/strict";
import { test } from "node:test";

import { computeAuditHash, GENESIS_HASH, type AuditChainEntry } from "@afere/audit-log";

import { verifyPublicCertificateQrAuthenticity } from "./public-qr.js";

test("validates an authentic public QR when the token matches and the emitted certificate exists in the audit trail", () => {
  const result = verifyPublicCertificateQrAuthenticity({
    qrCodeUrl: "https://verificar.afere.test/public/certificate?certificate=cert-001&token=tok-abc",
    expectedHost: "verificar.afere.test",
    certificates: [
      {
        certificateId: "cert-001",
        certificateNumber: "ACME-000123",
        publicVerificationToken: "tok-abc",
        issuedAtUtc: "2026-04-21T14:00:00Z",
        revision: "R0",
        instrumentDescription: "Balanca IPNA 300 kg",
        serialNumber: "SN-42",
        customerName: "Cliente Sigiloso",
        resultSummary: "123,45 kg",
        expandedUncertainty: "0,12 kg",
      },
    ],
    auditEntries: buildAuditTrail([
      {
        action: "certificate.emitted",
        certificateId: "cert-001",
        timestampUtc: "2026-04-21T14:00:00Z",
      },
    ]),
  });

  assert.equal(result.ok, true);
  assert.equal(result.status, "authentic");
  assert.equal(result.reason, undefined);
  assert.equal(result.certificate?.certificateNumber, "ACME-000123");
});

test("marks the public QR as reissued when the certificate has controlled reissue evidence", () => {
  const result = verifyPublicCertificateQrAuthenticity({
    qrCodeUrl: "https://verificar.afere.test/public/certificate?certificate=cert-002&token=tok-r1",
    expectedHost: "verificar.afere.test",
    certificates: [
      {
        certificateId: "cert-002",
        certificateNumber: "ACME-000124",
        publicVerificationToken: "tok-r1",
        issuedAtUtc: "2026-04-20T09:00:00Z",
        reissuedAtUtc: "2026-04-21T16:00:00Z",
        replacementCertificateNumber: "ACME-000124-R1",
        revision: "R1",
        instrumentDescription: "Balanca IPNA 300 kg",
        serialNumber: "SN-99",
      },
    ],
    auditEntries: buildAuditTrail([
      {
        action: "certificate.emitted",
        certificateId: "cert-002",
        timestampUtc: "2026-04-20T09:00:00Z",
      },
      {
        action: "certificate.reissue.approved",
        certificateId: "cert-002",
        actorId: "reviewer-1",
        timestampUtc: "2026-04-21T15:00:00Z",
      },
      {
        action: "certificate.reissue.approved",
        certificateId: "cert-002",
        actorId: "reviewer-2",
        timestampUtc: "2026-04-21T15:05:00Z",
      },
      {
        action: "certificate.reissued",
        certificateId: "cert-002",
        previousCertificateHash: "a".repeat(64),
        previousRevision: "R0",
        newRevision: "R1",
      },
      {
        action: "certificate.reissue.notified",
        certificateId: "cert-002",
        recipient: "cliente@example.com",
        timestampUtc: "2026-04-21T16:01:00Z",
      },
    ]),
  });

  assert.equal(result.ok, true);
  assert.equal(result.status, "reissued");
  assert.equal(result.certificate?.replacementCertificateNumber, "ACME-000124-R1");
});

test("fails closed as not_found when the QR token is wrong or the audit trail is tampered", () => {
  const publishedCertificate = {
    certificateId: "cert-003",
    certificateNumber: "ACME-000125",
    publicVerificationToken: "tok-ok",
    issuedAtUtc: "2026-04-21T14:00:00Z",
    revision: "R0",
    instrumentDescription: "Balanca IPNA 300 kg",
    serialNumber: "SN-55",
  };

  const wrongToken = verifyPublicCertificateQrAuthenticity({
    qrCodeUrl: "https://verificar.afere.test/public/certificate?certificate=cert-003&token=tok-errado",
    expectedHost: "verificar.afere.test",
    certificates: [publishedCertificate],
    auditEntries: buildAuditTrail([
      {
        action: "certificate.emitted",
        certificateId: "cert-003",
        timestampUtc: "2026-04-21T14:00:00Z",
      },
    ]),
  });

  assert.equal(wrongToken.ok, false);
  assert.equal(wrongToken.status, "not_found");
  assert.equal(wrongToken.reason, "token_mismatch");

  const tamperedAudit = verifyPublicCertificateQrAuthenticity({
    qrCodeUrl: "https://verificar.afere.test/public/certificate?certificate=cert-003&token=tok-ok",
    expectedHost: "verificar.afere.test",
    certificates: [publishedCertificate],
    auditEntries: [
      {
        ...buildAuditTrail([
          {
            action: "certificate.emitted",
            certificateId: "cert-003",
            timestampUtc: "2026-04-21T14:00:00Z",
          },
        ])[0]!,
        hash: "f".repeat(64),
      },
    ],
  });

  assert.equal(tamperedAudit.ok, false);
  assert.equal(tamperedAudit.status, "not_found");
  assert.equal(tamperedAudit.reason, "invalid_audit_trail");
});

function buildAuditTrail(payloads: Array<Record<string, unknown>>): AuditChainEntry[] {
  let prevHash = GENESIS_HASH;

  return payloads.map((payload, index) => {
    const entry = {
      id: `evt-${index + 1}`,
      prevHash,
      payload,
      hash: computeAuditHash(prevHash, payload),
    };

    prevHash = entry.hash;
    return entry;
  });
}
