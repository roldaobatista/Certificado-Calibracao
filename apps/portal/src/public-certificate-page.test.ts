import assert from "node:assert/strict";
import { test } from "node:test";

import { buildPublicCertificatePageModel } from "./public-certificate-page.js";

test("renders only the minimal public metadata for an authentic certificate", () => {
  const page = buildPublicCertificatePageModel({
    ok: true,
    status: "authentic",
    certificate: {
      certificateId: "cert-001",
      certificateNumber: "ACME-000123",
      issuedAtUtc: "2026-04-21T14:00:00Z",
      revision: "R0",
      instrumentDescription: "Balanca IPNA 300 kg",
      serialNumber: "SN-42",
      customerName: "Cliente Sigiloso",
      customerAddress: "Rua Interna, 123",
      resultSummary: "123,45 kg",
      expandedUncertainty: "0,12 kg",
      publicVerificationToken: "tok-abc",
      auditTrailHash: "a".repeat(64),
    },
  });

  assert.equal(page.status, "authentic");
  assert.equal(page.title, "Certificado autentico");
  assert.deepEqual(page.publicMetadata, {
    certificateNumber: "ACME-000123",
    issuedAtUtc: "2026-04-21T14:00:00Z",
    revision: "R0",
    instrumentDescription: "Balanca IPNA 300 kg",
    serialNumber: "SN-42",
  });
});

test("renders reissued certificates with minimal replacement metadata only", () => {
  const page = buildPublicCertificatePageModel({
    ok: true,
    status: "reissued",
    certificate: {
      certificateNumber: "ACME-000124",
      issuedAtUtc: "2026-04-20T09:00:00Z",
      revision: "R1",
      instrumentDescription: "Balanca IPNA 300 kg",
      serialNumber: "SN-99",
      reissuedAtUtc: "2026-04-21T16:00:00Z",
      replacementCertificateNumber: "ACME-000124-R1",
      customerName: "Cliente Sigiloso",
      actorId: "signer-1",
    },
  });

  assert.equal(page.status, "reissued");
  assert.equal(page.title, "Certificado reemitido");
  assert.deepEqual(page.publicMetadata, {
    certificateNumber: "ACME-000124",
    issuedAtUtc: "2026-04-20T09:00:00Z",
    revision: "R1",
    instrumentDescription: "Balanca IPNA 300 kg",
    serialNumber: "SN-99",
    reissuedAtUtc: "2026-04-21T16:00:00Z",
    replacementCertificateNumber: "ACME-000124-R1",
  });
});

test("renders not_found without exposing any metadata", () => {
  const page = buildPublicCertificatePageModel({
    ok: false,
    status: "not_found",
    reason: "certificate_not_found",
  });

  assert.equal(page.status, "not_found");
  assert.equal(page.title, "Certificado nao localizado");
  assert.deepEqual(page.publicMetadata, {});
});
