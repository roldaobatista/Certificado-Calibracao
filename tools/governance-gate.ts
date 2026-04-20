#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

interface CliOptions {
  workspace: string;
}

interface Finding {
  code: "GOV-001" | "GOV-002" | "GOV-003";
  path: string;
  message: string;
}

const REQUIRED_CODEOWNERS: Array<{ pattern: string; githubOwners: string[]; agentOwners: string[] }> = [
  {
    pattern: "apps/api/src/domain/emission/**",
    githubOwners: ["@roldaobatista"],
    agentOwners: ["@product-governance"],
  },
  {
    pattern: "apps/api/src/domain/audit/**",
    githubOwners: ["@roldaobatista"],
    agentOwners: ["@product-governance", "@lgpd-security"],
  },
  {
    pattern: "packages/engine-uncertainty/**",
    githubOwners: ["@roldaobatista"],
    agentOwners: ["@product-governance", "@metrology-calc"],
  },
  {
    pattern: "packages/normative-rules/**",
    githubOwners: ["@roldaobatista"],
    agentOwners: ["@product-governance", "@regulator"],
  },
  {
    pattern: "packages/audit-log/**",
    githubOwners: ["@roldaobatista"],
    agentOwners: ["@product-governance", "@db-schema", "@lgpd-security"],
  },
  { pattern: "compliance/**", githubOwners: ["@roldaobatista"], agentOwners: ["@product-governance"] },
  { pattern: "PRD.md", githubOwners: ["@roldaobatista"], agentOwners: ["@product-governance"] },
];

const REQUIRED_PR_TEMPLATE_PHRASES = [
  "Governance checklist",
  "Matriz requisito->spec->teste->evidencia atualizada",
  "Pacote normativo impactado?",
  "Copy-lint verde",
  "Guardrails de multitenancy verdes",
  "RLS tests passam em >=2 tenants sinteticos",
  "Audit hash-chain integra",
  "Release notes regulatorias",
  "Cloud agents",
  "Pareceres dos 3 auditores externos",
  "metrology-auditor",
  "legal-counsel",
  "senior-reviewer",
  "Nenhum dos 3 auditores emitiu BLOQUEIO",
  "Este PR pode alterar comportamento de emissao?",
  "Este PR pode alterar o que e gravado no audit log?",
  "Este PR introduz ou altera claim comercial?",
  "Algum dos 5 casos-limite aplicavel?",
];

const REQUIRED_PRODUCT_GOVERNANCE_WRITE_PATHS = ["adr/**", "compliance/release-norm/**"];

function parseArgs(argv: string[]): CliOptions {
  let workspace = process.cwd();
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--workspace") {
      const value = argv[i + 1];
      if (!value) throw new Error("--workspace exige um caminho");
      workspace = value;
      i += 1;
      continue;
    }
    throw new Error(`argumento desconhecido: ${arg}`);
  }
  return { workspace: resolve(workspace) };
}

export function checkGovernanceGate(workspace: string): Finding[] {
  return [
    ...checkCodeowners(workspace),
    ...checkPullRequestTemplate(workspace),
    ...checkProductGovernanceAgent(workspace),
  ];
}

function checkCodeowners(workspace: string): Finding[] {
  const path = join(workspace, ".github", "CODEOWNERS");
  if (!existsSync(path)) {
    return [{ code: "GOV-001", path: displayPath(workspace, path), message: ".github/CODEOWNERS ausente" }];
  }

  const text = readFileSync(path, "utf8");
  const entries = parseCodeowners(text);
  const agentEntries = parseAgentOwnerMetadata(text);
  const findings: Finding[] = [];
  for (const required of REQUIRED_CODEOWNERS) {
    const owners = entries.get(required.pattern);
    const missingGithubOwners = required.githubOwners.filter((owner) => !owners?.includes(owner));
    if (missingGithubOwners.length > 0) {
      findings.push({
        code: "GOV-001",
        path: ".github/CODEOWNERS",
        message: `${required.pattern} deve exigir GitHub owner real ${missingGithubOwners.join(", ")}`,
      });
    }

    const agentOwners = agentEntries.get(required.pattern);
    const missingAgentOwners = required.agentOwners.filter((owner) => !agentOwners?.includes(owner));
    if (missingAgentOwners.length > 0) {
      findings.push({
        code: "GOV-001",
        path: ".github/CODEOWNERS",
        message: `${required.pattern} deve declarar agent-owners ${missingAgentOwners.join(", ")}`,
      });
    }
  }
  return findings;
}

function parseCodeowners(text: string): Map<string, string[]> {
  const entries = new Map<string, string[]>();
  for (const line of text.replace(/\r\n/g, "\n").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const [pattern, ...owners] = trimmed.split(/\s+/);
    if (pattern) entries.set(pattern, owners);
  }
  return entries;
}

function parseAgentOwnerMetadata(text: string): Map<string, string[]> {
  const entries = new Map<string, string[]>();
  for (const line of text.replace(/\r\n/g, "\n").split("\n")) {
    const match = line.trim().match(/^#\s*agent-owners\s+(\S+)\s+(.+)$/);
    if (!match) continue;
    const [, pattern, ownerList] = match;
    entries.set(pattern, ownerList.split(/\s+/).filter(Boolean));
  }
  return entries;
}

function checkPullRequestTemplate(workspace: string): Finding[] {
  const path = join(workspace, ".github", "pull_request_template.md");
  if (!existsSync(path)) {
    return [{ code: "GOV-002", path: displayPath(workspace, path), message: ".github/pull_request_template.md ausente" }];
  }

  const normalized = normalizeText(readFileSync(path, "utf8"));
  return REQUIRED_PR_TEMPLATE_PHRASES.filter((phrase) => !normalized.includes(normalizeText(phrase))).map((phrase) => ({
    code: "GOV-002" as const,
    path: ".github/pull_request_template.md",
    message: `template de PR sem item obrigatório: ${phrase}`,
  }));
}

function checkProductGovernanceAgent(workspace: string): Finding[] {
  const path = join(workspace, ".claude", "agents", "product-governance.md");
  if (!existsSync(path)) {
    return [{ code: "GOV-003", path: displayPath(workspace, path), message: "agente product-governance ausente" }];
  }

  const allowed = extractAllowedWritePaths(readFileSync(path, "utf8"));
  const findings: Finding[] = [];
  for (const required of REQUIRED_PRODUCT_GOVERNANCE_WRITE_PATHS) {
    if (!allowed.includes(required)) {
      findings.push({
        code: "GOV-003",
        path: ".claude/agents/product-governance.md",
        message: `product-governance deve poder escrever em ${required}`,
      });
    }
  }

  for (const pathPattern of allowed) {
    if (isForbiddenProductGovernanceWritePath(pathPattern)) {
      findings.push({
        code: "GOV-003",
        path: ".claude/agents/product-governance.md",
        message: `product-governance não pode escrever em ${pathPattern}`,
      });
    }
  }
  return findings;
}

function extractAllowedWritePaths(text: string): string[] {
  const normalized = text.replace(/\r\n/g, "\n");
  const section = normalized.match(/(?:^|\n)## Paths permitidos \(escrita\)\n+([\s\S]*?)(?=\n## |\n*$)/)?.[1] ?? "";
  return section
    .split("\n")
    .map((line) => line.match(/^\s*-\s+(.+?)\s*$/)?.[1])
    .filter((value): value is string => Boolean(value))
    .map((value) => value.replace(/`/g, "").trim());
}

function isForbiddenProductGovernanceWritePath(pathPattern: string): boolean {
  if (!pathPattern.includes("/") && !pathPattern.includes("*")) return false;
  if (pathPattern === "compliance/release-norm/**") return false;
  if (pathPattern.startsWith("apps/")) return true;
  if (pathPattern.startsWith("packages/")) return true;
  if (pathPattern.startsWith("infra/")) return true;
  if (pathPattern.startsWith("compliance/")) return true;
  return false;
}

function normalizeText(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/→/g, "->")
    .replace(/≥/g, ">=")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function displayPath(workspace: string, path: string): string {
  return relative(workspace, path).replace(/\\/g, "/");
}

function main(): void {
  try {
    const { workspace } = parseArgs(process.argv.slice(2));
    const findings = checkGovernanceGate(workspace);
    for (const finding of findings) {
      console.log(`${finding.code} ${finding.path}: ${finding.message}`);
    }
    if (findings.length > 0) {
      console.log(`governance-gate: ${findings.length} finding(s)`);
      process.exit(1);
    }
    console.log("governance-gate: ok");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`governance-gate: ${message}`);
    process.exit(2);
  }
}

main();
