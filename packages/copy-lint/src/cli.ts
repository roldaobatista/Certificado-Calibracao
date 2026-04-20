#!/usr/bin/env node
import { relative } from "node:path";
import { lintFiles, type Finding, type LintResult } from "./lint.js";

interface CliArgs {
  paths: string[];
  json: boolean;
  failOnWarning: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { paths: [], json: false, failOnWarning: false, help: false };
  for (const arg of argv) {
    if (arg === "--json") args.json = true;
    else if (arg === "--fail-on-warning") args.failOnWarning = true;
    else if (arg === "-h" || arg === "--help") args.help = true;
    else if (!arg.startsWith("-")) args.paths.push(arg);
  }
  return args;
}

function printHelp(): void {
  console.log(`copy-lint — lint de claims regulatórios Aferê

Uso:
  copy-lint [paths...] [--json] [--fail-on-warning]

Sem paths: varre cobertura padrão de packages/copy-lint/src/rules.yaml.
Com paths: limita a varredura aos arquivos/globs passados.

Saída:
  exit 0  → sem errors (warnings podem existir se --fail-on-warning ausente)
  exit 1  → erros detectados (ou warnings com --fail-on-warning)
  exit 2  → erro interno`);
}

function formatHuman(finding: Finding, cwd: string): string {
  const rel = relative(cwd, finding.file);
  const sev = finding.severity.toUpperCase().padEnd(7);
  const head = `${rel}:${finding.line}:${finding.column}  ${sev}  ${finding.ruleId}  ${finding.reason}`;
  const hit = `    match: "${finding.match}"`;
  const sug = `    sugestão: ${finding.suggestion}`;
  return [head, hit, sug].join("\n");
}

function summarize(result: LintResult): string {
  return `${result.filesScanned} arquivos varridos | errors: ${result.errors} | warnings: ${result.warnings} | infos: ${result.infos}`;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    process.exit(0);
  }
  const cwd = process.cwd();
  const result = await lintFiles({ paths: args.paths });

  if (args.json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    for (const f of result.findings) console.log(formatHuman(f, cwd));
    console.log("");
    console.log(summarize(result));
  }

  const failExit = result.errors > 0 || (args.failOnWarning && result.warnings > 0);
  process.exit(failExit ? 1 : 0);
}

main().catch((err) => {
  console.error("copy-lint: erro interno", err);
  process.exit(2);
});
