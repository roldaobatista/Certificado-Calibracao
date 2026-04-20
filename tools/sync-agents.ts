#!/usr/bin/env node
// tools/sync-agents.ts — gera .codex/agents/*.toml a partir de .claude/agents/*.md.
//
// Uso:
//   pnpm exec tsx tools/sync-agents.ts
//   pnpm exec tsx tools/sync-agents.ts --check
//   pnpm exec tsx tools/sync-agents.ts --workspace /path/to/repo

import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, relative, sep } from "node:path";

interface CliOptions {
  check: boolean;
  workspace: string;
}

interface ClaudeAgent {
  name: string;
  description: string;
  mandate: string;
  allowedWritePaths: string[];
}

interface PlannedFile {
  path: string;
  content: string;
}

function parseArgs(argv: string[]): CliOptions {
  let workspace = process.cwd();
  let check = false;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--check") {
      check = true;
      continue;
    }
    if (arg === "--workspace") {
      const value = argv[i + 1];
      if (!value) throw new Error("--workspace exige um caminho");
      workspace = value;
      i += 1;
      continue;
    }
    throw new Error(`argumento desconhecido: ${arg}`);
  }

  return { check, workspace };
}

function parseClaudeAgent(filePath: string): ClaudeAgent {
  const text = readFileSync(filePath, "utf8").replace(/\r\n/g, "\n");
  const frontmatter = text.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!frontmatter?.[1]) {
    throw new Error(`${filePath}: frontmatter YAML ausente`);
  }

  const fields: Record<string, string> = {};
  for (const line of frontmatter[1].split("\n")) {
    const match = line.match(/^([a-zA-Z_]+):\s*(.+)$/);
    if (match?.[1] && match[2]) fields[match[1]] = match[2].trim();
  }

  if (!fields.name) throw new Error(`${filePath}: campo name ausente`);
  if (!fields.description) throw new Error(`${filePath}: campo description ausente`);

  return {
    name: fields.name,
    description: fields.description,
    mandate: extractSection(text, "Mandato"),
    allowedWritePaths: extractBullets(extractSection(text, "Paths permitidos \\(escrita\\)")),
  };
}

function extractSection(text: string, heading: string): string {
  const match = text.match(new RegExp(`(?:^|\\n)## ${heading}\\n+([\\s\\S]*?)(?=\\n## |\\n*$)`));
  return match?.[1]?.trim() ?? "";
}

function extractBullets(section: string): string[] {
  return section
    .split("\n")
    .map((line) => line.match(/^\s*-\s+(.+?)\s*$/)?.[1])
    .filter((value): value is string => Boolean(value));
}

function generateCodexToml(agent: ClaudeAgent): string {
  const allowedPaths = agent.allowedWritePaths.length ? agent.allowedWritePaths.join(", ") : "nenhum path de escrita declarado";
  const instructions = [
    `Você é o agente '${agent.name}' do Aferê (plataforma metrológica ISO/IEC 17025).`,
    "",
    `Paths permitidos (escrita): ${allowedPaths}`,
    "",
    "Mandato:",
    agent.mandate || "Mandato não declarado no agente Claude.",
    "",
    "Contexto canônico: AGENTS.md na raiz. Detalhamento do papel em .claude/agents/" +
      `${agent.name}.md. Ownership duro em harness/02-arquitetura.md. ` +
      "Auditores (metrology-auditor, legal-counsel, senior-reviewer) NUNCA editam o artefato que auditam.",
  ].join("\n");

  return [
    `# .codex/agents/${agent.name}.toml`,
    `# Gerado por tools/sync-agents.ts a partir de .claude/agents/${agent.name}.md.`,
    "# Não editar manualmente; edite o agente Claude e rode pnpm sync:agents.",
    "# Ownership (paths permitidos/bloqueados) está em .claude/agents/*.md.",
    "",
    `name = ${tomlString(agent.name)}`,
    `description = ${tomlString(agent.description)}`,
    `developer_instructions = ${tomlMultilineString(instructions)}`,
    "",
  ].join("\n");
}

function tomlString(value: string): string {
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function tomlMultilineString(value: string): string {
  return `"""\n${value.replace(/\\/g, "\\\\").replace(/"""/g, '\\"\\"\\"')}\n"""`;
}

function toDisplayPath(workspace: string, path: string): string {
  return relative(workspace, path).split(sep).join("/");
}

function buildPlan(workspace: string): { expected: PlannedFile[]; extraCodexFiles: string[] } {
  const claudeDir = join(workspace, ".claude", "agents");
  const codexDir = join(workspace, ".codex", "agents");
  if (!existsSync(claudeDir)) throw new Error(`diretório ausente: ${toDisplayPath(workspace, claudeDir)}`);

  const claudeFiles = readdirSync(claudeDir)
    .filter((file) => file.endsWith(".md"))
    .sort((a, b) => a.localeCompare(b));

  const expected = claudeFiles.map((file) => {
    const agent = parseClaudeAgent(join(claudeDir, file));
    return {
      path: join(codexDir, `${agent.name}.toml`),
      content: generateCodexToml(agent),
    };
  });

  const expectedPaths = new Set(expected.map((file) => file.path));
  const extraCodexFiles = existsSync(codexDir)
    ? readdirSync(codexDir)
        .filter((file) => file.endsWith(".toml"))
        .map((file) => join(codexDir, file))
        .filter((path) => !expectedPaths.has(path))
    : [];

  return { expected, extraCodexFiles };
}

function main(): void {
  try {
    const options = parseArgs(process.argv.slice(2));
    const { expected, extraCodexFiles } = buildPlan(options.workspace);
    const stale = expected.filter((file) => !existsSync(file.path) || readFileSync(file.path, "utf8") !== file.content);

    if (options.check) {
      for (const file of stale) console.log(`desatualizado: ${toDisplayPath(options.workspace, file.path)}`);
      for (const file of extraCodexFiles) console.log(`órfão: ${toDisplayPath(options.workspace, file)}`);
      if (stale.length || extraCodexFiles.length) {
        console.error("sync-agents: rode `pnpm sync:agents` para regenerar os espelhos Codex.");
        process.exit(1);
      }
      console.log(`sync-agents: ${expected.length} agente(s) sincronizados.`);
      return;
    }

    const codexDir = join(options.workspace, ".codex", "agents");
    mkdirSync(codexDir, { recursive: true });
    for (const file of stale) {
      writeFileSync(file.path, file.content);
      console.log(`gerado: ${toDisplayPath(options.workspace, file.path)}`);
    }
    for (const file of extraCodexFiles) {
      rmSync(file);
      console.log(`removido: ${toDisplayPath(options.workspace, file)}`);
    }
    if (!stale.length && !extraCodexFiles.length) {
      console.log(`sync-agents: ${expected.length} agente(s) já estavam sincronizados.`);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`sync-agents: ${message}`);
    process.exit(1);
  }
}

main();
