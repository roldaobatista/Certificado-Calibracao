import assert from "node:assert/strict";
import { test } from "node:test";

import { reserveSequentialCertificateNumber } from "./certificate-numbering.js";

test("reserves the next sequential certificate number for the same organization", () => {
  const result = reserveSequentialCertificateNumber({
    organizationId: "org-acme",
    organizationCode: "ACME",
    issuedNumbers: [
      { organizationId: "org-acme", certificateNumber: "ACME-000001" },
      { organizationId: "org-acme", certificateNumber: "ACME-000002" },
      { organizationId: "org-beta", certificateNumber: "BETA-000001" },
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(result.nextSequence, 3);
  assert.equal(result.certificateNumber, "ACME-000003");
  assert.deepEqual(result.errors, []);
});

test("keeps numbering isolated across tenants by organization prefix", () => {
  const result = reserveSequentialCertificateNumber({
    organizationId: "org-gamma",
    organizationCode: "GAMMA",
    issuedNumbers: [
      { organizationId: "org-acme", certificateNumber: "ACME-000001" },
      { organizationId: "org-beta", certificateNumber: "BETA-000001" },
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(result.nextSequence, 1);
  assert.equal(result.certificateNumber, "GAMMA-000001");
});

test("fails closed when numbering history is inconsistent or colliding", () => {
  const collision = reserveSequentialCertificateNumber({
    organizationId: "org-acme",
    organizationCode: "ACME",
    issuedNumbers: [
      { organizationId: "org-acme", certificateNumber: "ACME-000001" },
      { organizationId: "org-beta", certificateNumber: "ACME-000001" },
    ],
  });

  assert.equal(collision.ok, false);
  assert.deepEqual(collision.errors, ["existing_number_collision"]);

  const prefixMismatch = reserveSequentialCertificateNumber({
    organizationId: "org-acme",
    organizationCode: "ACME",
    issuedNumbers: [{ organizationId: "org-acme", certificateNumber: "BETA-000001" }],
  });

  assert.equal(prefixMismatch.ok, false);
  assert.deepEqual(prefixMismatch.errors, ["organization_prefix_mismatch"]);
});
