import { existsSync, readFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const AUDIT_ROOT = "compliance/audits";
const ESCALATION_TEMPLATE = `${AUDIT_ROOT}/escalations/_template.md`;
const ESCALATION_README = `${AUDIT_ROOT}/escalations/README.md`;

const AUDITORS = [
  {
    name: "metrology-auditor",
    auditDir: "metrology",
    requiredAllowedPaths: ["compliance/audits/metrology/**"],
  },
  {
    name: "legal-counsel",
    auditDir: "legal",
    requiredAllowedPaths: ["compliance/audits/legal/**", "compliance/legal-opinions/**"],
  },
  {
    name: "senior-reviewer",
    auditDir: "code",
    requiredAllowedPaths: ["compliance/audits/code/**"],
  },
] as const;

const VERDICTS = new Set(["PASS", "FAIL", "PASS_WITH_FINDINGS"]);
const REQUIRED_OPINION_FIELDS = ["auditor", "release", "verdict", "findings", "blockers", "date"] as const;
const REQUIRED_OPINION_SECTIONS = ["Escopo", "Evidência revisada", "Achados", "Veredito"] as const;
const LIMIT_CASES = [
  "Auditoria CGCRE agendada",
  "Processo judicial aberto",
  "Incidente LGPD com dados vazados",
  "Acidente metrológico",
  "Reclamação formal em órgão regulador",
] as const;

type Frontmatter = Record<string, unknown>;

export type ExternalAuditorsCheck = {
  errors: string[];
  checkedAuditors: number;
  checkedTemplates: number;
};

export type ReleaseAuditorOpinionCheck = {
  release: string;
  required: string[];
  missing: string[];
  errors: string[];
};

export function checkExternalAuditors(root = process.cwd()): ExternalAuditorsCheck {
  const errors: string[] = [];
  let checkedAuditors = 0;
  let checkedTemplates = 0;

  if (!existsSync(resolve(root, AUDIT_ROOT, "README.md"))) {
    errors.push(`AUDITOR-001: registro canônico ausente: ${AUDIT_ROOT}/README.md.`);
  }

  for (const auditor of AUDITORS) {
    const agentPath = `.claude/agents/${auditor.name}.md`;
    const absoluteAgentPath = resolve(root, agentPath);
    if (!existsSync(absoluteAgentPath)) {
      errors.push(`AUDITOR-001: agente auditor ausente: ${agentPath}.`);
    } else {
      checkedAuditors += 1;
      checkAgent(root, agentPath, readFileSync(absoluteAgentPath, "utf8"), auditor, errors);
    }

    const readmePath = `${AUDIT_ROOT}/${auditor.auditDir}/README.md`;
    if (!existsSync(resolve(root, readmePath))) {
      errors.push(`AUDITOR-001: README de auditoria ausente: ${readmePath}.`);
    }

    const templatePath = `${AUDIT_ROOT}/${auditor.auditDir}/_template.md`;
    if (!existsSync(resolve(root, templatePath))) {
      errors.push(`AUDITOR-001: template de parecer ausente: ${templatePath}.`);
    } else {
      checkedTemplates += 1;
      checkOpinionFile(root, templatePath, auditor.name, "<versao>", errors, { allowTemplateRelease: true });
    }
  }

  if (!existsSync(resolve(root, ESCALATION_README))) {
    errors.push(`AUDITOR-001: README de casos-limite ausente: ${ESCALATION_README}.`);
  } else {
    const readme = readFileSync(resolve(root, ESCALATION_README), "utf8");
    for (const limitCase of LIMIT_CASES) {
      if (!normalizeText(readme).includes(normalizeText(limitCase))) {
        errors.push(`AUDITOR-004: ${ESCALATION_README} não cobre caso-limite: ${limitCase}.`);
      }
    }
  }

  if (!existsSync(resolve(root, ESCALATION_TEMPLATE))) {
    errors.push(`AUDITOR-001: template de escalonamento humano ausente: ${ESCALATION_TEMPLATE}.`);
  } else {
    checkedTemplates += 1;
    const template = readFileSync(resolve(root, ESCALATION_TEMPLATE), "utf8");
    const frontmatter = parseFrontmatter(template);
    if (frontmatter.requires_human !== true) {
      errors.push(`AUDITOR-004: ${ESCALATION_TEMPLATE} deve declarar requires_human: true.`);
    }
    for (const field of ["case", "status", "date", "recommended_specialist"] as const) {
      if (!(field in frontmatter)) {
        errors.push(`AUDITOR-004: ${ESCALATION_TEMPLATE} sem campo ${field}.`);
      }
    }
  }

  return { errors, checkedAuditors, checkedTemplates };
}

export function checkReleaseAuditorOpinions(root = process.cwd(), release: string): ReleaseAuditorOpinionCheck {
  const required = AUDITORS.map((auditor) => `${AUDIT_ROOT}/${auditor.auditDir}/${release}.md`);
  const missing = required.filter((path) => !existsSync(resolve(root, path)));
  const errors: string[] = [];

  for (const auditor of AUDITORS) {
    const opinionPath = `${AUDIT_ROOT}/${auditor.auditDir}/${release}.md`;
    if (!existsSync(resolve(root, opinionPath))) continue;
    checkOpinionFile(root, opinionPath, auditor.name, release, errors);
  }

  return { release, required, missing, errors };
}

function checkAgent(
  root: string,
  agentPath: string,
  content: string,
  auditor: (typeof AUDITORS)[number],
  errors: string[],
) {
  const frontmatter = parseFrontmatter(content);
  if (stringValue(frontmatter.name) !== auditor.name) {
    errors.push(`AUDITOR-002: ${agentPath} deve declarar name: ${auditor.name}.`);
  }
  if (stringValue(frontmatter.model) !== "opus") {
    errors.push(`AUDITOR-002: ${agentPath} deve usar model: opus.`);
  }

  const tools = arrayValue(frontmatter.tools);
  for (const forbiddenTool of ["Edit", "Write", "MultiEdit"]) {
    if (tools.includes(forbiddenTool)) {
      errors.push(`AUDITOR-003: ${auditor.name} não pode ter ferramenta de escrita ${forbiddenTool}.`);
    }
  }

  const allowedPaths = extractAllowedWritePaths(content);
  for (const required of auditor.requiredAllowedPaths) {
    if (!allowedPaths.includes(required)) {
      errors.push(`AUDITOR-002: ${auditor.name} deve poder escrever em ${required}.`);
    }
  }

  for (const allowedPath of allowedPaths) {
    if (!auditor.requiredAllowedPaths.includes(allowedPath)) {
      errors.push(`AUDITOR-003: ${auditor.name} não pode escrever em ${allowedPath}.`);
    }
    if (isAuditedSourcePath(allowedPath)) {
      errors.push(`AUDITOR-003: ${auditor.name} não pode escrever path auditado: ${allowedPath}.`);
    }
  }

  const expectedAuditDir = `${AUDIT_ROOT}/${auditor.auditDir}`;
  if (!existsSync(resolve(root, expectedAuditDir))) {
    errors.push(`AUDITOR-001: diretório do auditor ausente: ${expectedAuditDir}.`);
  }
}

function checkOpinionFile(
  root: string,
  relativePath: string,
  expectedAuditor: string,
  expectedRelease: string,
  errors: string[],
  options: { allowTemplateRelease?: boolean } = {},
) {
  const content = readFileSync(resolve(root, relativePath), "utf8");
  const frontmatter = parseFrontmatter(content);

  for (const field of REQUIRED_OPINION_FIELDS) {
    if (!(field in frontmatter)) {
      errors.push(`AUDITOR-005: ${relativePath} sem campo obrigatório ${field}.`);
    }
  }

  if (stringValue(frontmatter.auditor) !== expectedAuditor) {
    errors.push(`AUDITOR-005: ${relativePath} deve declarar auditor: ${expectedAuditor}.`);
  }

  const release = stringValue(frontmatter.release);
  if (options.allowTemplateRelease) {
    if (!release) errors.push(`AUDITOR-005: ${relativePath} deve declarar release.`);
  } else if (release !== expectedRelease) {
    errors.push(`AUDITOR-005: ${relativePath} deve declarar release: ${expectedRelease}.`);
  }

  const verdict = stringValue(frontmatter.verdict);
  if (verdict && !VERDICTS.has(verdict)) {
    errors.push(`AUDITOR-005: ${relativePath} verdict inválido: ${verdict}.`);
  }

  const blockers = arrayValue(frontmatter.blockers);
  if (!options.allowTemplateRelease && (verdict === "FAIL" || blockers.length > 0)) {
    errors.push(`AUDITOR-006: ${expectedAuditor} bloqueia release ${expectedRelease} em ${relativePath}.`);
  }

  const findings = frontmatter.findings;
  if (!Array.isArray(findings)) {
    errors.push(`AUDITOR-005: ${relativePath} findings deve ser lista.`);
  }
  if (!Array.isArray(frontmatter.blockers)) {
    errors.push(`AUDITOR-005: ${relativePath} blockers deve ser lista.`);
  }

  const date = stringValue(frontmatter.date);
  if (date && !isIsoLikeDateTime(date)) {
    errors.push(`AUDITOR-005: ${relativePath} date deve usar timestamp ISO-8601.`);
  }

  for (const section of REQUIRED_OPINION_SECTIONS) {
    if (!hasSection(content, section)) {
      errors.push(`AUDITOR-005: ${relativePath} sem seção obrigatória ## ${section}.`);
    }
  }
}

function extractAllowedWritePaths(markdown: string): string[] {
  const normalized = markdown.replace(/\r\n/g, "\n");
  const section = normalized.match(/(?:^|\n)## Paths permitidos \(escrita\)\n+([\s\S]*?)(?=\n## |\n*$)/)?.[1] ?? "";
  return section
    .split("\n")
    .map((line) => line.match(/^\s*-\s+(.+?)\s*$/)?.[1])
    .filter((value): value is string => Boolean(value))
    .map((value) => normalizeAllowedWritePath(value))
    .filter((value): value is string => Boolean(value))
    .filter((value) => value.length > 0);
}

function normalizeAllowedWritePath(value: string): string | undefined {
  const backtickMatch = value.match(/`([^`]+)`/);
  if (backtickMatch) {
    const path = backtickMatch[1].trim();
    return looksLikeRepositoryPath(path) ? path : undefined;
  }

  const trimmed = value.trim();
  if (!looksLikeRepositoryPath(trimmed)) return undefined;
  return trimmed.replace(/\s+\(.+\)$/, "").replace(/\.$/, "");
}

function looksLikeRepositoryPath(value: string) {
  return /^(apps|packages|infra|specs|harness|compliance|adr|evals|tools|\.github|\.claude|\.codex|PRD\.md)(\/|$)/.test(
    value,
  );
}

function parseFrontmatter(markdown: string): Frontmatter {
  const match = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const parsed = yamlLoad(match[1]);
  return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as Frontmatter) : {};
}

function isAuditedSourcePath(path: string) {
  return (
    path.startsWith("apps/") ||
    path.startsWith("packages/") ||
    path.startsWith("infra/") ||
    path.startsWith("specs/") ||
    path.startsWith("harness/") ||
    path === "PRD.md"
  );
}

function hasSection(markdown: string, section: string) {
  return new RegExp(`^##\\s+${escapeRegex(section)}\\b`, "im").test(markdown);
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

function parseCliArgs(argv: string[]) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "check";
  let release = "";
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--release") {
      release = args[++index];
    } else {
      throw new Error(`argumento desconhecido: ${arg}`);
    }
  }
  return { command, release };
}

function runCli() {
  try {
    const { command, release } = parseCliArgs(process.argv.slice(2));
    if (command === "release") {
      if (!release) {
        console.error("Uso: external-auditors-gate release --release <versao>");
        return 2;
      }
      const result = checkReleaseAuditorOpinions(process.cwd(), release);
      console.log(`external-auditors-gate: release ${release}, ${result.missing.length} parecer(es) ausente(s).`);
      for (const missing of result.missing) console.error(`ERROR AUDITOR-007: parecer ausente: ${missing}.`);
      for (const error of result.errors) console.error(`ERROR ${error}`);
      return result.missing.length > 0 || result.errors.length > 0 ? 1 : 0;
    }

    if (command !== "check") {
      console.error("Uso: external-auditors-gate [check|release] [--release <versao>]");
      return 2;
    }

    const result = checkExternalAuditors();
    console.log(`external-auditors-gate: ${result.checkedAuditors}/3 auditores, ${result.checkedTemplates}/4 templates.`);
    for (const error of result.errors) console.error(`ERROR ${error}`);
    return result.errors.length > 0 ? 1 : 0;
  } catch (error) {
    console.error(`external-auditors-gate: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
