import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { loadRequirements, type Requirement } from "./validation-dossier";

const VERIFICATION_LOG_README = "compliance/verification-log/README.md";

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
  return { errors };
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
  console.log("verification-cascade: check estrutural.");
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
