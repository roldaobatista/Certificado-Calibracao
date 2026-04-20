import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import fg from "fast-glob";
import { loadRules, type CompiledRule, type Coverage, type Severity } from "./rules.js";

export interface Finding {
  file: string;
  line: number;
  column: number;
  ruleId: string;
  severity: Severity;
  match: string;
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
  paths?: string[];
  rulesPath?: string;
  cwd?: string;
}

export async function lintFiles(options: LintOptions = {}): Promise<LintResult> {
  const { paths, rulesPath } = options;
  const cwd = options.cwd ?? findWorkspaceRoot(process.cwd()) ?? process.cwd();
  const rules = loadRules(rulesPath);
  const files = await resolveFiles(paths, rules.coverage, cwd);
  const findings: Finding[] = [];

  for (const file of files) {
    const content = safeRead(file);
    if (content === null) continue;
    findings.push(...scanContent(file, content, rules.compiled));
  }

  return summarize(findings, files.length);
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

async function resolveFiles(paths: string[] | undefined, coverage: Coverage, cwd: string): Promise<string[]> {
  const patterns = paths && paths.length > 0 ? paths : coverage.include;
  return fg(patterns, {
    cwd,
    ignore: coverage.exclude,
    absolute: true,
    dot: false,
    onlyFiles: true,
  });
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

function scanContent(file: string, content: string, rules: CompiledRule[]): Finding[] {
  const findings: Finding[] = [];
  const lines = content.split(/\r?\n/);

  for (const rule of rules) {
    // clona regex para não compartilhar lastIndex entre arquivos
    const regex = new RegExp(rule.regex.source, rule.regex.flags);
    let match: RegExpExecArray | null;
    while ((match = regex.exec(content)) !== null) {
      const { line, column } = offsetToLineCol(content, match.index);
      const snippet = lines[line - 1] ?? "";
      findings.push({
        file,
        line,
        column,
        ruleId: rule.id,
        severity: rule.severity,
        match: match[0],
        reason: rule.reason,
        suggestion: rule.suggestion,
        snippet,
      });
      // avança para evitar loop em zero-length matches
      if (match.index === regex.lastIndex) regex.lastIndex += 1;
    }
  }
  return findings;
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
