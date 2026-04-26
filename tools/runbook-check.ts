import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const RUNBOOK_ROOT = "compliance/runbooks";
const DRILL_SCHEDULE = `${RUNBOOK_ROOT}/drill-schedule.yaml`;
const EXECUTIONS_README = `${RUNBOOK_ROOT}/executions/README.md`;

const REQUIRED_RUNBOOKS = [
  { id: "R1", file: "r1-kms-key-rotation.md" },
  { id: "R2", file: "r2-audit-hash-chain-divergence.md" },
  { id: "R3", file: "r3-worm-object-lock-violation.md" },
  { id: "R4", file: "r4-normative-package-disaster-recovery.md" },
  { id: "R5", file: "r5-emission-revocation.md" },
  { id: "R6", file: "r6-security-incident.md" },
  { id: "R7", file: "r7-backup-restore.md" },
  { id: "R8", file: "r8-reemission-procedure.md" },
] as const;

const REQUIRED_SECTIONS = [
  "Trigger",
  "Impacto",
  "Papéis",
  "Passos",
  "Validação",
  "Evidência",
  "Drill",
  "Revisão",
] as const;

type RunbookId = (typeof REQUIRED_RUNBOOKS)[number]["id"];

type DrillScheduleEntry = {
  id?: string;
  runbook?: string;
  cadence?: string;
  next_due?: string | Date;
  owner?: string;
  evidence_path?: string;
};

export type RunbookCheckResult = {
  errors: string[];
  checkedRunbooks: number;
  checkedDrills: number;
};

export function checkRunbooks(root = process.cwd()): RunbookCheckResult {
  const errors: string[] = [];
  let checkedRunbooks = 0;

  for (const runbook of REQUIRED_RUNBOOKS) {
    const relativePath = `${RUNBOOK_ROOT}/${runbook.file}`;
    const absolutePath = resolve(root, relativePath);
    if (!existsSync(absolutePath)) {
      errors.push(`RUNBOOK-001: runbook obrigatório ausente: ${relativePath}.`);
      continue;
    }

    checkedRunbooks += 1;
    const content = readFileSync(absolutePath, "utf8");
    const frontmatter = parseFrontmatter(content);
    if (frontmatter.id !== runbook.id) {
      errors.push(`RUNBOOK-002: ${relativePath} deve declarar id: ${runbook.id}.`);
    }
    for (const field of ["version", "status", "owner", "rto", "rpo"]) {
      if (!frontmatter[field]) {
        errors.push(`RUNBOOK-002: ${relativePath} sem frontmatter obrigatório ${field}.`);
      }
    }
    for (const section of REQUIRED_SECTIONS) {
      if (!new RegExp(`^##\\s+${escapeRegex(section)}\\b`, "im").test(content)) {
        errors.push(`RUNBOOK-003: ${relativePath} sem seção obrigatória ## ${section}.`);
      }
    }
  }

  if (!existsSync(resolve(root, EXECUTIONS_README))) {
    errors.push(`RUNBOOK-001: diretório de evidências sem README: ${EXECUTIONS_README}.`);
  }

  const drills = loadDrillSchedule(root, errors);
  const drillsById = new Map(drills.map((entry) => [entry.id, entry]));
  for (const runbook of REQUIRED_RUNBOOKS) {
    const entry = drillsById.get(runbook.id);
    if (!entry) {
      errors.push(`RUNBOOK-004: drill-schedule.yaml não cobre ${runbook.id}.`);
      continue;
    }
    const expectedPath = `${RUNBOOK_ROOT}/${runbook.file}`;
    if (entry.runbook !== expectedPath) {
      errors.push(`RUNBOOK-004: ${runbook.id} aponta para runbook incorreto: ${entry.runbook}.`);
    }
    for (const field of ["cadence", "next_due", "owner", "evidence_path"] as const) {
      if (!entry[field]) {
        errors.push(`RUNBOOK-004: ${runbook.id} sem campo obrigatório ${field} no drill-schedule.yaml.`);
      }
    }
    if (entry.evidence_path && !normalizePath(entry.evidence_path).startsWith(`${RUNBOOK_ROOT}/executions/`)) {
      errors.push(`RUNBOOK-004: ${runbook.id} evidence_path deve ficar em ${RUNBOOK_ROOT}/executions/.`);
    }
  }

  return {
    errors,
    checkedRunbooks,
    checkedDrills: drills.filter((entry) => REQUIRED_RUNBOOKS.some((runbook) => runbook.id === entry.id)).length,
  };
}

function loadDrillSchedule(root: string, errors: string[]) {
  const schedulePath = resolve(root, DRILL_SCHEDULE);
  if (!existsSync(schedulePath)) {
    errors.push(`RUNBOOK-001: calendário de drills ausente: ${DRILL_SCHEDULE}.`);
    return [] as DrillScheduleEntry[];
  }

  const parsed = yamlLoad(readFileSync(schedulePath, "utf8"));
  if (!Array.isArray(parsed)) {
    errors.push(`RUNBOOK-004: ${DRILL_SCHEDULE} deve conter uma lista YAML.`);
    return [];
  }

  return parsed as DrillScheduleEntry[];
}

function parseFrontmatter(markdown: string): Record<string, string> {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const parsed = yamlLoad(match[1]);
  return parsed && typeof parsed === "object" && !Array.isArray(parsed)
    ? Object.fromEntries(Object.entries(parsed).map(([key, value]) => [key, String(value)]))
    : {};
}

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function runCli() {
  const result = checkRunbooks();
  console.log(`runbook-check: ${result.checkedRunbooks}/8 runbooks, ${result.checkedDrills}/8 drills.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
