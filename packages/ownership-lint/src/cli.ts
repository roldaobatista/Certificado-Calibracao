#!/usr/bin/env node
import { relative } from "node:path";
import { lintOwnership, type Finding, type LintResult } from "./lint.js";

interface CliArgs {
  paths: string[];
  json: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { paths: [], json: false, help: false };
  for (const arg of argv) {
    if (arg === "--json") args.json = true;
    else if (arg === "-h" || arg === "--help") args.help = true;
    else if (!arg.startsWith("-")) args.paths.push(arg);
  }
  return args;
}

function printHelp(): void {
  console.log(`ownership-lint — Gate 6 de ownership (harness/05-guardrails.md)

Uso:
  ownership-lint [paths...] [--json]

Sem paths: usa scope declarado em cada regra de rules.yaml.
Com paths: limita varredura aos globs passados.

Detecta imports proibidos cruzando boundaries de ownership:
- apps/web, apps/portal não importam @afere/normative-rules, @afere/engine-uncertainty, @afere/db.
- apps/android não importa @afere/normative-rules, @afere/engine-uncertainty.

Saída:
  exit 0 → sem violação
  exit 1 → pelo menos uma violação de error
  exit 2 → erro interno`);
}

function formatHuman(finding: Finding, cwd: string): string {
  const rel = relative(cwd, finding.file);
  const sev = finding.severity.toUpperCase().padEnd(7);
  const head = `${rel}:${finding.line}:${finding.column}  ${sev}  ${finding.ruleId}  ${finding.reason}`;
  const hit = `    import: "${finding.importSpecifier}"  proibido: "${finding.forbidden}"`;
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
  const result = await lintOwnership({ paths: args.paths });

  if (args.json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    for (const f of result.findings) console.log(formatHuman(f, cwd));
    console.log("");
    console.log(summarize(result));
  }

  process.exit(result.errors > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error("ownership-lint: erro interno", err);
  process.exit(2);
});
