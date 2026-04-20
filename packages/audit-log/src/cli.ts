#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { verifyAuditHashChain, type AuditChainEntry } from "./verify.js";

interface CliArgs {
  file?: string;
  json: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { json: false, help: false };
  for (const arg of argv) {
    if (arg === "--json") args.json = true;
    else if (arg === "-h" || arg === "--help") args.help = true;
    else if (!arg.startsWith("-") && !args.file) args.file = arg;
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  return args;
}

function printHelp(): void {
  console.log(`audit-chain-verify — Gate 3 audit hash-chain verifier

Uso:
  audit-chain-verify <audit.jsonl> [--json]

Cada linha deve ser um JSON com: id, prevHash, payload, hash.

Saída:
  exit 0 → cadeia íntegra
  exit 1 → primeira divergência encontrada
  exit 2 → erro interno ou uso inválido`);
}

function readJsonl(path: string): AuditChainEntry[] {
  return readFileSync(path, "utf8")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as AuditChainEntry);
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    process.exit(0);
  }
  if (!args.file) throw new Error("arquivo JSONL obrigatório");

  const entries = readJsonl(args.file);
  const result = verifyAuditHashChain(entries);

  if (args.json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else if (result.ok) {
    console.log(`${result.checked} registros verificados — hash-chain íntegra`);
  } else {
    const invalid = result.firstInvalid;
    console.log(
      `hash-chain divergente em ${invalid?.id ?? "registro desconhecido"} ` +
        `(index ${invalid?.index ?? "?"}): ${invalid?.reason ?? "unknown"}`,
    );
  }

  process.exit(result.ok ? 0 : 1);
}

try {
  main();
} catch (error) {
  console.error("audit-chain-verify: erro interno", error);
  process.exit(2);
}
