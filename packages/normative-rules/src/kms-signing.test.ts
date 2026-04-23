import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import test from "node:test";

import type { NormativePackage } from "./package.js";
import { signNormativePackageWithAwsKms } from "./kms-signing.js";

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

function createFakeKmsClient(options?: {
  keyUsage?: string;
  keySpec?: string;
  algorithms?: string[];
}) {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const publicKeyDer = publicKey.export({ format: "der", type: "spki" });

  return {
    async send(command: unknown) {
      const commandName = (command as { constructor?: { name?: string } }).constructor?.name;
      const input = (command as { input?: Record<string, unknown> }).input ?? {};

      if (commandName === "GetPublicKeyCommand") {
        return {
          KeyUsage: options?.keyUsage ?? "SIGN_VERIFY",
          KeySpec: options?.keySpec ?? "ECC_NIST_EDWARDS25519",
          SigningAlgorithms: options?.algorithms ?? ["ED25519_SHA_512"],
          PublicKey: publicKeyDer,
        };
      }

      if (commandName === "SignCommand") {
        const signature = sign(null, Buffer.from(input.Message as Uint8Array), privateKey);
        return {
          KeyId: input.KeyId,
          Signature: signature,
        };
      }

      throw new Error(`unexpected_command:${commandName ?? "unknown"}`);
    },
  };
}

test("signs a normative package with AWS KMS sidecars", async () => {
  const result = await signNormativePackageWithAwsKms({
    normativePackage: baselinePackage,
    keyId: "arn:aws:kms:sa-east-1:111122223333:key/example",
    region: "sa-east-1",
    signer: "ci-release",
    keyIdLabel: "kms-ed25519-sa-east-1-v1",
    signedAt: "2026-04-23T12:00:00.000Z",
    client: createFakeKmsClient(),
  });

  assert.equal(result.signatureMetadata.provider, "aws-kms");
  assert.equal(result.signatureMetadata.signing_algorithm, "ED25519_SHA_512");
  assert.equal(result.signatureMetadata.kms_region, "sa-east-1");
  assert.equal(result.signatureMetadata.key_id, "kms-ed25519-sa-east-1-v1");
  assert.match(result.publicKeyPem, /BEGIN PUBLIC KEY/);
  assert.equal(result.sha256.length, 64);
  assert.equal(result.signature.length > 40, true);
});

test("fails closed when the KMS key usage is not SIGN_VERIFY", async () => {
  await assert.rejects(
    signNormativePackageWithAwsKms({
      normativePackage: baselinePackage,
      keyId: "arn:aws:kms:sa-east-1:111122223333:key/example",
      region: "sa-east-1",
      signer: "ci-release",
      client: createFakeKmsClient({ keyUsage: "ENCRYPT_DECRYPT" }),
    }),
    /kms_key_usage_invalid/,
  );
});

test("fails closed when the KMS key spec is not Ed25519", async () => {
  await assert.rejects(
    signNormativePackageWithAwsKms({
      normativePackage: baselinePackage,
      keyId: "arn:aws:kms:sa-east-1:111122223333:key/example",
      region: "sa-east-1",
      signer: "ci-release",
      client: createFakeKmsClient({ keySpec: "ECC_NIST_P256" }),
    }),
    /kms_key_spec_invalid/,
  );
});
