import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const POLICY_MARKDOWN = "compliance/cloud-agents-policy.md";
const POLICY_YAML = "compliance/cloud-agents/policy.yaml";
const ATTESTATION_TEMPLATE = "compliance/cloud-agents/attestations/_template.yaml";
const HARNESS_POLICY = "harness/09-cloud-agents-policy.md";
const CLOUD_AGENTS_LOG = "compliance/cloud-agents-log.md";
const INCIDENT_TEMPLATE = "compliance/incidents/cloud-agent-attestation-failure-template.md";

const REQUIRED_ALLOWLIST = [
  "apps/web/ui/components/**",
  "apps/portal/ui/**",
  "docs/**",
  "evals/fixtures/synthetic/**",
  "tests/unit/**",
] as const;
const REQUIRED_BLOCKLIST = [
  "apps/api/**",
  "apps/android/**",
  "packages/engine-uncertainty/**",
  "packages/normative-rules/**",
  "packages/db/**",
  "packages/audit-log/**",
  "compliance/**",
  "specs/**",
  ".claude/agents/**",
  "infra/**",
] as const;
const REQUIRED_MECHANISMS = [
  "slsa-build-level-2-plus",
  "sigstore-cosign",
  "github-artifact-attestations",
] as const;
const REQUIRED_VERIFIERS = ["gh attestation verify", "cosign verify-blob"] as const;
const WEAK_MECHANISMS = new Set(["user-agent", "commit-metadata", "commit-author", "branch-name"]);

type CloudAgentsPolicy = {
  version?: number;
  source?: string;
  status?: string;
  allowlist?: string[];
  blocklist?: string[];
  provenance?: {
    require_verified_attestation?: boolean;
    deny_without_attestation?: boolean;
    accepted_mechanisms?: string[];
    allowed_issuers?: string[];
    required_verifier_commands?: string[];
  };
  fixture_scanner?: {
    synthetic_only?: boolean;
    allowed_email_domain?: string;
    synthetic_name_prefix?: string;
  };
  incident?: {
    failure_template?: string;
    audit_log?: string;
  };
};

type AttestationManifest = {
  schema_version?: number;
  mechanism?: string;
  subject_commit?: string;
  issuer?: string;
  identity?: string;
  predicate_type?: string;
  verified_at?: string;
  verifier_command?: string;
};

export type CloudAgentsPolicyCheck = {
  errors: string[];
  checkedAllowedPaths: number;
  checkedBlockedPaths: number;
  checkedMechanisms: number;
};

export type CloudAgentPullRequestInput = {
  branchName: string;
  changedFiles: string[];
  commitSha: string;
  attestationPath?: string;
};

export type CloudAgentPullRequestCheck = {
  errors: string[];
  isCloudAgentBranch: boolean;
  checkedAllowedPaths: number;
  attestationVerified: boolean;
};

export function checkCloudAgentsPolicy(root = process.cwd()): CloudAgentsPolicyCheck {
  const errors: string[] = [];
  for (const path of [
    POLICY_MARKDOWN,
    POLICY_YAML,
    ATTESTATION_TEMPLATE,
    HARNESS_POLICY,
    CLOUD_AGENTS_LOG,
    INCIDENT_TEMPLATE,
  ]) {
    if (!existsSync(resolve(root, path))) {
      errors.push(`CLOUD-001: artefato obrigatório ausente: ${path}.`);
    }
  }

  const policy = loadPolicy(root, errors);
  if (policy) {
    checkPolicyDocument(root, policy, errors);
  }
  if (existsSync(resolve(root, HARNESS_POLICY))) {
    checkHarnessPolicy(root, errors);
  }

  return {
    errors,
    checkedAllowedPaths: policy?.allowlist?.length ?? 0,
    checkedBlockedPaths: policy?.blocklist?.length ?? 0,
    checkedMechanisms: policy?.provenance?.accepted_mechanisms?.length ?? 0,
  };
}

export function evaluateCloudAgentPullRequest(
  root: string,
  input: CloudAgentPullRequestInput,
): CloudAgentPullRequestCheck {
  const errors: string[] = [];
  const isCloudAgentBranch = input.branchName.startsWith("cloud-agent/");
  if (!isCloudAgentBranch) {
    return { errors, isCloudAgentBranch, checkedAllowedPaths: 0, attestationVerified: false };
  }

  const policy = loadPolicy(root, errors);
  if (!policy) {
    return { errors, isCloudAgentBranch, checkedAllowedPaths: 0, attestationVerified: false };
  }

  let checkedAllowedPaths = 0;
  for (const file of input.changedFiles.map(normalizePath)) {
    if (matchesAny(file, policy.blocklist ?? [])) {
      errors.push(`CLOUD-PR-001: cloud agent não pode tocar path bloqueado: ${file}.`);
      continue;
    }
    if (!matchesAny(file, policy.allowlist ?? [])) {
      errors.push(`CLOUD-PR-001: cloud agent fora da allowlist: ${file}.`);
      continue;
    }
    checkedAllowedPaths += 1;
  }

  if (!input.attestationPath) {
    errors.push("CLOUD-PR-002: branch cloud-agent/* exige attestation verificável; nenhum manifesto informado.");
    return { errors, isCloudAgentBranch, checkedAllowedPaths, attestationVerified: false };
  }

  const attestationVerified = checkAttestationManifest(root, policy, input, errors);
  return { errors, isCloudAgentBranch, checkedAllowedPaths, attestationVerified };
}

function loadPolicy(root: string, errors: string[]): CloudAgentsPolicy | undefined {
  const path = resolve(root, POLICY_YAML);
  if (!existsSync(path)) return undefined;

  const parsed = yamlLoad(readFileSync(path, "utf8"));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    errors.push(`CLOUD-002: ${POLICY_YAML} deve conter objeto YAML.`);
    return undefined;
  }
  return parsed as CloudAgentsPolicy;
}

function checkPolicyDocument(root: string, policy: CloudAgentsPolicy, errors: string[]) {
  if (policy.version !== 1) errors.push(`CLOUD-002: ${POLICY_YAML} deve declarar version: 1.`);
  if (policy.source !== HARNESS_POLICY) {
    errors.push(`CLOUD-002: ${POLICY_YAML} deve apontar source: ${HARNESS_POLICY}.`);
  }
  if (policy.status !== "enforced") errors.push(`CLOUD-002: ${POLICY_YAML} deve declarar status: enforced.`);

  checkRequiredList("allowlist", policy.allowlist, REQUIRED_ALLOWLIST, errors);
  checkRequiredList("blocklist", policy.blocklist, REQUIRED_BLOCKLIST, errors);

  const provenance = policy.provenance;
  if (provenance?.require_verified_attestation !== true) {
    errors.push("CLOUD-002: provenance.require_verified_attestation deve ser true.");
  }
  if (provenance?.deny_without_attestation !== true) {
    errors.push("CLOUD-002: provenance.deny_without_attestation deve ser true.");
  }

  const mechanisms = provenance?.accepted_mechanisms ?? [];
  for (const mechanism of REQUIRED_MECHANISMS) {
    if (!mechanisms.includes(mechanism)) {
      errors.push(`CLOUD-002: provenance.accepted_mechanisms deve incluir ${mechanism}.`);
    }
  }
  for (const mechanism of mechanisms) {
    if (WEAK_MECHANISMS.has(mechanism)) {
      errors.push(`CLOUD-002: mecanismo fraco não aceito como attestation: ${mechanism}.`);
    }
  }

  const issuers = provenance?.allowed_issuers ?? [];
  if (issuers.length === 0) errors.push("CLOUD-002: provenance.allowed_issuers não pode ser vazio.");
  for (const verifier of REQUIRED_VERIFIERS) {
    if (!provenance?.required_verifier_commands?.includes(verifier)) {
      errors.push(`CLOUD-002: provenance.required_verifier_commands deve incluir ${verifier}.`);
    }
  }

  if (policy.fixture_scanner?.synthetic_only !== true) {
    errors.push("CLOUD-003: fixture_scanner.synthetic_only deve ser true.");
  }
  if (policy.fixture_scanner?.allowed_email_domain !== "example.afere.test") {
    errors.push("CLOUD-003: fixture_scanner.allowed_email_domain deve ser example.afere.test.");
  }
  if (policy.fixture_scanner?.synthetic_name_prefix !== "TEST_") {
    errors.push("CLOUD-003: fixture_scanner.synthetic_name_prefix deve ser TEST_.");
  }

  if (policy.incident?.failure_template !== INCIDENT_TEMPLATE) {
    errors.push(`CLOUD-004: incident.failure_template deve ser ${INCIDENT_TEMPLATE}.`);
  }
  if (policy.incident?.audit_log !== CLOUD_AGENTS_LOG) {
    errors.push(`CLOUD-004: incident.audit_log deve ser ${CLOUD_AGENTS_LOG}.`);
  }
  for (const linkedPath of [policy.incident?.failure_template, policy.incident?.audit_log]) {
    if (linkedPath && !existsSync(resolve(root, linkedPath))) {
      errors.push(`CLOUD-004: artefato referenciado ausente: ${linkedPath}.`);
    }
  }
}

function checkRequiredList(
  field: "allowlist" | "blocklist",
  actual: string[] | undefined,
  required: readonly string[],
  errors: string[],
) {
  if (!Array.isArray(actual)) {
    errors.push(`CLOUD-002: ${field} deve ser lista.`);
    return;
  }
  for (const path of required) {
    if (!actual.includes(path)) errors.push(`CLOUD-002: ${field} deve incluir ${path}.`);
  }
}

function checkHarnessPolicy(root: string, errors: string[]) {
  const text = normalizeText(readFileSync(resolve(root, HARNESS_POLICY), "utf8"));
  for (const required of ["slsa build level 2+", "sigstore", "github artifact attestations", "fallback"]) {
    if (!text.includes(required)) errors.push(`CLOUD-005: ${HARNESS_POLICY} deve mencionar ${required}.`);
  }
}

function checkAttestationManifest(
  root: string,
  policy: CloudAgentsPolicy,
  input: Required<Pick<CloudAgentPullRequestInput, "attestationPath" | "commitSha">>,
  errors: string[],
) {
  const path = resolve(root, input.attestationPath);
  if (!existsSync(path)) {
    errors.push(`CLOUD-PR-002: attestation ausente: ${input.attestationPath}.`);
    return false;
  }

  const parsed = yamlLoad(readFileSync(path, "utf8"));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    errors.push("CLOUD-PR-003: attestation deve conter objeto YAML.");
    return false;
  }

  const attestation = parsed as AttestationManifest;
  if (attestation.schema_version !== 1) errors.push("CLOUD-PR-003: attestation.schema_version deve ser 1.");
  if (!policy.provenance?.accepted_mechanisms?.includes(stringValue(attestation.mechanism))) {
    errors.push(`CLOUD-PR-003: mecanismo de attestation não aceito: ${stringValue(attestation.mechanism)}.`);
  }
  if (stringValue(attestation.subject_commit) !== input.commitSha) {
    errors.push("CLOUD-PR-003: attestation.subject_commit não corresponde ao commit avaliado.");
  }
  if (!policy.provenance?.allowed_issuers?.includes(stringValue(attestation.issuer))) {
    errors.push(`CLOUD-PR-003: issuer de attestation não permitido: ${stringValue(attestation.issuer)}.`);
  }
  if (!stringValue(attestation.identity)) errors.push("CLOUD-PR-003: attestation.identity é obrigatório.");
  if (!stringValue(attestation.predicate_type).includes("slsa.dev/provenance")) {
    errors.push("CLOUD-PR-003: attestation.predicate_type deve ser SLSA provenance.");
  }
  if (!isIsoLikeDateTime(stringValue(attestation.verified_at))) {
    errors.push("CLOUD-PR-003: attestation.verified_at deve ser ISO-8601.");
  }
  const verifierCommand = stringValue(attestation.verifier_command);
  if (!policy.provenance?.required_verifier_commands?.some((prefix) => verifierCommand.startsWith(prefix))) {
    errors.push("CLOUD-PR-003: attestation.verifier_command deve registrar gh attestation verify ou cosign verify-blob.");
  }

  return !errors.some((error) => error.startsWith("CLOUD-PR-003"));
}

function matchesAny(file: string, globs: string[]) {
  return globs.some((glob) => globToRegex(glob).test(file));
}

function globToRegex(glob: string) {
  const normalized = normalizePath(glob);
  let pattern = "";
  for (let index = 0; index < normalized.length; index += 1) {
    if (normalized.slice(index, index + 2) === "**") {
      pattern += ".*";
      index += 1;
    } else if (normalized[index] === "*") {
      pattern += "[^/]*";
    } else {
      pattern += normalized[index].replace(/[.+^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`^${pattern}$`);
}

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function normalizeText(text: string) {
  return text
    .replace(/\r\n/g, "\n")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function stringValue(value: unknown) {
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function isIsoLikeDateTime(value: string) {
  return /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})/.test(value);
}

function parseCliArgs(argv: string[]) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "check";
  const parsed: {
    command: string;
    branchName?: string;
    base?: string;
    commitSha?: string;
    attestationPath?: string;
  } = { command };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--branch") parsed.branchName = args[++index];
    else if (arg === "--base") parsed.base = args[++index];
    else if (arg === "--commit") parsed.commitSha = args[++index];
    else if (arg === "--attestation") parsed.attestationPath = args[++index];
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  return parsed;
}

function getChangedFiles(base = "origin/main") {
  const output = execFileSync("git", ["diff", "--name-only", `${base}...HEAD`], { encoding: "utf8" });
  return output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function getCurrentBranch() {
  return execFileSync("git", ["branch", "--show-current"], { encoding: "utf8" }).trim();
}

function getHeadCommit() {
  return execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
}

function runCli() {
  try {
    const args = parseCliArgs(process.argv.slice(2));
    if (args.command === "check") {
      const result = checkCloudAgentsPolicy();
      console.log(
        `cloud-agents-policy-check: ${result.checkedAllowedPaths} allowlist, ${result.checkedBlockedPaths} blocklist, ${result.checkedMechanisms} mecanismo(s).`,
      );
      for (const error of result.errors) console.error(`ERROR ${error}`);
      return result.errors.length > 0 ? 1 : 0;
    }

    if (args.command === "pr") {
      const result = evaluateCloudAgentPullRequest(process.cwd(), {
        branchName: args.branchName ?? getCurrentBranch(),
        changedFiles: getChangedFiles(args.base),
        commitSha: args.commitSha ?? getHeadCommit(),
        attestationPath: args.attestationPath,
      });
      console.log(
        `cloud-agents-policy-check: pr cloud=${result.isCloudAgentBranch}, allowed_paths=${result.checkedAllowedPaths}, attestation=${result.attestationVerified}.`,
      );
      for (const error of result.errors) console.error(`ERROR ${error}`);
      return result.errors.length > 0 ? 1 : 0;
    }

    console.error("Uso: cloud-agents-policy-check [check|pr] [--branch <nome>] [--base <ref>] [--commit <sha>] [--attestation <path>]");
    return 2;
  } catch (error) {
    console.error(`cloud-agents-policy-check: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
