import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const COMMANDS_DIR = ".claude/commands";
const REQUIRED_COMMANDS = ["spec-norm-diff", "ac-evidence", "claim-check", "tenant-fuzz", "emit-cert-dry"] as const;
const REQUIRED_FIELDS = ["description", "owner", "risk_level", "required_commands"] as const;
const REQUIRED_SECTIONS = ["Objetivo", "Execução", "Evidência", "Escalonamento", "Referências"] as const;
const VALID_OWNERS = new Set([
  "android",
  "backend-api",
  "copy-compliance",
  "db-schema",
  "legal-counsel",
  "lgpd-security",
  "metrology-auditor",
  "metrology-calc",
  "product-governance",
  "qa-acceptance",
  "regulator",
  "senior-reviewer",
  "web-ui",
]);
const VALID_RISK_LEVELS = new Set(["low", "medium", "high", "blocker"]);

type Frontmatter = Record<string, unknown>;

export type RegulatorySlashCommandsCheck = {
  errors: string[];
  checkedCommands: number;
};

export function checkRegulatorySlashCommands(root = process.cwd()): RegulatorySlashCommandsCheck {
  const errors: string[] = [];
  let checkedCommands = 0;

  for (const command of REQUIRED_COMMANDS) {
    const relativePath = `${COMMANDS_DIR}/${command}.md`;
    const absolutePath = resolve(root, relativePath);
    if (!existsSync(absolutePath)) {
      errors.push(`SLASH-001: comando regulatório ausente: ${relativePath}.`);
      continue;
    }

    checkedCommands += 1;
    const content = readFileSync(absolutePath, "utf8");
    checkCommand(relativePath, command, content, errors);
  }

  return { errors, checkedCommands };
}

function checkCommand(relativePath: string, command: string, content: string, errors: string[]) {
  const frontmatter = parseFrontmatter(relativePath, content, errors);
  if (!frontmatter) return;

  for (const field of REQUIRED_FIELDS) {
    if (!(field in frontmatter)) {
      errors.push(`SLASH-002: ${relativePath} sem campo obrigatório ${field}.`);
    }
  }

  const owner = stringValue(frontmatter.owner);
  if (owner && !VALID_OWNERS.has(owner)) {
    errors.push(`SLASH-003: ${relativePath} owner inválido: ${owner}.`);
  }

  const riskLevel = stringValue(frontmatter.risk_level);
  if (riskLevel && !VALID_RISK_LEVELS.has(riskLevel)) {
    errors.push(`SLASH-003: ${relativePath} risk_level inválido: ${riskLevel}.`);
  }

  const requiredCommands = arrayValue(frontmatter.required_commands);
  if ("required_commands" in frontmatter && requiredCommands.length === 0) {
    errors.push(`SLASH-002: ${relativePath} required_commands deve ser lista não vazia.`);
  }

  for (const section of REQUIRED_SECTIONS) {
    if (!hasSection(content, section)) {
      errors.push(`SLASH-004: ${relativePath} sem seção obrigatória ## ${section}.`);
    }
  }

  const commandTitle = new RegExp(`^#\\s+/${escapeRegex(command)}\\b`, "im");
  if (!commandTitle.test(content)) {
    errors.push(`SLASH-004: ${relativePath} deve declarar título # /${command}.`);
  }

  if (!hasExecutableBlock(content)) {
    errors.push(`SLASH-005: ${relativePath} deve conter bloco executável em ## Execução.`);
  }
}

function parseFrontmatter(relativePath: string, content: string, errors: string[]): Frontmatter | null {
  const normalized = content.replace(/\r\n/g, "\n");
  const match = normalized.match(/^---\n([\s\S]*?)\n---/);
  if (!match?.[1]) {
    errors.push(`SLASH-002: ${relativePath} sem frontmatter YAML.`);
    return null;
  }

  try {
    const parsed = yamlLoad(match[1]);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      errors.push(`SLASH-002: ${relativePath} frontmatter deve ser mapa YAML.`);
      return null;
    }
    return parsed as Frontmatter;
  } catch (error) {
    errors.push(`SLASH-002: ${relativePath} frontmatter YAML inválido: ${error instanceof Error ? error.message : String(error)}.`);
    return null;
  }
}

function hasSection(markdown: string, section: string) {
  return new RegExp(`^##\\s+${escapeRegex(section)}\\b`, "im").test(markdown);
}

function hasExecutableBlock(markdown: string) {
  const normalized = markdown.replace(/\r\n/g, "\n");
  const execution = normalized.match(/(?:^|\n)## Execução\n+([\s\S]*?)(?=\n## |\n*$)/)?.[1] ?? "";
  return /```(?:bash|sh|powershell)?\n[\s\S]*?\b(pnpm|tsx|node|bash|gh|git)\b[\s\S]*?```/i.test(execution);
}

function stringValue(value: unknown) {
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value.map(stringValue).filter(Boolean) : [];
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function runCli() {
  const result = checkRegulatorySlashCommands();
  console.log(`slash-commands-check: ${result.checkedCommands}/5 comando(s) regulatório(s) verificados.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
