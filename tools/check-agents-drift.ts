#!/usr/bin/env node
// tools/check-agents-drift.ts — detecta drift entre .claude/agents/*.md e .codex/agents/*.toml.
//
// Compara, por nome de agente: name, description, paths.allowed_write.
// Falha (exit 1) se encontrar divergência. Reporta em formato legível + JSON opcional.
//
// Uso:
//   pnpm exec tsx tools/check-agents-drift.ts
//   pnpm exec tsx tools/check-agents-drift.ts --json
//
// Geração automática a partir de spec canônica fica para sessão futura
// (tools/sync-agents.ts). Este script só detecta — não corrige.

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

interface AgentFields {
  name: string;
  description: string;
  allowedWrite: string[];
  source: "claude" | "codex";
}

const WORKSPACE = process.cwd();
const CLAUDE_DIR = join(WORKSPACE, ".claude/agents");
const CODEX_DIR = join(WORKSPACE, ".codex/agents");

function parseClaudeMd(path: string): AgentFields | null {
  const text = readFileSync(path, "utf8");
  const fmMatch = text.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch || fmMatch[1] === undefined) return null;
  const frontmatter: Record<string, string> = {};
  for (const line of fmMatch[1].split("\n")) {
    const m = line.match(/^([a-zA-Z_]+):\s*(.+)$/);
    if (m) frontmatter[m[1]!] = m[2]!.trim();
  }
  const allowedWrite: string[] = [];
  const allowedSection = text.match(/##\s*Paths permitidos \(escrita\)\s*\n([\s\S]*?)(?=\n##|\Z)/);
  if (allowedSection && allowedSection[1] !== undefined) {
    for (const line of allowedSection[1].split("\n")) {
      const m = line.match(/^-\s*`([^`]+)`/);
      if (m && m[1]) allowedWrite.push(m[1]);
    }
  }
  return {
    name: frontmatter.name ?? "",
    description: frontmatter.description ?? "",
    allowedWrite,
    source: "claude",
  };
}

function parseCodexToml(path: string): AgentFields | null {
  const text = readFileSync(path, "utf8");
  const name = getTomlString(text, "name") ?? "";
  const description = getTomlString(text, "description") ?? "";
  const allowedWrite = getTomlStringArray(text, "allowed_write") ?? [];
  return { name, description, allowedWrite, source: "codex" };
}

function getTomlString(text: string, key: string): string | null {
  const re = new RegExp(`^${key}\\s*=\\s*"((?:[^"\\\\]|\\\\.)*)"`, "m");
  const m = text.match(re);
  if (!m || m[1] === undefined) return null;
  return m[1].replace(/\\"/g, '"');
}

function getTomlStringArray(text: string, key: string): string[] | null {
  const re = new RegExp(`^${key}\\s*=\\s*\\[([\\s\\S]*?)\\]`, "m");
  const m = text.match(re);
  if (!m || m[1] === undefined) return null;
  const items: string[] = [];
  const itemRe = /"((?:[^"\\]|\\.)*)"/g;
  let sub: RegExpExecArray | null;
  while ((sub = itemRe.exec(m[1])) !== null) {
    if (sub[1] !== undefined) items.push(sub[1]);
  }
  return items;
}

interface Drift {
  agent: string;
  field: string;
  claude: unknown;
  codex: unknown;
}

function diff(a: AgentFields, b: AgentFields): Drift[] {
  const drifts: Drift[] = [];
  if (a.name !== b.name) drifts.push({ agent: a.name || b.name, field: "name", claude: a.name, codex: b.name });
  if (a.description !== b.description) {
    drifts.push({ agent: a.name, field: "description", claude: a.description, codex: b.description });
  }
  const sortedA = [...a.allowedWrite].sort();
  const sortedB = [...b.allowedWrite].sort();
  if (JSON.stringify(sortedA) !== JSON.stringify(sortedB)) {
    drifts.push({ agent: a.name, field: "allowed_write", claude: sortedA, codex: sortedB });
  }
  return drifts;
}

function main(): void {
  const claudeFiles = readdirSync(CLAUDE_DIR).filter((f) => f.endsWith(".md"));
  const codexFiles = readdirSync(CODEX_DIR).filter((f) => f.endsWith(".toml"));
  const claudeAgents = new Map<string, AgentFields>();
  const codexAgents = new Map<string, AgentFields>();

  for (const f of claudeFiles) {
    const parsed = parseClaudeMd(join(CLAUDE_DIR, f));
    if (parsed && parsed.name) claudeAgents.set(parsed.name, parsed);
  }
  for (const f of codexFiles) {
    const parsed = parseCodexToml(join(CODEX_DIR, f));
    if (parsed && parsed.name) codexAgents.set(parsed.name, parsed);
  }

  const allNames = new Set<string>([...claudeAgents.keys(), ...codexAgents.keys()]);
  const drifts: Drift[] = [];
  const missingInClaude: string[] = [];
  const missingInCodex: string[] = [];

  for (const name of allNames) {
    const a = claudeAgents.get(name);
    const b = codexAgents.get(name);
    if (!a) missingInClaude.push(name);
    else if (!b) missingInCodex.push(name);
    else drifts.push(...diff(a, b));
  }

  const json = process.argv.includes("--json");
  const summary = {
    claudeCount: claudeAgents.size,
    codexCount: codexAgents.size,
    missingInClaude,
    missingInCodex,
    drifts,
  };

  if (json) {
    process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
  } else {
    console.log(`Claude agents: ${summary.claudeCount} | Codex agents: ${summary.codexCount}`);
    if (missingInClaude.length) console.log(`\n✗ faltando em .claude/agents: ${missingInClaude.join(", ")}`);
    if (missingInCodex.length) console.log(`\n✗ faltando em .codex/agents: ${missingInCodex.join(", ")}`);
    if (drifts.length) {
      console.log(`\n✗ ${drifts.length} divergência(s):`);
      for (const d of drifts) {
        console.log(`  - ${d.agent} / ${d.field}`);
        console.log(`      claude: ${JSON.stringify(d.claude)}`);
        console.log(`      codex:  ${JSON.stringify(d.codex)}`);
      }
    }
    if (!missingInClaude.length && !missingInCodex.length && !drifts.length) {
      console.log("\n✓ sem drift — .claude/agents e .codex/agents sincronizados");
    }
  }

  const fail = drifts.length > 0 || missingInClaude.length > 0 || missingInCodex.length > 0;
  process.exit(fail ? 1 : 0);
}

main();
