import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const ESCALATION_ROOT = "compliance/escalations";
const README_PATH = `${ESCALATION_ROOT}/README.md`;
const TEMPLATE_PATH = `${ESCALATION_ROOT}/_template.md`;
const TIEBREAKER_ADR = "adr/0009-tiebreaker-designation.md";

const ESCALATION_TYPES = new Set(["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]);
const CLOSED_STATUSES = new Set(["resolved", "superseded"]);
const REQUIRED_FRONTMATTER_FIELDS = [
  "id",
  "status",
  "type",
  "opened_at",
  "trigger",
  "agents",
  "affected_paths",
  "tiebreaker_adr",
  "sla",
  "owner",
] as const;
const REQUIRED_SECTIONS = [
  "Posições",
  "Impacto se não resolvido",
  "Resolução",
  "Assinaturas",
  "Aprendizado",
] as const;

export type EscalationCheckResult = {
  errors: string[];
  checkedEscalations: number;
  openEscalations: number;
};

type EscalationFrontmatter = Record<string, unknown>;

export function checkEscalations(root = process.cwd()): EscalationCheckResult {
  const errors: string[] = [];
  checkRequiredArtifacts(root, errors);

  const escalationFiles = listEscalationFiles(root);
  let openEscalations = 0;
  for (const relativePath of escalationFiles) {
    const absolutePath = resolve(root, relativePath);
    const content = readFileSync(absolutePath, "utf8");
    const frontmatter = parseFrontmatter(content);
    const status = stringValue(frontmatter.status);

    checkEscalationFrontmatter(relativePath, frontmatter, errors);
    checkEscalationSections(relativePath, content, status, errors);

    if (!CLOSED_STATUSES.has(status)) {
      openEscalations += 1;
      errors.push(
        `ESC-004: ${relativePath} está com status: ${status || "<ausente>"}; escalations abertas não podem ser mergeadas.`,
      );
    }
  }

  return {
    errors,
    checkedEscalations: escalationFiles.length,
    openEscalations,
  };
}

function checkRequiredArtifacts(root: string, errors: string[]) {
  if (!existsSync(resolve(root, README_PATH))) {
    errors.push(`ESC-001: registro canônico ausente: ${README_PATH}.`);
  }

  const templateFile = resolve(root, TEMPLATE_PATH);
  if (!existsSync(templateFile)) {
    errors.push(`ESC-001: template obrigatório ausente: ${TEMPLATE_PATH}.`);
  } else {
    const template = readFileSync(templateFile, "utf8");
    const frontmatter = parseFrontmatter(template);
    for (const field of REQUIRED_FRONTMATTER_FIELDS) {
      if (!(field in frontmatter)) {
        errors.push(`ESC-002: ${TEMPLATE_PATH} sem campo de frontmatter ${field}.`);
      }
    }
    for (const section of REQUIRED_SECTIONS) {
      if (!hasSection(template, section)) {
        errors.push(`ESC-003: ${TEMPLATE_PATH} sem seção obrigatória ## ${section}.`);
      }
    }
  }

  const adrFile = resolve(root, TIEBREAKER_ADR);
  if (!existsSync(adrFile)) {
    errors.push(`ESC-001: ADR de tiebreaker ausente: ${TIEBREAKER_ADR}.`);
    return;
  }

  const adr = normalizeText(readFileSync(adrFile, "utf8"));
  if (!adr.includes("responsavel tecnico do produto")) {
    errors.push(`ESC-006: ${TIEBREAKER_ADR} deve designar o Responsável Técnico do Produto.`);
  }
  if (!adr.includes("product-governance")) {
    errors.push(`ESC-006: ${TIEBREAKER_ADR} deve exigir sucessão/aprovação por product-governance.`);
  }
}

function checkEscalationFrontmatter(relativePath: string, frontmatter: EscalationFrontmatter, errors: string[]) {
  for (const field of REQUIRED_FRONTMATTER_FIELDS) {
    if (!(field in frontmatter)) {
      errors.push(`ESC-002: ${relativePath} sem campo obrigatório ${field}.`);
    }
  }

  const type = stringValue(frontmatter.type);
  if (type && !ESCALATION_TYPES.has(type)) {
    errors.push(`ESC-002: ${relativePath} type inválido: ${type}; esperado D1-D9.`);
  }

  const agents = arrayValue(frontmatter.agents);
  if (agents.length < 2) {
    errors.push(`ESC-002: ${relativePath} deve declarar pelo menos 2 agentes envolvidos.`);
  }

  const affectedPaths = arrayValue(frontmatter.affected_paths);
  if (affectedPaths.length === 0) {
    errors.push(`ESC-002: ${relativePath} deve declarar affected_paths.`);
  }

  const tiebreakerAdr = stringValue(frontmatter.tiebreaker_adr);
  if (tiebreakerAdr !== TIEBREAKER_ADR) {
    errors.push(`ESC-002: ${relativePath} deve apontar tiebreaker_adr para ${TIEBREAKER_ADR}.`);
  }

  const openedAt = stringValue(frontmatter.opened_at);
  if (openedAt && !isIsoLikeDateTime(openedAt)) {
    errors.push(`ESC-002: ${relativePath} opened_at deve usar timestamp ISO-8601.`);
  }

  const status = stringValue(frontmatter.status);
  if (CLOSED_STATUSES.has(status)) {
    const resolvedAt = stringValue(frontmatter.resolved_at);
    if (!resolvedAt) {
      errors.push(`ESC-002: ${relativePath} com status ${status} deve declarar resolved_at.`);
    } else if (!isIsoLikeDateTime(resolvedAt)) {
      errors.push(`ESC-002: ${relativePath} resolved_at deve usar timestamp ISO-8601.`);
    }
  }
}

function checkEscalationSections(relativePath: string, content: string, status: string, errors: string[]) {
  for (const section of REQUIRED_SECTIONS) {
    if (!hasSection(content, section)) {
      errors.push(`ESC-003: ${relativePath} sem seção obrigatória ## ${section}.`);
    }
  }

  if (!CLOSED_STATUSES.has(status)) return;

  const resolution = sectionContent(content, "Resolução");
  if (isPlaceholder(resolution)) {
    errors.push(`ESC-005: ${relativePath} resolvida sem conteúdo efetivo em ## Resolução.`);
  }

  const signatures = sectionContent(content, "Assinaturas");
  if (!isIsoLikeDateTime(signatures)) {
    errors.push(`ESC-005: ${relativePath} deve registrar assinatura com timestamp ISO-8601.`);
  }
}

function listEscalationFiles(root: string) {
  const escalationDir = resolve(root, ESCALATION_ROOT);
  if (!existsSync(escalationDir)) return [];
  return readdirSync(escalationDir, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name)
    .filter((name) => name.endsWith(".md"))
    .filter((name) => name !== "README.md" && name !== "_template.md")
    .sort()
    .map((name) => `${ESCALATION_ROOT}/${name}`);
}

function parseFrontmatter(markdown: string): EscalationFrontmatter {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const parsed = yamlLoad(match[1]);
  return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as EscalationFrontmatter) : {};
}

function hasSection(markdown: string, section: string) {
  return new RegExp(`^##\\s+${escapeRegex(section)}\\b`, "im").test(markdown);
}

function sectionContent(markdown: string, section: string) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const start = lines.findIndex((line) => new RegExp(`^##\\s+${escapeRegex(section)}\\b`, "i").test(line));
  if (start === -1) return "";

  const sectionLines: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (/^##\s+/.test(line)) break;
    sectionLines.push(line);
  }
  return sectionLines.join("\n").trim();
}

function isPlaceholder(value: string) {
  const normalized = normalizeText(value).trim();
  return (
    normalized.length === 0 ||
    normalized === "pendente." ||
    normalized === "preencher ao resolver." ||
    normalized === "tbd"
  );
}

function stringValue(value: unknown) {
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value.map(stringValue).filter(Boolean) : [];
}

function isIsoLikeDateTime(value: string) {
  return /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})/.test(value);
}

function normalizeText(text: string) {
  return text
    .replace(/\r\n/g, "\n")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function runCli() {
  const result = checkEscalations();
  console.log(
    `escalation-check: ${result.checkedEscalations} escalation(s), ${result.openEscalations} aberta(s).`,
  );
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
