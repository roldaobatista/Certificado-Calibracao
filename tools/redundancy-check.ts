import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

import { loadRequirements, type Criticality, type Requirement } from "./validation-dossier";

const PROPERTY_CONFIG = "evals/property-config.yaml";
const FLAKE_LOG_README = "compliance/validation-dossier/flake-log/README.md";
const REGULATOR_DECISIONS_README = "compliance/regulator-decisions/README.md";
const NIGHTLY_FLAKE_GATE_WORKFLOW = ".github/workflows/nightly-flake-gate.yml";

const MIN_SEEDS_BY_CRITICALITY: Record<Criticality, number> = {
  blocker: 500,
  high: 100,
  medium: 50,
  low: 10,
};

const REGULATORY_DOUBLE_CHECK_RULES = [
  {
    pattern: "packages/normative-rules/**",
    reason: "packages/normative-rules/** exige duas passagens do regulator.",
  },
  {
    pattern: "apps/api/src/domain/emission/**",
    reason: "apps/api/src/domain/emission/** exige duas passagens do regulator para regras de bloqueio.",
  },
] as const;

const ADJACENT_REVIEW_RULES = [
  {
    pattern: "apps/api/src/domain/emission/**",
    agents: ["regulator", "metrology-calc"],
  },
  {
    pattern: "packages/engine-uncertainty/**",
    agents: ["regulator"],
  },
  {
    pattern: "packages/normative-rules/**",
    agents: ["metrology-calc", "qa-acceptance"],
  },
  {
    pattern: "packages/audit-log/**",
    agents: ["lgpd-security"],
  },
  {
    pattern: "packages/db/**",
    agents: ["lgpd-security"],
  },
] as const;

type PropertyConfigEntry = {
  req?: string;
  criticality?: Criticality;
  N?: number;
  canonical_seeds?: unknown[];
  test?: string;
  command?: string;
  report_path?: string;
};

export type RedundancyCheckResult = {
  errors: string[];
  checkedProperties: number;
  checkedFlakeGate: boolean;
  checkedRegulatoryRecords: boolean;
};

export type RedundancyPlan = {
  changedFiles: string[];
  requiresRegulatoryDoubleCheck: boolean;
  regulatoryDoubleCheckReasons: string[];
  requiredReviewAgents: string[];
};

export function checkRedundancy(root = process.cwd()): RedundancyCheckResult {
  const errors: string[] = [];
  const properties = loadPropertyConfig(root, errors);
  const requirementsById = new Map(loadRequirements(root).map((requirement) => [requirement.id, requirement]));

  for (const [index, property] of properties.entries()) {
    validatePropertyConfigEntry(root, property, index, requirementsById, errors);
  }

  const checkedFlakeGate = checkFlakeGate(root, errors);
  const checkedRegulatoryRecords = existsSync(resolve(root, REGULATOR_DECISIONS_README));
  if (!checkedRegulatoryRecords) {
    errors.push(`REDUNDANCY-001: registro de decisoes regulatorias ausente: ${REGULATOR_DECISIONS_README}.`);
  }

  return {
    errors,
    checkedProperties: properties.length,
    checkedFlakeGate,
    checkedRegulatoryRecords,
  };
}

export function buildRedundancyPlan(changedFiles: string[]): RedundancyPlan {
  const normalizedChangedFiles = changedFiles.map(normalizePath);
  const regulatoryDoubleCheckReasons = REGULATORY_DOUBLE_CHECK_RULES
    .filter((rule) => normalizedChangedFiles.some((changedFile) => matchesPathPattern(changedFile, rule.pattern)))
    .map((rule) => rule.reason);
  const requiredReviewAgents = ADJACENT_REVIEW_RULES
    .filter((rule) => normalizedChangedFiles.some((changedFile) => matchesPathPattern(changedFile, rule.pattern)))
    .flatMap((rule) => [...rule.agents]);

  return {
    changedFiles: normalizedChangedFiles,
    requiresRegulatoryDoubleCheck: regulatoryDoubleCheckReasons.length > 0,
    regulatoryDoubleCheckReasons: uniqueSorted(regulatoryDoubleCheckReasons),
    requiredReviewAgents: uniqueSorted(requiredReviewAgents),
  };
}

function loadPropertyConfig(root: string, errors: string[]) {
  const configPath = resolve(root, PROPERTY_CONFIG);
  if (!existsSync(configPath)) {
    errors.push(`REDUNDANCY-001: configuracao de property testing ausente: ${PROPERTY_CONFIG}.`);
    return [] as PropertyConfigEntry[];
  }

  const parsed = yamlLoad(readFileSync(configPath, "utf8"));
  if (!Array.isArray(parsed)) {
    errors.push(`REDUNDANCY-002: ${PROPERTY_CONFIG} deve conter uma lista YAML.`);
    return [];
  }

  if (parsed.length === 0) {
    errors.push(`REDUNDANCY-002: ${PROPERTY_CONFIG} deve declarar ao menos uma propriedade.`);
  }

  return parsed as PropertyConfigEntry[];
}

function validatePropertyConfigEntry(
  root: string,
  property: PropertyConfigEntry,
  index: number,
  requirementsById: Map<string, Requirement>,
  errors: string[],
) {
  const label = property.req ?? `<property #${index + 1}>`;
  if (!property.req) errors.push(`REDUNDANCY-002: ${label} sem campo obrigatorio req.`);
  if (!property.criticality || !isCriticality(property.criticality)) {
    errors.push(`REDUNDANCY-002: ${label} tem criticality invalida: ${property.criticality}.`);
    return;
  }

  const requiredSeeds = MIN_SEEDS_BY_CRITICALITY[property.criticality];
  if (!Number.isInteger(property.N) || Number(property.N) < requiredSeeds) {
    errors.push(
      `REDUNDANCY-003: ${label} com criticality ${property.criticality} exige N minimo ${requiredSeeds}, recebeu ${property.N}.`,
    );
  }

  if (!Array.isArray(property.canonical_seeds) || property.canonical_seeds.length === 0) {
    errors.push(`REDUNDANCY-004: ${label} deve declarar canonical_seeds nao vazio.`);
  }

  if (!property.test) {
    errors.push(`REDUNDANCY-005: ${label} sem campo obrigatorio test.`);
  } else if (!existsSync(resolve(root, property.test))) {
    errors.push(`REDUNDANCY-005: ${label} aponta para teste inexistente: ${property.test}.`);
  }

  if (!property.command) errors.push(`REDUNDANCY-002: ${label} sem campo obrigatorio command.`);
  if (!property.report_path) errors.push(`REDUNDANCY-002: ${label} sem campo obrigatorio report_path.`);

  if (property.req) {
    const requirement = requirementsById.get(property.req);
    if (!requirement) {
      errors.push(`REDUNDANCY-006: ${label} nao existe em compliance/validation-dossier/requirements.yaml.`);
    } else if (requirement.criticality !== property.criticality) {
      errors.push(
        `REDUNDANCY-006: ${label} declara criticality ${property.criticality}, mas o requisito usa ${requirement.criticality}.`,
      );
    }
  }
}

function checkFlakeGate(root: string, errors: string[]) {
  let ok = true;
  if (!existsSync(resolve(root, FLAKE_LOG_README))) {
    errors.push(`REDUNDANCY-001: log de flake ausente: ${FLAKE_LOG_README}.`);
    ok = false;
  }

  const workflowPath = resolve(root, NIGHTLY_FLAKE_GATE_WORKFLOW);
  if (!existsSync(workflowPath)) {
    errors.push(`REDUNDANCY-001: workflow noturno de flake gate ausente: ${NIGHTLY_FLAKE_GATE_WORKFLOW}.`);
    return false;
  }

  const workflow = readFileSync(workflowPath, "utf8");
  if (!/\bschedule\s*:/i.test(workflow)) {
    errors.push(`REDUNDANCY-007: ${NIGHTLY_FLAKE_GATE_WORKFLOW} deve ter gatilho schedule.`);
    ok = false;
  }
  if (!/flake-gate/i.test(workflow)) {
    errors.push(`REDUNDANCY-007: ${NIGHTLY_FLAKE_GATE_WORKFLOW} deve declarar job de flake-gate.`);
    ok = false;
  }

  return ok;
}

function isCriticality(value: string): value is Criticality {
  return Object.hasOwn(MIN_SEEDS_BY_CRITICALITY, value);
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
  let json = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--changed") {
      changedFiles.push(args[++index]);
    } else if (arg === "--json") {
      json = true;
    } else {
      changedFiles.push(arg);
    }
  }

  return { command, changedFiles, json };
}

function runCli() {
  const { command, changedFiles, json } = parseCliArgs(process.argv.slice(2));

  if (command === "plan") {
    const plan = buildRedundancyPlan(changedFiles);
    if (json) console.log(JSON.stringify(plan, null, 2));
    else {
      console.log(`redundancy-check: ${plan.requiredReviewAgents.length} review(s) adjacente(s).`);
      console.log(`regulatory-double-check: ${plan.requiresRegulatoryDoubleCheck ? "sim" : "nao"}`);
      for (const reason of plan.regulatoryDoubleCheckReasons) console.log(reason);
      for (const agent of plan.requiredReviewAgents) console.log(`review:${agent}`);
    }
    return 0;
  }

  if (command !== "check") {
    console.error("Uso: redundancy-check [check|plan] [--changed <arquivo>] [--json]");
    return 2;
  }

  const result = checkRedundancy();
  console.log(
    `redundancy-check: ${result.checkedProperties} propriedade(s), flake-gate ${result.checkedFlakeGate ? "ok" : "faltando"}, decisoes regulatorias ${result.checkedRegulatoryRecords ? "ok" : "faltando"}.`,
  );
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
