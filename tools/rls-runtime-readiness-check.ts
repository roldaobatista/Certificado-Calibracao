#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export type RlsRuntimeReadinessResult = {
  errors: string[];
  checkedFiles: number;
};

const MIGRATIONS_ROOT = "packages/db/prisma/migrations";
const TENANT_CONTEXT_FILE = "packages/db/src/tenant-context.ts";
const REQUIRED_DOCS = [
  "specs/0099-rls-runtime-role-readiness.md",
  "adr/0065-rls-runtime-role-readiness.md",
  "compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk.md",
];
const REQUIRED_DOC_PHRASES = [
  "FORCE ROW LEVEL SECURITY",
  "afere_app",
  "app.current_organization_id",
  "owner-bypass",
];

export function checkRlsRuntimeReadiness(root = process.cwd()): RlsRuntimeReadinessResult {
  const errors: string[] = [];
  let checkedFiles = 0;

  const dockerComposePath = resolve(root, "docker-compose.yml");
  const envExamplePath = resolve(root, ".env.example");
  const migrationFiles = listMigrationFiles(resolve(root, MIGRATIONS_ROOT));
  const tenantContextPath = resolve(root, TENANT_CONTEXT_FILE);

  const dockerCompose = readOptionalFile(dockerComposePath);
  const envExample = readOptionalFile(envExamplePath);
  checkedFiles += Number(dockerCompose !== null) + Number(envExample !== null) + migrationFiles.length;

  const ownerUser = dockerCompose ? extractPostgresOwnerUser(dockerCompose) : null;
  const runtimeUsers = dockerCompose ? extractRuntimeDatabaseUsers(dockerCompose) : [];
  const appRuntimeUsers = ownerUser ? runtimeUsers.filter((user) => user !== ownerUser) : [];
  const forceRlsMigrations = migrationFiles.filter((file) =>
    /\bFORCE\s+ROW\s+LEVEL\s+SECURITY\b/i.test(readFileSync(file, "utf8")),
  );
  const tenantContextImplemented = hasTenantContextImplementation(tenantContextPath);

  // 001: Se docker-compose usa owner na DATABASE_URL, exigir documentação de bypass
  //      exceto se DATABASE_APP_URL também estiver configurada (role não-owner separada).
  const hasAppUrlInCompose = dockerCompose ? /DATABASE_APP_URL:/.test(dockerCompose) : false;
  if (ownerUser && runtimeUsers.includes(ownerUser) && !hasAppUrlInCompose) {
    const missingDocs = checkRequiredDocs(root);
    checkedFiles += REQUIRED_DOCS.length;
    if (missingDocs.length > 0) {
      errors.push(
        `RUNTIME-RLS-001: docker-compose usa DATABASE_URL com o dono do banco (${ownerUser}), mas a exceção owner-bypass não está documentada: ${missingDocs.join(", ")}.`,
      );
    }
  }

  // 002: FORCE RLS só é seguro com tenant context transacional implementado.
  if (forceRlsMigrations.length > 0 && !tenantContextImplemented) {
    errors.push(
      `RUNTIME-RLS-002: FORCE ROW LEVEL SECURITY apareceu antes de ${TENANT_CONTEXT_FILE} implementar app.current_organization_id transacional (${forceRlsMigrations.map((file) => displayPath(root, file)).join(", ")}).`,
    );
  }

  // 003: Se DATABASE_APP_URL está presente, tenant context deve estar implementado.
  const hasAppUrlInEnv = envExample ? envExample.includes("DATABASE_APP_URL") : false;
  if (hasAppUrlInEnv && !tenantContextImplemented) {
    errors.push(
      `RUNTIME-RLS-003: DATABASE_APP_URL está configurada, mas ${TENANT_CONTEXT_FILE} não implementa app.current_organization_id transacional.`,
    );
  }

  // 004: .env.example deve documentar separação owner/app e contexto RLS.
  if (!envExample) {
    errors.push("RUNTIME-RLS-004: .env.example ausente; não há registro das URLs owner/app para RLS runtime.");
  } else {
    const missingEnvMarkers = ["DATABASE_OWNER_URL", "DATABASE_APP_URL", "app.current_organization_id"].filter(
      (marker) => !envExample.includes(marker),
    );
    if (missingEnvMarkers.length > 0) {
      errors.push(`RUNTIME-RLS-004: .env.example deve documentar separação owner/app e contexto RLS: ${missingEnvMarkers.join(", ")}.`);
    }
  }

  // 005: Verificar que pelo menos uma migration cria ou referencia a role afere_app.
  const hasAppRoleInMigrations = migrationFiles.some((file) =>
    /\bafere_app\b/i.test(readFileSync(file, "utf8")),
  );
  if (!hasAppRoleInMigrations) {
    errors.push("RUNTIME-RLS-005: Nenhuma migration cria ou referencia a role afere_app.");
  }

  return {
    errors,
    checkedFiles,
  };
}

function listMigrationFiles(root: string): string[] {
  if (!existsSync(root)) return [];
  const files: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = resolve(root, entry.name);
    if (!entry.isDirectory()) continue;

    const migration = resolve(path, "migration.sql");
    if (existsSync(migration) && statSync(migration).isFile()) files.push(migration);
  }
  return files.sort((a, b) => a.localeCompare(b));
}

function readOptionalFile(path: string): string | null {
  return existsSync(path) && statSync(path).isFile() ? readFileSync(path, "utf8") : null;
}

function extractPostgresOwnerUser(compose: string): string | null {
  const match = compose.match(/\bPOSTGRES_USER:\s*['"]?([^'"\s#]+)['"]?/);
  return match?.[1] ?? null;
}

function extractRuntimeDatabaseUsers(compose: string): string[] {
  const users = new Set<string>();
  const regex = /\bDATABASE_URL:\s*['"]?postgres(?:ql)?:\/\/([^:'"@\s#]+):/gi;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(compose)) !== null) {
    const user = match[1]?.trim();
    if (user) users.add(user);
  }
  return [...users].sort((a, b) => a.localeCompare(b));
}

function hasTenantContextImplementation(path: string): boolean {
  const content = readOptionalFile(path);
  if (!content) return false;
  return /\bwithTenant(?:Context|Prisma)?\b/.test(content) && /app\.current_organization_id/.test(content);
}

function checkRequiredDocs(root: string): string[] {
  const missing: string[] = [];
  for (const path of REQUIRED_DOCS) {
    const fullPath = resolve(root, path);
    const content = readOptionalFile(fullPath);
    if (!content) {
      missing.push(path);
      continue;
    }

    const missingPhrases = REQUIRED_DOC_PHRASES.filter((phrase) => !content.includes(phrase));
    if (missingPhrases.length > 0) {
      missing.push(`${path} sem ${missingPhrases.join("/")}`);
    }
  }
  return missing;
}

function displayPath(root: string, path: string): string {
  return relative(root, path).split(sep).join("/");
}

function runCli() {
  const result = checkRlsRuntimeReadiness();
  for (const error of result.errors) console.error(`ERROR ${error}`);
  console.log(`rls-runtime-readiness-check: ${result.checkedFiles} arquivo(s) verificado(s).`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
