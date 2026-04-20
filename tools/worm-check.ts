#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, resolve, relative, sep } from "node:path";
import { pathToFileURL } from "node:url";

export interface WormFinding {
  file: string;
  line: number;
  column: number;
  ruleId: "WORM-001" | "WORM-002" | "WORM-003";
  resource: string;
  message: string;
}

export interface WormScanResult {
  findings: WormFinding[];
  errors: number;
  filesScanned: number;
}

export interface WormScanOptions {
  cwd?: string;
  paths?: string[];
}

const DEFAULT_PATHS = ["infra"];
const REGULATORY_NAME = /(cert|certificate|certificado|audit|checkpoint|evidence|compliance|worm)/i;

export async function scanWormStorage(options: WormScanOptions = {}): Promise<WormScanResult> {
  const cwd = options.cwd ?? findWorkspaceRoot(process.cwd()) ?? process.cwd();
  const files = resolveFiles(cwd, options.paths);
  const findings = files.flatMap((file) => scanTerraformFile(file));
  return { findings, errors: findings.length, filesScanned: files.length };
}

function resolveFiles(cwd: string, paths: string[] | undefined): string[] {
  const entries = paths && paths.length > 0 ? paths : DEFAULT_PATHS;
  const files: string[] = [];
  for (const entry of entries) {
    const absolute = resolve(cwd, entry);
    if (!existsSync(absolute)) continue;
    const stat = statSync(absolute);
    if (stat.isDirectory()) files.push(...walk(absolute));
    else if (absolute.endsWith(".tf")) files.push(absolute);
  }
  return [...new Set(files)].sort((a, b) => a.localeCompare(b));
}

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === ".terraform" || entry.name === "node_modules") continue;
    const path = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(path));
    else if (entry.isFile() && path.endsWith(".tf")) out.push(path);
  }
  return out;
}

function scanTerraformFile(file: string): WormFinding[] {
  const content = readFileSync(file, "utf8");
  const findings: WormFinding[] = [];
  const resourceRegex = /resource\s+"([^"]+)"\s+"([^"]+)"\s*\{/g;
  let match: RegExpExecArray | null;
  while ((match = resourceRegex.exec(content)) !== null) {
    const type = match[1] ?? "";
    const name = match[2] ?? "";
    const bodyStart = resourceRegex.lastIndex;
    const bodyEnd = findMatchingBrace(content, bodyStart - 1);
    if (bodyEnd === -1) continue;
    const block = content.slice(match.index, bodyEnd + 1);
    const resource = `${type}.${name}`;
    if (!isRegulatoryBucket(resource, block)) continue;

    if (type === "aws_s3_bucket" && !/\bobject_lock_enabled\s*=\s*true\b/i.test(block)) {
      findings.push(makeFinding(file, content, match.index, "WORM-001", resource, "S3 regulatório sem object_lock_enabled = true"));
    }
    if (type === "b2_bucket" && !/\bfile_lock_enabled\s*=\s*true\b/i.test(block)) {
      findings.push(makeFinding(file, content, match.index, "WORM-002", resource, "B2 regulatório sem file_lock_enabled = true"));
    }
    if (
      type === "google_storage_bucket" &&
      !/\bretention_policy\s*\{[\s\S]*?\bis_locked\s*=\s*true\b/i.test(block)
    ) {
      findings.push(makeFinding(file, content, match.index, "WORM-003", resource, "GCS regulatório sem retention_policy.is_locked = true"));
    }
  }
  return findings;
}

function isRegulatoryBucket(resource: string, block: string): boolean {
  return REGULATORY_NAME.test(resource) || REGULATORY_NAME.test(block);
}

function findMatchingBrace(content: string, openBraceIndex: number): number {
  let depth = 0;
  for (let i = openBraceIndex; i < content.length; i += 1) {
    if (content[i] === "{") depth += 1;
    if (content[i] === "}") {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function makeFinding(
  file: string,
  content: string,
  offset: number,
  ruleId: WormFinding["ruleId"],
  resource: string,
  message: string,
): WormFinding {
  const { line, column } = offsetToLineCol(content, offset);
  return { file, line, column, ruleId, resource, message };
}

function offsetToLineCol(content: string, offset: number): { line: number; column: number } {
  let line = 1;
  let column = 1;
  for (let i = 0; i < offset; i += 1) {
    if (content[i] === "\n") {
      line += 1;
      column = 1;
    } else {
      column += 1;
    }
  }
  return { line, column };
}

function findWorkspaceRoot(start: string): string | null {
  let dir = resolve(start);
  for (let i = 0; i < 10; i += 1) {
    if (existsSync(resolve(dir, "pnpm-workspace.yaml"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
  return null;
}

function toDisplayPath(cwd: string, file: string): string {
  return relative(cwd, file).split(sep).join("/");
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const json = args.includes("--json");
  const paths = args.filter((arg) => arg !== "--json");
  const cwd = process.cwd();
  const result = await scanWormStorage({ cwd, paths });

  if (json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    for (const finding of result.findings) {
      console.log(
        `${toDisplayPath(cwd, finding.file)}:${finding.line}:${finding.column}  ERROR  ${finding.ruleId}  ${finding.message}`,
      );
      console.log(`    resource: ${finding.resource}`);
    }
    console.log("");
    console.log(`${result.filesScanned} arquivos varridos | errors: ${result.errors}`);
  }

  process.exit(result.errors > 0 ? 1 : 0);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main().catch((error) => {
    console.error("worm-check: erro interno", error);
    process.exit(2);
  });
}
