import { createHash, sign, verify } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, normalize, resolve } from "node:path";

import { load as yamlLoad } from "js-yaml";

export type NormativeRuleSeverity = "blocker" | "high" | "medium" | "low";

export type NormativePackage = {
  version: string;
  effective_date: string;
  sources: Array<{
    id: string;
    title: string;
    version: string;
    reference: string;
  }>;
  rules: Array<{
    id: string;
    description: string;
    severity: NormativeRuleSeverity;
    applies_to: string[];
  }>;
};

export type SignedNormativePackageInput = {
  package: NormativePackage;
  sha256: string;
  signature: string;
  publicKeyPem: string;
};

export type NormativePackageSignatureMetadata = {
  algorithm: "ed25519";
  key_id: string;
  signer: string;
  signed_at: string;
};

export type NormativePackageManifestEntry = {
  version: string;
  effective_date: string;
  path: string;
  sha256: string;
  key_id: string;
  status: "approved";
};

export type NormativePackageManifest = {
  generated_at: string;
  packages: NormativePackageManifestEntry[];
};

export type NormativePackageVerification = {
  ok: boolean;
  hash: string;
  errors: string[];
  package?: NormativePackage;
};

export type ApprovedNormativePackageVerification = NormativePackageVerification & {
  signatureMetadata?: NormativePackageSignatureMetadata;
};

export type ApprovedNormativePackageRepositoryVerification = {
  ok: boolean;
  errors: string[];
  packages: Array<{
    manifest: NormativePackageManifestEntry;
    verification: ApprovedNormativePackageVerification;
  }>;
};

export function hashNormativePackage(normativePackage: NormativePackage): string {
  return createHash("sha256").update(canonicalJson(normativePackage)).digest("hex");
}

export function signNormativePackage(normativePackage: NormativePackage, privateKeyPem: string): string {
  const signature = sign(null, Buffer.from(canonicalJson(normativePackage), "utf8"), privateKeyPem);
  return signature.toString("base64");
}

export function verifySignedNormativePackage(
  input: SignedNormativePackageInput,
): NormativePackageVerification {
  const errors: string[] = [];
  const computedHash = hashNormativePackage(input.package);
  const expectedHash = input.sha256?.trim();

  const schemaErrors = validateNormativePackage(input.package);
  errors.push(...schemaErrors);

  if (!expectedHash) {
    errors.push("missing_sha256");
  } else if (computedHash !== expectedHash) {
    errors.push(`hash_mismatch: expected ${expectedHash}, got ${computedHash}`);
  }

  if (!input.signature?.trim()) {
    errors.push("missing_signature");
  }

  if (!input.publicKeyPem?.trim()) {
    errors.push("missing_public_key");
  }

  if (errors.length === 0) {
    const validSignature = verify(
      null,
      Buffer.from(canonicalJson(input.package), "utf8"),
      input.publicKeyPem,
      Buffer.from(input.signature.trim(), "base64"),
    );
    if (!validSignature) errors.push("signature_invalid");
  }

  return {
    ok: errors.length === 0,
    hash: computedHash,
    errors,
    package: input.package,
  };
}

export function loadSignedNormativePackageFromDirectory(
  directory: string,
  publicKeyPem: string,
): NormativePackageVerification {
  const packagePath = resolve(directory, "package.yaml");
  const shaPath = resolve(directory, "package.sha256");
  const signaturePath = resolve(directory, "package.sig");
  const errors: string[] = [];

  if (!existsSync(packagePath)) errors.push("missing_package_yaml");
  if (!existsSync(shaPath)) errors.push("missing_package_sha256");
  if (!existsSync(signaturePath)) errors.push("missing_package_sig");

  if (errors.length > 0) {
    return { ok: false, hash: "", errors };
  }

  const normativePackage = parseNormativePackageYaml(readFileSync(packagePath, "utf8"));
  return verifySignedNormativePackage({
    package: normativePackage,
    sha256: readFileSync(shaPath, "utf8"),
    signature: readFileSync(signaturePath, "utf8"),
    publicKeyPem,
  });
}

export function loadApprovedNormativePackageFromDirectory(directory: string): ApprovedNormativePackageVerification {
  const publicKeyPath = resolve(directory, "package.public-key.pem");
  const signatureMetadataPath = resolve(directory, "package.signature.yaml");
  const errors: string[] = [];

  if (!existsSync(publicKeyPath)) errors.push("missing_package_public_key");
  if (!existsSync(signatureMetadataPath)) errors.push("missing_package_signature_metadata");

  if (errors.length > 0) {
    return { ok: false, hash: "", errors };
  }

  const signatureMetadata = parseSignatureMetadataYaml(readFileSync(signatureMetadataPath, "utf8"));
  errors.push(...validateSignatureMetadata(signatureMetadata));

  const verification = loadSignedNormativePackageFromDirectory(directory, readFileSync(publicKeyPath, "utf8"));
  errors.push(...verification.errors);

  return {
    ...verification,
    ok: errors.length === 0,
    errors,
    signatureMetadata,
  };
}

export function loadNormativePackageManifest(manifestPath: string): NormativePackageManifest {
  const manifest = yamlLoad(readFileSync(manifestPath, "utf8"));
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new Error("manifest.yaml deve conter um objeto YAML.");
  }
  return manifest as NormativePackageManifest;
}

export function verifyApprovedNormativePackageRepository(
  root: string,
): ApprovedNormativePackageRepositoryVerification {
  const manifestPath = resolve(root, "compliance", "normative-packages", "releases", "manifest.yaml");
  const errors: string[] = [];
  const packages: ApprovedNormativePackageRepositoryVerification["packages"] = [];

  if (!existsSync(manifestPath)) {
    return {
      ok: false,
      errors: ["missing_normative_package_manifest"],
      packages,
    };
  }

  const manifest = loadNormativePackageManifest(manifestPath);
  errors.push(...validateManifest(manifest));

  for (const entry of manifest.packages ?? []) {
    if (!isApprovedPackagePath(entry.path)) {
      continue;
    }

    const verification = loadApprovedNormativePackageFromDirectory(resolve(root, ...entry.path.split("/")));
    packages.push({ manifest: entry, verification });

    for (const error of verification.errors) {
      errors.push(`${entry.version}:${error}`);
    }

    if (verification.package?.version !== entry.version) {
      errors.push(`${entry.version}:version_mismatch`);
    }

    if (verification.package?.effective_date !== entry.effective_date) {
      errors.push(`${entry.version}:effective_date_mismatch`);
    }

    if (verification.hash !== entry.sha256) {
      errors.push(`${entry.version}:manifest_hash_mismatch`);
    }

    if (verification.signatureMetadata?.key_id !== entry.key_id) {
      errors.push(`${entry.version}:key_id_mismatch`);
    }
  }

  return {
    ok: errors.length === 0,
    errors,
    packages,
  };
}

export function parseNormativePackageYaml(yaml: string): NormativePackage {
  const parsed = yamlLoad(yaml);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("package.yaml deve conter um objeto YAML.");
  }
  return parsed as NormativePackage;
}

export function assertSignedNormativePackage(input: SignedNormativePackageInput): NormativePackage {
  const result = verifySignedNormativePackage(input);
  if (!result.ok) {
    throw new Error(`Normative package inválido: ${result.errors.join(", ")}`);
  }
  return input.package;
}

function parseSignatureMetadataYaml(yaml: string): NormativePackageSignatureMetadata {
  const parsed = yamlLoad(yaml);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("package.signature.yaml deve conter um objeto YAML.");
  }
  return parsed as NormativePackageSignatureMetadata;
}

function validateNormativePackage(normativePackage: NormativePackage): string[] {
  const errors: string[] = [];
  if (!normativePackage?.version) errors.push("missing_version");
  if (!normativePackage?.effective_date) errors.push("missing_effective_date");
  if (!Array.isArray(normativePackage?.sources) || normativePackage.sources.length === 0) {
    errors.push("missing_sources");
  }
  if (!Array.isArray(normativePackage?.rules) || normativePackage.rules.length === 0) {
    errors.push("missing_rules");
  }

  for (const source of normativePackage?.sources ?? []) {
    if (!source.id) errors.push("source_missing_id");
    if (!source.title) errors.push(`source_missing_title:${source.id ?? "<unknown>"}`);
    if (!source.version) errors.push(`source_missing_version:${source.id ?? "<unknown>"}`);
    if (!source.reference) errors.push(`source_missing_reference:${source.id ?? "<unknown>"}`);
  }

  for (const rule of normativePackage?.rules ?? []) {
    if (!rule.id) errors.push("rule_missing_id");
    if (!rule.description) errors.push(`rule_missing_description:${rule.id ?? "<unknown>"}`);
    if (!rule.severity) errors.push(`rule_missing_severity:${rule.id ?? "<unknown>"}`);
    if (!Array.isArray(rule.applies_to) || rule.applies_to.length === 0) {
      errors.push(`rule_missing_applies_to:${rule.id ?? "<unknown>"}`);
    }
  }

  return errors;
}

function validateSignatureMetadata(metadata: NormativePackageSignatureMetadata): string[] {
  const errors: string[] = [];
  if (metadata?.algorithm !== "ed25519") errors.push("signature_metadata_algorithm_not_ed25519");
  if (!metadata?.key_id) errors.push("signature_metadata_missing_key_id");
  if (!metadata?.signer) errors.push("signature_metadata_missing_signer");
  if (!metadata?.signed_at) errors.push("signature_metadata_missing_signed_at");
  return errors;
}

function validateManifest(manifest: NormativePackageManifest): string[] {
  const errors: string[] = [];
  if (!manifest?.generated_at) errors.push("manifest_missing_generated_at");
  if (!Array.isArray(manifest?.packages) || manifest.packages.length === 0) {
    errors.push("manifest_missing_packages");
  }

  for (const entry of manifest?.packages ?? []) {
    const label = entry?.version ?? "<unknown>";
    if (!entry.version) errors.push("manifest_entry_missing_version");
    if (!entry.effective_date) errors.push(`${label}:manifest_entry_missing_effective_date`);
    if (!entry.path) errors.push(`${label}:manifest_entry_missing_path`);
    if (entry.path && !isApprovedPackagePath(entry.path)) {
      errors.push(`${label}:manifest_entry_path_not_approved_package`);
    }
    if (!entry.sha256) errors.push(`${label}:manifest_entry_missing_sha256`);
    if (!entry.key_id) errors.push(`${label}:manifest_entry_missing_key_id`);
    if (entry.status !== "approved") errors.push(`${label}:manifest_entry_status_not_approved`);
  }

  return errors;
}

function isApprovedPackagePath(path: string): boolean {
  if (!path || isAbsolute(path)) return false;
  const normalized = normalize(path).replace(/\\/g, "/");
  return (
    normalized.startsWith("compliance/normative-packages/approved/") &&
    !normalized.split("/").includes("..")
  );
}

function canonicalJson(value: unknown): string {
  return JSON.stringify(sortDeep(value));
}

function sortDeep(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortDeep);
  if (!value || typeof value !== "object") return value;

  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, nestedValue]) => [key, sortDeep(nestedValue)]),
  );
}
