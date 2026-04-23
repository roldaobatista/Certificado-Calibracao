import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parseNormativePackageYaml } from "./package.js";
import { signNormativePackageWithAwsKms } from "./kms-signing.js";

type CliArgs = {
  dir: string;
  keyId: string;
  region: string;
  signer: string;
  keyIdLabel?: string;
};

async function runCli(argv: string[]) {
  const args = parseArgs(argv);
  const directory = resolve(process.cwd(), args.dir);
  const packagePath = resolve(directory, "package.yaml");
  const normativePackage = parseNormativePackageYaml(readFileSync(packagePath, "utf8"));
  const signed = await signNormativePackageWithAwsKms({
    normativePackage,
    keyId: args.keyId,
    region: args.region,
    signer: args.signer,
    keyIdLabel: args.keyIdLabel,
  });

  mkdirSync(directory, { recursive: true });
  writeFileSync(resolve(directory, "package.sha256"), `${signed.sha256}\n`);
  writeFileSync(resolve(directory, "package.sig"), `${signed.signature}\n`);
  writeFileSync(resolve(directory, "package.public-key.pem"), signed.publicKeyPem);
  writeFileSync(
    resolve(directory, "package.signature.yaml"),
    [
      `algorithm: ${signed.signatureMetadata.algorithm}`,
      `key_id: ${signed.signatureMetadata.key_id}`,
      `signer: ${signed.signatureMetadata.signer}`,
      `signed_at: '${signed.signatureMetadata.signed_at}'`,
      `provider: ${signed.signatureMetadata.provider}`,
      `signing_algorithm: ${signed.signatureMetadata.signing_algorithm}`,
      `kms_key_arn: ${signed.signatureMetadata.kms_key_arn}`,
      `kms_region: ${signed.signatureMetadata.kms_region}`,
      `public_key_fingerprint_sha256: ${signed.signatureMetadata.public_key_fingerprint_sha256}`,
    ].join("\n"),
  );

  console.log(`normative-package-kms-sign: sidecars escritos em ${directory}`);
}

function parseArgs(argv: string[]): CliArgs {
  const result: Partial<CliArgs> = {};

  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];

    if (!flag?.startsWith("--") || !value) {
      throw new Error("uso: --dir <path> --key-id <arn|alias> --region <aws-region> --signer <label> [--key-id-label <label>]");
    }

    switch (flag) {
      case "--dir":
        result.dir = value;
        break;
      case "--key-id":
        result.keyId = value;
        break;
      case "--region":
        result.region = value;
        break;
      case "--signer":
        result.signer = value;
        break;
      case "--key-id-label":
        result.keyIdLabel = value;
        break;
      default:
        throw new Error(`flag_desconhecida:${flag}`);
    }
  }

  if (!result.dir || !result.keyId || !result.region || !result.signer) {
    throw new Error("uso: --dir <path> --key-id <arn|alias> --region <aws-region> --signer <label> [--key-id-label <label>]");
  }

  return result as CliArgs;
}

export async function main() {
  await runCli(process.argv.slice(2));
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`normative-package-kms-sign error: ${message}`);
    process.exitCode = 1;
  });
}
