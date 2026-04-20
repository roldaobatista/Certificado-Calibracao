import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
  hashNormativePackage,
  loadApprovedNormativePackageFromDirectory,
  loadSignedNormativePackageFromDirectory,
  signNormativePackage,
  verifyApprovedNormativePackageRepository,
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

function writeSignedPackage(root: string, keys: ReturnType<typeof generateKeys>, keyId = "test-key-1") {
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
  writeFileSync(join(root, "package.sig"), `${signNormativePackage(baselinePackage, keys.privateKeyPem)}\n`);
  writeFileSync(join(root, "package.public-key.pem"), keys.publicKeyPem);
  writeFileSync(
    join(root, "package.signature.yaml"),
    [
      "algorithm: ed25519",
      `key_id: ${keyId}`,
      "signer: test-suite",
      "signed_at: '2026-04-20T00:00:00.000Z'",
    ].join("\n"),
  );
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

test("loads approved packages with versioned public key and signature metadata sidecars", () => {
  const keys = generateKeys();
  const root = mkdtempSync(join(tmpdir(), "afere-approved-normative-package-"));

  try {
    writeSignedPackage(root, keys, "approved-key-1");

    const result = loadApprovedNormativePackageFromDirectory(root);

    assert.equal(result.ok, true);
    assert.deepEqual(result.errors, []);
    assert.equal(result.package?.version, "0.1.0");
    assert.equal(result.signatureMetadata?.algorithm, "ed25519");
    assert.equal(result.signatureMetadata?.key_id, "approved-key-1");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("verifies approved package repository manifest against signed package directories", () => {
  const keys = generateKeys();
  const root = mkdtempSync(join(tmpdir(), "afere-normative-repository-"));
  const relativePackagePath = "compliance/normative-packages/approved/2026-04-20-baseline-v0.1.0";
  const packageDir = join(root, ...relativePackagePath.split("/"));
  const manifestDir = join(root, "compliance", "normative-packages", "releases");

  try {
    mkdirSync(packageDir, { recursive: true });
    mkdirSync(manifestDir, { recursive: true });
    writeSignedPackage(packageDir, keys, "manifest-key-1");
    writeFileSync(
      join(manifestDir, "manifest.yaml"),
      [
        "generated_at: '2026-04-20T00:00:00.000Z'",
        "packages:",
        "  - version: 0.1.0",
        "    effective_date: '2026-04-20'",
        `    path: ${relativePackagePath}`,
        `    sha256: ${hashNormativePackage(baselinePackage)}`,
        "    key_id: manifest-key-1",
        "    status: approved",
      ].join("\n"),
    );

    const result = verifyApprovedNormativePackageRepository(root);

    assert.equal(result.ok, true, result.errors.join("\n"));
    assert.equal(result.packages.length, 1);
    assert.equal(result.packages[0]?.manifest.version, "0.1.0");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("verifies the committed approved baseline normative package from releases manifest", () => {
  const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

  const result = verifyApprovedNormativePackageRepository(repoRoot);

  assert.equal(result.ok, true, result.errors.join("\n"));
  assert.ok(result.packages.some((entry) => entry.manifest.version === "0.1.0"));
});
