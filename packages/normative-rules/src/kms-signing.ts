import { createHash } from "node:crypto";

import {
  GetPublicKeyCommand,
  KMSClient,
  SignCommand,
  type GetPublicKeyCommandOutput,
  type SignCommandOutput,
} from "@aws-sdk/client-kms";

import {
  hashNormativePackage,
  serializeNormativePackageForSignature,
  type NormativePackage,
  type NormativePackageSignatureMetadata,
} from "./package.js";

export type AwsKmsLikeClient = {
  send(command: unknown): Promise<unknown>;
};

export type AwsKmsSigningInput = {
  normativePackage: NormativePackage;
  keyId: string;
  region: string;
  signer: string;
  keyIdLabel?: string;
  signedAt?: string;
  client?: AwsKmsLikeClient;
};

export type AwsKmsSigningArtifacts = {
  sha256: string;
  signature: string;
  publicKeyPem: string;
  signatureMetadata: NormativePackageSignatureMetadata;
};

const AWS_KMS_SIGNING_ALGORITHM = "ED25519_SHA_512";
const AWS_KMS_ED25519_KEY_SPEC = "ECC_NIST_EDWARDS25519";
const AWS_KMS_SIGN_VERIFY = "SIGN_VERIFY";

export async function signNormativePackageWithAwsKms(
  input: AwsKmsSigningInput,
): Promise<AwsKmsSigningArtifacts> {
  const client = input.client ?? new KMSClient({ region: input.region });
  const signablePayload = Buffer.from(serializeNormativePackageForSignature(input.normativePackage), "utf8");
  const sha256 = hashNormativePackage(input.normativePackage);

  const publicKeyResult = (await client.send(
    new GetPublicKeyCommand({ KeyId: input.keyId }),
  )) as GetPublicKeyCommandOutput;

  const keyUsage = publicKeyResult.KeyUsage;
  const keySpec = publicKeyResult.KeySpec;
  const algorithms = publicKeyResult.SigningAlgorithms ?? [];

  if (keyUsage !== AWS_KMS_SIGN_VERIFY) {
    throw new Error(`kms_key_usage_invalid:${keyUsage ?? "unknown"}`);
  }
  if (keySpec !== AWS_KMS_ED25519_KEY_SPEC) {
    throw new Error(`kms_key_spec_invalid:${keySpec ?? "unknown"}`);
  }
  if (!algorithms.includes(AWS_KMS_SIGNING_ALGORITHM)) {
    throw new Error("kms_signing_algorithm_not_supported");
  }
  if (!publicKeyResult.PublicKey) {
    throw new Error("kms_public_key_missing");
  }

  const signResult = (await client.send(
    new SignCommand({
      KeyId: input.keyId,
      Message: signablePayload,
      MessageType: "RAW",
      SigningAlgorithm: AWS_KMS_SIGNING_ALGORITHM,
    }),
  )) as SignCommandOutput;

  if (!signResult.Signature) {
    throw new Error("kms_signature_missing");
  }

  const publicKeyDer = Buffer.from(publicKeyResult.PublicKey);
  return {
    sha256,
    signature: Buffer.from(signResult.Signature).toString("base64"),
    publicKeyPem: derToPem(publicKeyDer, "PUBLIC KEY"),
    signatureMetadata: {
      algorithm: "ed25519",
      key_id: input.keyIdLabel ?? input.keyId,
      signer: input.signer,
      signed_at: input.signedAt ?? new Date().toISOString(),
      provider: "aws-kms",
      signing_algorithm: AWS_KMS_SIGNING_ALGORITHM,
      kms_key_arn: signResult.KeyId ?? input.keyId,
      kms_region: input.region,
      public_key_fingerprint_sha256: createHash("sha256").update(publicKeyDer).digest("hex"),
    },
  };
}

function derToPem(der: Buffer, label: string): string {
  const base64 = der.toString("base64");
  const lines = base64.match(/.{1,64}/g) ?? [];
  return [`-----BEGIN ${label}-----`, ...lines, `-----END ${label}-----`, ""].join("\n");
}
