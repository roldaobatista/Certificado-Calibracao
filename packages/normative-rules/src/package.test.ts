import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import {
  hashNormativePackage,
  loadSignedNormativePackageFromDirectory,
  signNormativePackage,
  verifySignedNormativePackage,
  type NormativePackage,
} from "./package.js";

const baselinePackage: NormativePackage = {
  version: "0.1.0",
  effective_date: "2026-04-20",
  sources: [
    {
      id: "PRD",
      title: "PRD Aferê",
      version: "1.8",
      reference: "PRD.md",
    },
  ],
  rules: [
    {
      id: "RULE-STANDARD-VALID-CERTIFICATE",
      description: "Padrão usado na emissão precisa ter certificado válido.",
      severity: "blocker",
      applies_to: ["certificate-emission"],
    },
  ],
};

function generateKeys() {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  return {
    privateKeyPem: privateKey.export({ format: "pem", type: "pkcs8" }).toString(),
    publicKeyPem: publicKey.export({ format: "pem", type: "spki" }).toString(),
  };
}

test("hashes normative packages canonically regardless of object key order", () => {
  const samePackageDifferentOrder = {
    rules: baselinePackage.rules,
    sources: baselinePackage.sources,
    effective_date: baselinePackage.effective_date,
    version: baselinePackage.version,
  } as NormativePackage;

  assert.equal(hashNormativePackage(baselinePackage), hashNormativePackage(samePackageDifferentOrder));
});

test("verifies a signed normative package", () => {
  const { privateKeyPem, publicKeyPem } = generateKeys();
  const signature = signNormativePackage(baselinePackage, privateKeyPem);
  const sha256 = hashNormativePackage(baselinePackage);

  const result = verifySignedNormativePackage({
    package: baselinePackage,
    sha256,
    signature,
    publicKeyPem,
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.errors, []);
});

test("rejects tampered package contents when hash no longer matches", () => {
  const { privateKeyPem, publicKeyPem } = generateKeys();
  const signature = signNormativePackage(baselinePackage, privateKeyPem);
  const tampered = {
    ...baselinePackage,
    version: "0.1.1",
  };

  const result = verifySignedNormativePackage({
    package: tampered,
    sha256: hashNormativePackage(baselinePackage),
    signature,
    publicKeyPem,
  });

  assert.equal(result.ok, false);
  assert.match(result.errors.join("\n"), /hash_mismatch/);
});

test("rejects unsigned normative packages fail-closed", () => {
  const { publicKeyPem } = generateKeys();
  const result = verifySignedNormativePackage({
    package: baselinePackage,
    sha256: hashNormativePackage(baselinePackage),
    signature: "",
    publicKeyPem,
  });

  assert.equal(result.ok, false);
  assert.match(result.errors.join("\n"), /missing_signature/);
});

test("loads and verifies package.yaml, package.sha256 and package.sig from a directory", () => {
  const { privateKeyPem, publicKeyPem } = generateKeys();
  const root = mkdtempSync(join(tmpdir(), "afere-normative-package-"));

  try {
    writeFileSync(
      join(root, "package.yaml"),
      [
        "version: 0.1.0",
        "effective_date: '2026-04-20'",
        "sources:",
        "  - id: PRD",
        "    title: PRD Aferê",
        "    version: '1.8'",
        "    reference: PRD.md",
        "rules:",
        "  - id: RULE-STANDARD-VALID-CERTIFICATE",
        "    description: Padrão usado na emissão precisa ter certificado válido.",
        "    severity: blocker",
        "    applies_to:",
        "      - certificate-emission",
      ].join("\n"),
    );
    writeFileSync(join(root, "package.sha256"), `${hashNormativePackage(baselinePackage)}\n`);
    writeFileSync(join(root, "package.sig"), `${signNormativePackage(baselinePackage, privateKeyPem)}\n`);

    const result = loadSignedNormativePackageFromDirectory(root, publicKeyPem);

    assert.equal(result.ok, true);
    assert.equal(result.package?.version, "0.1.0");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
