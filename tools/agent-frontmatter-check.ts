import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const AGENTS_DIR = ".claude/agents";
const EXPECTED_AGENTS = [
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
] as const;

const AUDITORS = new Set(["legal-counsel", "metrology-auditor", "senior-reviewer"]);
const ALLOWED_MODELS = new Set(["haiku", "sonnet", "opus"]);
const ALLOWED_ROLES = new Set(["executor", "auditor"]);
const ALLOWED_TOOLS = new Set(["Read", "Edit", "Write", "Grep", "Glob", "Bash", "MultiEdit"]);
const WRITE_TOOLS = new Set(["Edit", "Write", "MultiEdit"]);

const REQUIRED_FIELDS = [
  "schema_version",
  "name",
  "role",
  "description",
  "model",
  "tools",
  "owner_paths",
  "blocked_write_paths",
  "handoff_targets",
] as const;

type Frontmatter = Record<string, unknown>;

export type AgentFrontmatterCheck = {
  errors: string[];
  checkedAgents: number;
};

export function checkAgentFrontmatter(root = process.cwd()): AgentFrontmatterCheck {
  const errors: string[] = [];
  const agentsDir = resolve(root, AGENTS_DIR);
  if (!existsSync(agentsDir)) {
    return { errors: [`AGENT-FM-001: diretório de agentes ausente: ${AGENTS_DIR}.`], checkedAgents: 0 };
  }

  const files = readdirSync(agentsDir)
    .filter((file) => file.endsWith(".md"))
    .sort((a, b) => a.localeCompare(b));

  const seen = new Set<string>();
  for (const file of files) {
    const filePath = `${AGENTS_DIR}/${file}`;
    const expectedName = basename(file, ".md");
    const content = readFileSync(join(agentsDir, file), "utf8");
    const frontmatter = parseFrontmatter(content, filePath, errors);
    if (!frontmatter) continue;

    const name = stringValue(frontmatter.name);
    const role = stringValue(frontmatter.role);
    const model = stringValue(frontmatter.model);
    const tools = arrayValue(frontmatter.tools);
    const ownerPaths = arrayValue(frontmatter.owner_paths);
    const blockedWritePaths = arrayValue(frontmatter.blocked_write_paths);
    const handoffTargets = arrayValue(frontmatter.handoff_targets);

    seen.add(name);

    if (name !== expectedName || !isKebabCase(name) || !EXPECTED_AGENTS.includes(name as (typeof EXPECTED_AGENTS)[number])) {
      errors.push(`AGENT-FM-001: ${filePath} deve ter filename/name canônicos; encontrado name: ${name || "<ausente>"}.`);
    }

    for (const field of REQUIRED_FIELDS) {
      if (!(field in frontmatter)) {
        errors.push(`AGENT-FM-002: ${filePath} sem campo obrigatório ${field}.`);
      }
    }

    if (frontmatter.schema_version !== 1) {
      errors.push(`AGENT-FM-002: ${filePath} deve declarar schema_version: 1.`);
    }
    if (!ALLOWED_ROLES.has(role)) {
      errors.push(`AGENT-FM-002: ${filePath} role inválido: ${role || "<ausente>"}.`);
    }
    if (AUDITORS.has(name) && role !== "auditor") {
      errors.push(`AGENT-FM-002: ${filePath} auditor externo deve declarar role: auditor.`);
    }
    if (!AUDITORS.has(name) && role === "auditor") {
      errors.push(`AGENT-FM-002: ${filePath} somente auditores externos podem declarar role: auditor.`);
    }
    if (!ALLOWED_MODELS.has(model)) {
      errors.push(`AGENT-FM-002: ${filePath} model inválido: ${model || "<ausente>"}.`);
    }
    if (AUDITORS.has(name) && model !== "opus") {
      errors.push(`AGENT-FM-002: ${filePath} auditor externo deve usar model: opus.`);
    }
    if (!stringValue(frontmatter.description) || stringValue(frontmatter.description).includes("\n")) {
      errors.push(`AGENT-FM-002: ${filePath} description deve ter uma linha.`);
    }
    if (!tools.length) {
      errors.push(`AGENT-FM-002: ${filePath} tools deve ser lista não vazia.`);
    }
    for (const tool of tools) {
      if (!ALLOWED_TOOLS.has(tool)) errors.push(`AGENT-FM-003: ${filePath} tool inválida: ${tool}.`);
    }
    for (const tool of tools) {
      if (AUDITORS.has(name) && WRITE_TOOLS.has(tool)) {
        errors.push(`AGENT-FM-005: ${name} não pode declarar ferramenta de escrita ${tool}.`);
      }
    }
    if (!ownerPaths.length) {
      errors.push(`AGENT-FM-002: ${filePath} owner_paths deve ser lista não vazia.`);
    }
    if (!blockedWritePaths.length) {
      errors.push(`AGENT-FM-002: ${filePath} blocked_write_paths deve ser lista não vazia.`);
    }
    for (const target of handoffTargets) {
      if (!EXPECTED_AGENTS.includes(target as (typeof EXPECTED_AGENTS)[number])) {
        errors.push(`AGENT-FM-006: ${filePath} handoff_targets referencia agente inexistente: ${target}.`);
      }
    }
  }

  for (const expected of EXPECTED_AGENTS) {
    if (!seen.has(expected)) errors.push(`AGENT-FM-001: agente canônico ausente: ${AGENTS_DIR}/${expected}.md.`);
  }

  return { errors, checkedAgents: files.length };
}

function parseFrontmatter(content: string, filePath: string, errors: string[]): Frontmatter | null {
  const normalized = content.replace(/\r\n/g, "\n");
  const match = normalized.match(/^---\n([\s\S]*?)\n---/);
  if (!match?.[1]) {
    errors.push(`AGENT-FM-002: ${filePath} sem frontmatter YAML.`);
    return null;
  }
  try {
    const parsed = yamlLoad(match[1]);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      errors.push(`AGENT-FM-002: ${filePath} frontmatter deve ser mapa YAML.`);
      return null;
    }
    return parsed as Frontmatter;
  } catch (error) {
    errors.push(`AGENT-FM-002: ${filePath} frontmatter YAML inválido: ${error instanceof Error ? error.message : String(error)}.`);
    return null;
  }
}

function stringValue(value: unknown) {
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value.map(stringValue).filter(Boolean) : [];
}

function isKebabCase(value: string) {
  return /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value);
}

function runCli() {
  const result = checkAgentFrontmatter();
  console.log(`agent-frontmatter-check: ${result.checkedAgents}/13 agente(s) verificados.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
