#!/usr/bin/env node
import { relative } from "node:path";
import { lintTenantSql, type Finding, type LintResult } from "./lint.js";

interface CliArgs {
  cwd: string;
  paths: string[];
  json: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { cwd: process.cwd(), paths: [], json: false, help: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") args.json = true;
    else if (arg === "-h" || arg === "--help") args.help = true;
    else if (arg === "--cwd") {
      const value = argv[i + 1];
      if (!value) throw new Error("--cwd exige um caminho");
      args.cwd = value;
      i += 1;
    } else if (!arg.startsWith("-")) {
      args.paths.push(arg);
    } else {
      throw new Error(`argumento desconhecido: ${arg}`);
    }
  }
  return args;
}

function printHelp(): void {
  console.log(`tenant-lint — Gate 1 tenant-safe SQL (harness/05-guardrails.md)

Uso:
  tenant-lint [paths...] [--json] [--cwd <repo>]

Sem paths: varre packages/db e apps/api/src.
Com paths: limita a varredura aos arquivos/diretórios passados.

Saída:
  exit 0 → nenhuma query/policy multitenant sem organization_id
  exit 1 → pelo menos uma violação TENANT-LINT
  exit 2 → erro interno`);
}

function formatHuman(finding: Finding, cwd: string): string {
  const rel = relative(cwd, finding.file);
  const head = `${rel}:${finding.line}:${finding.column}  ERROR  ${finding.ruleId}  ${finding.message}`;
  const table = `    tabela: ${finding.table}`;
  const snippet = `    trecho: ${finding.snippet}`;
  return [head, table, snippet].join("\n");
}

function summarize(result: LintResult): string {
  return `${result.filesScanned} arquivos varridos | errors: ${result.errors}`;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    process.exit(0);
  }

  const result = await lintTenantSql({ cwd: args.cwd, paths: args.paths });
  if (args.json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    for (const finding of result.findings) console.log(formatHuman(finding, args.cwd));
    console.log("");
    console.log(summarize(result));
  }
  process.exit(result.errors > 0 ? 1 : 0);
}

main().catch((error) => {
  console.error("tenant-lint: erro interno", error);
  process.exit(2);
});
