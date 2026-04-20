import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

import { loadRequirements, type Requirement } from "./validation-dossier";

const VERIFICATION_LOG_README = "compliance/verification-log/README.md";
const SNAPSHOT_MANIFEST = "compliance/validation-dossier/snapshots/manifest.yaml";
const REQUIRED_SNAPSHOT_SOURCE = "harness/05-guardrails.md";
const REQUIRED_SNAPSHOT_PROFILES = ["A", "B", "C"] as const;
const REQUIRED_BASELINE_APPROVERS = ["regulator", "product-governance"] as const;

export const CRITICAL_AREAS = [
  "apps/api/src/domain/emission/**",
  "apps/api/src/domain/audit/**",
  "packages/engine-uncertainty/**",
  "packages/normative-rules/**",
  "packages/audit-log/**",
] as const;

const RELEASE_AUDITOR_PATHS = [
  "compliance/audits/metrology",
  "compliance/audits/legal",
  "compliance/audits/code",
] as const;

export type CascadeGate = {
  level: "L0" | "L1" | "L2" | "L3" | "L4" | "L5";
  gate: string;
  required: boolean;
  reason: string;
};

export type CascadePlan = {
  changedFiles: string[];
  criticalAreas: string[];
  requiresFullRegression: boolean;
  requiresSnapshotDiff: boolean;
  regressionTests: string[];
  gates: CascadeGate[];
};

export type ReleaseAuditCheck = {
  release: string;
  required: string[];
  missing: string[];
};

export type VerificationCascadeCheck = {
  errors: string[];
  checkedSnapshots: number;
  checkedProfiles: string[];
};

type SnapshotManifest = {
  version?: number;
  source?: string;
  policy?: {
    profiles_required?: unknown;
    snapshots_per_profile?: unknown;
    fail_on_diff?: unknown;
    approval_required_for_baseline_update?: unknown;
  };
  snapshots?: unknown;
};

type SnapshotManifestEntry = {
  id?: unknown;
  profile?: unknown;
  baseline_path?: unknown;
  current_path?: unknown;
  sha256?: unknown;
  renderer?: unknown;
  requirement_refs?: unknown;
};

export function buildCascadePlan(root: string, changedFiles: string[]): CascadePlan {
  const normalizedChangedFiles = changedFiles.map(normalizePath);
  const criticalAreas = CRITICAL_AREAS.filter((area) =>
    normalizedChangedFiles.some((changedFile) => matchesPathPattern(changedFile, area)),
  );
  const requiresFullRegression = criticalAreas.length > 0;
  const regressionTests = requiresFullRegression
    ? selectAreaRegressionTests(loadRequirements(root), criticalAreas)
    : [];

  return {
    changedFiles: normalizedChangedFiles,
    criticalAreas,
    requiresFullRegression,
    requiresSnapshotDiff: requiresFullRegression,
    regressionTests,
    gates: buildGates(requiresFullRegression),
  };
}

export function checkReleaseAudits(root: string, release: string): ReleaseAuditCheck {
  const required = RELEASE_AUDITOR_PATHS.map((path) => `${path}/${release}.md`);
  return {
    release,
    required,
    missing: required.filter((path) => !existsSync(resolve(root, path))),
  };
}

export function checkVerificationCascade(root = process.cwd()): VerificationCascadeCheck {
  const errors: string[] = [];
  if (!existsSync(resolve(root, VERIFICATION_LOG_README))) {
    errors.push(`CASCADE-001: ${VERIFICATION_LOG_README} não encontrado.`);
  }
  const snapshotCheck = checkSnapshotDiff(root);
  errors.push(...snapshotCheck.errors);
  return {
    errors,
    checkedSnapshots: snapshotCheck.checkedSnapshots,
    checkedProfiles: snapshotCheck.checkedProfiles,
  };
}

function checkSnapshotDiff(root: string) {
  const errors: string[] = [];
  const manifestPath = resolve(root, SNAPSHOT_MANIFEST);
  if (!existsSync(manifestPath)) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} não encontrado.`);
    return { errors, checkedSnapshots: 0, checkedProfiles: [] };
  }

  const manifest = loadSnapshotManifest(manifestPath, errors);
  if (!manifest) return { errors, checkedSnapshots: 0, checkedProfiles: [] };

  validateSnapshotPolicy(manifest, errors);

  const snapshots = Array.isArray(manifest.snapshots) ? (manifest.snapshots as SnapshotManifestEntry[]) : [];
  if (snapshots.length === 0) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar snapshots.`);
  }

  const checkedProfiles: string[] = [];
  let checkedSnapshots = 0;
  for (const [index, snapshot] of snapshots.entries()) {
    if (!isRecord(snapshot)) {
      errors.push(`CASCADE-002: snapshot #${index + 1} deve ser objeto.`);
      continue;
    }

    const id = asNonEmptyString(snapshot.id);
    const profile = asNonEmptyString(snapshot.profile);
    const baselinePath = asNonEmptyString(snapshot.baseline_path);
    const currentPath = asNonEmptyString(snapshot.current_path);
    const expectedHash = asNonEmptyString(snapshot.sha256);
    const renderer = asNonEmptyString(snapshot.renderer);
    const label = id ?? `snapshot #${index + 1}`;

    if (!id) errors.push(`CASCADE-002: ${label} deve declarar id.`);
    if (!profile) errors.push(`CASCADE-002: ${label} deve declarar profile.`);
    if (!baselinePath) errors.push(`CASCADE-002: ${label} deve declarar baseline_path.`);
    if (!currentPath) errors.push(`CASCADE-002: ${label} deve declarar current_path.`);
    if (!expectedHash) errors.push(`CASCADE-002: ${label} deve declarar sha256.`);
    if (!renderer) errors.push(`CASCADE-002: ${label} deve declarar renderer.`);
    if (!Array.isArray(snapshot.requirement_refs) || snapshot.requirement_refs.length === 0) {
      errors.push(`CASCADE-002: ${label} deve declarar requirement_refs.`);
    }
    if (profile && !REQUIRED_SNAPSHOT_PROFILES.includes(profile as (typeof REQUIRED_SNAPSHOT_PROFILES)[number])) {
      errors.push(`CASCADE-002: ${label} usa perfil inválido: ${profile}.`);
    }
    if (!id || !profile || !baselinePath || !currentPath || !expectedHash) continue;

    const baselineFullPath = resolveSafePath(root, baselinePath);
    const currentFullPath = resolveSafePath(root, currentPath);
    if (!baselineFullPath) {
      errors.push(`CASCADE-002: ${label} baseline_path deve ser relativo ao repositório.`);
      continue;
    }
    if (!currentFullPath) {
      errors.push(`CASCADE-002: ${label} current_path deve ser relativo ao repositório.`);
      continue;
    }
    if (!existsSync(baselineFullPath)) {
      errors.push(`CASCADE-002: ${label} baseline ausente: ${normalizePath(baselinePath)}.`);
      continue;
    }
    if (!existsSync(currentFullPath)) {
      errors.push(`CASCADE-002: ${label} snapshot atual ausente: ${normalizePath(currentPath)}.`);
      continue;
    }

    const baselineHash = sha256File(baselineFullPath);
    const currentHash = sha256File(currentFullPath);
    checkedSnapshots += 1;
    checkedProfiles.push(profile);

    if (baselineHash !== expectedHash.toLowerCase()) {
      errors.push(
        `CASCADE-003: ${label} baseline diverge do sha256 do manifest (${baselineHash} != ${expectedHash.toLowerCase()}).`,
      );
    }
    if (currentHash !== baselineHash) {
      errors.push(`CASCADE-003: ${label} snapshot atual diverge do baseline (${currentHash} != ${baselineHash}).`);
    }
  }

  const snapshotsPerProfile = snapshotCountPolicy(manifest);
  for (const profile of REQUIRED_SNAPSHOT_PROFILES) {
    const count = checkedProfiles.filter((checkedProfile) => checkedProfile === profile).length;
    if (count < snapshotsPerProfile) {
      errors.push(`CASCADE-002: perfil ${profile} tem ${count}/${snapshotsPerProfile} snapshot(s) canônico(s).`);
    }
  }

  return {
    errors,
    checkedSnapshots,
    checkedProfiles: uniqueSorted(checkedProfiles),
  };
}

function loadSnapshotManifest(path: string, errors: string[]) {
  try {
    const parsed = yamlLoad(readFileSync(path, "utf8"));
    if (!isRecord(parsed)) {
      errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve conter objeto YAML.`);
      return undefined;
    }
    return parsed as SnapshotManifest;
  } catch (error) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} inválido: ${(error as Error).message}`);
    return undefined;
  }
}

function validateSnapshotPolicy(manifest: SnapshotManifest, errors: string[]) {
  if (manifest.version !== 1) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar version: 1.`);
  }
  if (manifest.source !== REQUIRED_SNAPSHOT_SOURCE) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve apontar source: ${REQUIRED_SNAPSHOT_SOURCE}.`);
  }

  const policy = manifest.policy;
  if (!isRecord(policy)) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar policy.`);
    return;
  }

  const profiles = Array.isArray(policy.profiles_required) ? policy.profiles_required : [];
  for (const profile of REQUIRED_SNAPSHOT_PROFILES) {
    if (!profiles.includes(profile)) {
      errors.push(`CASCADE-002: policy.profiles_required deve incluir ${profile}.`);
    }
  }
  if (snapshotCountPolicy(manifest) < 1) {
    errors.push("CASCADE-002: policy.snapshots_per_profile deve ser >= 1.");
  }
  if (policy.fail_on_diff !== true) {
    errors.push("CASCADE-002: policy.fail_on_diff deve ser true.");
  }

  const approvers = Array.isArray(policy.approval_required_for_baseline_update)
    ? policy.approval_required_for_baseline_update
    : [];
  for (const approver of REQUIRED_BASELINE_APPROVERS) {
    if (!approvers.includes(approver)) {
      errors.push(`CASCADE-002: baseline update deve exigir aprovação de ${approver}.`);
    }
  }
}

function buildGates(requiresFullRegression: boolean): CascadeGate[] {
  const gates: CascadeGate[] = [
    {
      level: "L3",
      gate: "pre-commit-gates",
      required: true,
      reason: "Código sempre passa pelos gates duros de lint, ownership, dossiê e governança.",
    },
  ];

  if (requiresFullRegression) {
    gates.push(
      {
        level: "L4",
        gate: "full-regression",
        required: true,
        reason: "Mudança em área crítica exige 100% dos REQs blocker/high ligados à área.",
      },
      {
        level: "L4",
        gate: "snapshot-diff",
        required: true,
        reason: "Mudança em área crítica exige diff dos certificados canônicos antes do merge.",
      },
    );
  } else {
    gates.push({
      level: "L4",
      gate: "impact-analysis",
      required: true,
      reason: "Mudança fora da lista crítica usa análise de impacto e suite sentinela mínima.",
    });
  }

  return gates;
}

function selectAreaRegressionTests(requirements: Requirement[], criticalAreas: readonly string[]) {
  const selected = requirements
    .filter((requirement) => requirement.criticality === "blocker" || requirement.criticality === "high")
    .filter((requirement) =>
      (requirement.critical_paths ?? []).some((path) =>
        criticalAreas.some((area) => pathPatternsIntersect(path, area)),
      ),
    )
    .flatMap((requirement) => requirement.linked_tests ?? []);

  return uniqueSorted(selected);
}

function pathPatternsIntersect(left: string, right: string) {
  const normalizedLeft = normalizePath(left);
  const normalizedRight = normalizePath(right);
  if (normalizedLeft === normalizedRight) return true;
  const leftPrefix = patternPrefix(normalizedLeft);
  const rightPrefix = patternPrefix(normalizedRight);
  return leftPrefix.startsWith(rightPrefix) || rightPrefix.startsWith(leftPrefix);
}

function patternPrefix(pattern: string) {
  const wildcardIndex = pattern.indexOf("*");
  return wildcardIndex === -1 ? pattern : pattern.slice(0, wildcardIndex);
}

function matchesPathPattern(path: string, pattern: string) {
  const normalizedPattern = normalizePath(pattern);
  if (normalizedPattern.endsWith("/**")) {
    return path.startsWith(normalizedPattern.slice(0, -3));
  }
  if (normalizedPattern.includes("*")) {
    const regex = new RegExp(`^${escapeRegex(normalizedPattern).replace(/\\\*/g, ".*")}$`);
    return regex.test(path);
  }
  return path === normalizedPattern;
}

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function uniqueSorted(values: string[]) {
  return [...new Set(values)].sort();
}

function snapshotCountPolicy(manifest: SnapshotManifest) {
  const value = manifest.policy?.snapshots_per_profile;
  return typeof value === "number" && Number.isInteger(value) ? value : 0;
}

function sha256File(path: string) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function resolveSafePath(root: string, path: string) {
  const normalized = normalizePath(path);
  if (normalized.startsWith("/") || normalized.startsWith("../") || normalized.includes("/../")) return undefined;
  if (/^[a-zA-Z]:\//.test(normalized)) return undefined;

  const fullPath = resolve(root, normalized);
  const rootPath = resolve(root);
  return fullPath.startsWith(rootPath) ? fullPath : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asNonEmptyString(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function parseCliArgs(argv: string[]) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "check";
  const changedFiles: string[] = [];
  let release = "";
  let json = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--changed") {
      changedFiles.push(args[++index]);
    } else if (arg === "--release") {
      release = args[++index];
    } else if (arg === "--json") {
      json = true;
    } else {
      changedFiles.push(arg);
    }
  }

  return { command, changedFiles, release, json };
}

function runCli() {
  const { command, changedFiles, release, json } = parseCliArgs(process.argv.slice(2));
  if (command === "plan") {
    const plan = buildCascadePlan(process.cwd(), changedFiles);
    if (json) console.log(JSON.stringify(plan, null, 2));
    else {
      console.log(`verification-cascade: ${plan.criticalAreas.length} área(s) crítica(s).`);
      console.log(`full-regression: ${plan.requiresFullRegression ? "sim" : "não"}`);
      console.log(`snapshot-diff: ${plan.requiresSnapshotDiff ? "sim" : "não"}`);
      for (const test of plan.regressionTests) console.log(test);
    }
    return 0;
  }

  if (command === "release-audits") {
    if (!release) {
      console.error("Uso: verification-cascade release-audits --release <versao>");
      return 2;
    }
    const auditCheck = checkReleaseAudits(process.cwd(), release);
    if (json) console.log(JSON.stringify(auditCheck, null, 2));
    else {
      console.log(`verification-cascade: release ${release}, ${auditCheck.missing.length} parecer(es) ausente(s).`);
      for (const missing of auditCheck.missing) console.error(`ERROR CASCADE-005: parecer L5 ausente: ${missing}.`);
    }
    return auditCheck.missing.length > 0 ? 1 : 0;
  }

  if (command !== "check") {
    console.error("Uso: verification-cascade [check|plan|release-audits] [--changed <arquivo>] [--release <versao>] [--json]");
    return 2;
  }

  const result = checkVerificationCascade();
  console.log(`verification-cascade: check estrutural + snapshot-diff (${result.checkedSnapshots} snapshot(s)).`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
