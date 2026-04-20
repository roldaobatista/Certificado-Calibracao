import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, extname, resolve } from "node:path";

export interface Finding {
  file: string;
  line: number;
  column: number;
  ruleId: string;
  severity: "error";
  table: string;
  message: string;
  snippet: string;
}

export interface LintResult {
  findings: Finding[];
  errors: number;
  filesScanned: number;
}

export interface LintOptions {
  cwd?: string;
  paths?: string[];
}

const DEFAULT_PATHS = ["packages/db", "apps/api/src"];
const SCANNED_EXTENSIONS = new Set([".sql", ".ts", ".tsx", ".mts", ".cts", ".prisma"]);
const SINGLE_TENANT_TABLES = new Set(["_prisma_migrations", "health_check", "organizations", "organization"]);

export async function lintTenantSql(options: LintOptions = {}): Promise<LintResult> {
  const cwd = options.cwd ?? findWorkspaceRoot(process.cwd()) ?? process.cwd();
  const files = resolveFiles(cwd, options.paths);
  const findings: Finding[] = [];

  for (const file of files) {
    const content = safeRead(file);
    if (content === null) continue;
    findings.push(...scanFile(file, content));
  }

  return {
    findings,
    errors: findings.length,
    filesScanned: files.length,
  };
}

function resolveFiles(cwd: string, paths: string[] | undefined): string[] {
  const entries = paths && paths.length > 0 ? paths : DEFAULT_PATHS;
  const files: string[] = [];

  for (const entry of entries) {
    const absolute = resolve(cwd, entry);
    if (!existsSync(absolute)) continue;
    const stat = statSync(absolute);
    if (stat.isDirectory()) {
      files.push(...walk(absolute));
    } else if (isScannable(absolute)) {
      files.push(absolute);
    }
  }

  return [...new Set(files)].sort((a, b) => a.localeCompare(b));
}

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist" || entry.name === ".turbo") continue;
    if (entry.name === "tenant-lint") continue;
    const path = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(path));
    else if (entry.isFile() && isScannable(path, false)) out.push(path);
  }
  return out;
}

function isScannable(file: string): boolean {
  if (/\.test\.[cm]?tsx?$/i.test(file)) return false;
  return SCANNED_EXTENSIONS.has(extname(file));
}

function safeRead(file: string): string | null {
  try {
    return readFileSync(file, "utf8");
  } catch {
    return null;
  }
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

function scanFile(file: string, content: string): Finding[] {
  const normalized = content.replace(/\r\n/g, "\n");
  return [...scanPolicies(file, normalized), ...scanCrud(file, normalized)];
}

function scanPolicies(file: string, content: string): Finding[] {
  const findings: Finding[] = [];
  const regex = /\bcreate\s+policy\b[\s\S]*?\bon\s+("?[a-zA-Z_][\w.]*"?)[\s\S]*?(?=;|$)/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(content)) !== null) {
    const table = normalizeTable(match[1] ?? "");
    const statement = match[0];
    if (!table || isSingleTenant(table) || hasTenantScope(statement)) continue;
    findings.push(makeFinding(file, content, match.index, "TENANT-SQL-002", table, statement));
  }
  return findings;
}

function scanCrud(file: string, content: string): Finding[] {
  const findings: Finding[] = [];
  const patterns = [
    /\bselect\b[\s\S]*?\bfrom\s+("?[a-zA-Z_][\w.]*"?)[\s\S]*?(?=;|`|$)/gi,
    /\bupdate\s+("?[a-zA-Z_][\w.]*"?)[\s\S]*?(?=;|`|$)/gi,
    /\bdelete\s+from\s+("?[a-zA-Z_][\w.]*"?)[\s\S]*?(?=;|`|$)/gi,
  ];

  for (const pattern of patterns) {
    const regex = new RegExp(pattern.source, pattern.flags);
    let match: RegExpExecArray | null;
    while ((match = regex.exec(content)) !== null) {
      const table = normalizeTable(match[1] ?? "");
      const statement = match[0];
      if (!table || isSingleTenant(table) || hasTenantScope(statement)) continue;
      findings.push(makeFinding(file, content, match.index, "TENANT-SQL-001", table, statement));
    }
  }

  const insertRegex = /\binsert\s+into\s+("?[a-zA-Z_][\w.]*"?)\s*\(([\s\S]*?)\)[\s\S]*?(?=;|`|$)/gi;
  let insertMatch: RegExpExecArray | null;
  while ((insertMatch = insertRegex.exec(content)) !== null) {
    const table = normalizeTable(insertMatch[1] ?? "");
    const columns = insertMatch[2] ?? "";
    const statement = insertMatch[0];
    if (!table || isSingleTenant(table) || hasTenantScope(columns) || hasTenantScope(statement)) continue;
    findings.push(makeFinding(file, content, insertMatch.index, "TENANT-SQL-001", table, statement));
  }

  return dedupeFindings(findings);
}

function normalizeTable(raw: string): string {
  const cleaned = raw.replace(/"/g, "").trim().toLowerCase();
  const parts = cleaned.split(".");
  return parts[parts.length - 1] ?? cleaned;
}

function isSingleTenant(table: string): boolean {
  return SINGLE_TENANT_TABLES.has(table);
}

function hasTenantScope(sql: string): boolean {
  return /\borganization_id\b/i.test(sql);
}

function makeFinding(
  file: string,
  content: string,
  offset: number,
  ruleId: "TENANT-SQL-001" | "TENANT-SQL-002",
  table: string,
  statement: string,
): Finding {
  const { line, column } = offsetToLineCol(content, offset);
  const lines = content.split("\n");
  return {
    file,
    line,
    column,
    ruleId,
    severity: "error",
    table,
    message: `TENANT-LINT: query em ${table} não filtra por organization_id`,
    snippet: firstLine(statement) || lines[line - 1] || "",
  };
}

function dedupeFindings(findings: Finding[]): Finding[] {
  const seen = new Set<string>();
  return findings.filter((finding) => {
    const key = `${finding.file}:${finding.line}:${finding.column}:${finding.ruleId}:${finding.table}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function firstLine(text: string): string {
  return text.trim().split("\n")[0]?.trim() ?? "";
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
