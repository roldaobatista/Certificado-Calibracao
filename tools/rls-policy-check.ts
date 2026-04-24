#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export type RlsPolicyCheckResult = {
  errors: string[];
  checkedTables: number;
  checkedMigrations: number;
};

type MultitenantTable = {
  table: string;
  migration: string;
};

const MIGRATIONS_ROOT = "packages/db/prisma/migrations";

export function checkRlsPolicies(root = process.cwd()): RlsPolicyCheckResult {
  const migrationsRoot = resolve(root, MIGRATIONS_ROOT);
  const errors: string[] = [];
  const migrations = listMigrationFiles(migrationsRoot);

  if (!existsSync(migrationsRoot)) {
    return {
      errors: [`RLS-000: diretório de migrações ausente: ${MIGRATIONS_ROOT}.`],
      checkedTables: 0,
      checkedMigrations: 0,
    };
  }

  const multitenantTables = new Map<string, MultitenantTable>();
  const rlsEnabledTables = new Set<string>();
  const tenantPolicyTables = new Set<string>();

  for (const file of migrations) {
    const content = readFileSync(file, "utf8");
    const migration = relative(root, file).split(sep).join("/");

    for (const table of findCreatedMultitenantTables(content)) {
      if (!multitenantTables.has(table)) {
        multitenantTables.set(table, { table, migration });
      }
    }

    for (const table of findRlsEnabledTables(content)) {
      rlsEnabledTables.add(table);
    }

    for (const table of findTenantPolicyTables(content)) {
      tenantPolicyTables.add(table);
    }
  }

  for (const entry of [...multitenantTables.values()].sort((a, b) => a.table.localeCompare(b.table))) {
    if (!rlsEnabledTables.has(entry.table)) {
      errors.push(`RLS-001: tabela multitenant sem ENABLE ROW LEVEL SECURITY: ${entry.table} (${entry.migration}).`);
    }
    if (!tenantPolicyTables.has(entry.table)) {
      errors.push(`RLS-002: tabela multitenant sem policy tenant isolation com organization_id: ${entry.table} (${entry.migration}).`);
    }
  }

  return {
    errors,
    checkedTables: multitenantTables.size,
    checkedMigrations: migrations.length,
  };
}

function listMigrationFiles(root: string): string[] {
  if (!existsSync(root)) return [];
  const files: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = resolve(root, entry.name);
    if (entry.isDirectory()) {
      const migration = resolve(path, "migration.sql");
      if (existsSync(migration) && statSync(migration).isFile()) files.push(migration);
    }
  }
  return files.sort((a, b) => a.localeCompare(b));
}

function findCreatedMultitenantTables(content: string): string[] {
  const tables: string[] = [];
  const regex =
    /\bCREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(?:(?:"public"|public)\.)?"([^"]+)"\s*\(([\s\S]*?)\)\s*;/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(content)) !== null) {
    const table = normalizeTable(match[1] ?? "");
    const body = match[2] ?? "";
    if (!table || !hasOrganizationIdColumn(body)) continue;
    tables.push(table);
  }
  return tables;
}

function findRlsEnabledTables(content: string): string[] {
  const tables: string[] = [];
  const regex = /\bALTER\s+TABLE\s+(?:(?:"public"|public)\.)?"([^"]+)"\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\b/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(content)) !== null) {
    const table = normalizeTable(match[1] ?? "");
    if (table) tables.push(table);
  }
  return tables;
}

function findTenantPolicyTables(content: string): string[] {
  const tables: string[] = [];
  const regex = /\bCREATE\s+POLICY\b[\s\S]*?\bON\s+(?:(?:"public"|public)\.)?"([^"]+)"[\s\S]*?(?=;|$)/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(content)) !== null) {
    const table = normalizeTable(match[1] ?? "");
    const statement = match[0] ?? "";
    if (!table || !/\borganization_id\b/i.test(statement) || !/app\.current_organization_id/i.test(statement)) continue;
    tables.push(table);
  }
  return tables;
}

function hasOrganizationIdColumn(createTableBody: string): boolean {
  return /"organization_id"\s+[^,\n]+/i.test(createTableBody);
}

function normalizeTable(raw: string): string {
  return raw.replace(/"/g, "").trim().toLowerCase();
}

function runCli() {
  const result = checkRlsPolicies();
  for (const error of result.errors) console.error(`ERROR ${error}`);
  console.log(`rls-policy-check: ${result.checkedTables} tabela(s), ${result.checkedMigrations} migração(ões).`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
