import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import fg from "fast-glob";
import { loadRules, type OwnershipRule, type Severity } from "./rules.js";

export interface Finding {
  file: string;
  line: number;
  column: number;
  ruleId: string;
  severity: Severity;
  importSpecifier: string;
  forbidden: string;
  reason: string;
  suggestion: string;
  snippet: string;
}

export interface LintResult {
  findings: Finding[];
  errors: number;
  warnings: number;
  infos: number;
  filesScanned: number;
}

export interface LintOptions {
  rulesPath?: string;
  cwd?: string;
  paths?: string[];
}

export async function lintOwnership(options: LintOptions = {}): Promise<LintResult> {
  const { rulesPath, paths } = options;
  const cwd = options.cwd ?? findWorkspaceRoot(process.cwd()) ?? process.cwd();
  const rules = loadRules(rulesPath);
  const findings: Finding[] = [];
  let filesScanned = 0;

  for (const rule of rules.rules) {
    const scope = paths && paths.length > 0 ? paths : rule.scope;
    const files = await fg(scope, {
      cwd,
      ignore: rules.coverage.exclude,
      absolute: true,
      dot: false,
      onlyFiles: true,
    });
    filesScanned += files.length;
    for (const file of files) {
      const content = safeRead(file);
      if (content === null) continue;
      findings.push(...scanFile(file, content, rule));
    }
  }

  return summarize(findings, filesScanned);
}

function summarize(findings: Finding[], filesScanned: number): LintResult {
  return {
    findings,
    errors: findings.filter((f) => f.severity === "error").length,
    warnings: findings.filter((f) => f.severity === "warning").length,
    infos: findings.filter((f) => f.severity === "info").length,
    filesScanned,
  };
}

export function findWorkspaceRoot(start: string): string | null {
  let dir = resolve(start);
  for (let i = 0; i < 10; i += 1) {
    if (existsSync(resolve(dir, "pnpm-workspace.yaml"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
  return null;
}

function safeRead(path: string): string | null {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

const IMPORT_PATTERNS = [
  // import ... from "..."
  /import\s+(?:type\s+)?(?:[^'"()]+?\s+from\s+)?['"]([^'"]+)['"]/g,
  // import "..."
  /import\s+['"]([^'"]+)['"]/g,
  // require("...")
  /require\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
  // dynamic import("...")
  /import\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
  // Kotlin/Java import
  /^\s*import\s+([a-zA-Z0-9_.]+)(?:\s*;)?\s*$/gm,
];

function scanFile(file: string, content: string, rule: OwnershipRule): Finding[] {
  const findings: Finding[] = [];
  const lines = content.split(/\r?\n/);

  for (const pattern of IMPORT_PATTERNS) {
    const regex = new RegExp(pattern.source, pattern.flags);
    let match: RegExpExecArray | null;
    while ((match = regex.exec(content)) !== null) {
      const specifier = match[1];
      if (specifier === undefined) continue;
      const hit = rule.forbidden_imports.find((f) => matchImport(specifier, f));
      if (!hit) continue;

      const { line, column } = offsetToLineCol(content, match.index);
      findings.push({
        file,
        line,
        column,
        ruleId: rule.id,
        severity: rule.severity,
        importSpecifier: specifier,
        forbidden: hit,
        reason: rule.reason,
        suggestion: rule.suggestion,
        snippet: lines[line - 1] ?? "",
      });
    }
  }
  return findings;
}

/**
 * Compara import specifier com forbidden.
 * - Match exato (import "@afere/foo" contra "@afere/foo").
 * - Prefixo com "/" (import "@afere/foo/bar" contra "@afere/foo").
 * - Substring para paths relativos (import "../../packages/foo/src" contra "packages/foo").
 */
function matchImport(specifier: string, forbidden: string): boolean {
  if (specifier === forbidden) return true;
  if (specifier.startsWith(`${forbidden}/`)) return true;
  if (specifier.includes(forbidden)) return true;
  return false;
}

function offsetToLineCol(content: string, offset: number): { line: number; column: number } {
  let line = 1;
  let col = 1;
  for (let i = 0; i < offset; i += 1) {
    if (content[i] === "\n") {
      line += 1;
      col = 1;
    } else {
      col += 1;
    }
  }
  return { line, column: col };
}
