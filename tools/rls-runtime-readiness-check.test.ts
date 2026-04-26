import assert from "node:assert/strict";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

import { checkRlsRuntimeReadiness } from "./rls-runtime-readiness-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-rls-runtime-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "packages/db/prisma/migrations/202604230001_base"), { recursive: true });
  mkdirSync(join(root, "packages/db/src"), { recursive: true });
  mkdirSync(join(root, "specs"), { recursive: true });
  mkdirSync(join(root, "adr"), { recursive: true });
  mkdirSync(join(root, "compliance/validation-dossier/findings"), { recursive: true });
  mkdirSync(join(root, ".githooks"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeBaseline(root: string, overrides: { dockerCompose?: string; migration?: string; envExample?: string } = {}) {
  writeFileSync(
    join(root, "docker-compose.yml"),
    overrides.dockerCompose ??
      [
        "services:",
        "  postgres:",
        "    environment:",
        "      POSTGRES_USER: afere",
        "  api:",
        "    environment:",
        "      DATABASE_URL: postgresql://afere:afere@postgres:5432/afere?schema=public",
      ].join("\n"),
  );
  writeFileSync(
    join(root, ".env.example"),
    overrides.envExample ??
      [
        "POSTGRES_USER=afere",
        "DATABASE_OWNER_URL=postgresql://afere:afere@postgres:5432/afere?schema=public",
        "DATABASE_APP_URL=postgresql://afere_app:afere_app@postgres:5432/afere?schema=public",
        "# DATABASE_URL permanece owner-only em dev ate tenant context transacional.",
      ].join("\n"),
  );
  writeFileSync(
    join(root, "packages/db/prisma/migrations/202604230001_base/migration.sql"),
    overrides.migration ??
      [
        'CREATE TABLE "public"."service_orders" (',
        '  "id" uuid NOT NULL,',
        '  "organization_id" uuid NOT NULL',
        ");",
        'ALTER TABLE "public"."service_orders" ENABLE ROW LEVEL SECURITY;',
        'CREATE POLICY "service_orders_tenant_isolation"',
        '  ON "public"."service_orders"',
        "  FOR ALL",
        '  USING ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid)',
        '  WITH CHECK ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid);',
      ].join("\n"),
  );
  writeReadinessDocs(root);
  writeFileSync(join(root, "package.json"), JSON.stringify({ scripts: { "check:all": "pnpm rls-runtime-readiness-check" } }));
  writeFileSync(join(root, ".githooks/pre-commit"), "pnpm rls-runtime-readiness-check\n");
}

function writeReadinessDocs(root: string) {
  const requiredText = [
    "FORCE ROW LEVEL SECURITY",
    "afere_app",
    "app.current_organization_id",
    "owner-bypass",
  ].join("\n");
  writeFileSync(join(root, "specs/0099-rls-runtime-role-readiness.md"), requiredText);
  writeFileSync(join(root, "adr/0065-rls-runtime-role-readiness.md"), requiredText);
  writeFileSync(
    join(root, "compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk.md"),
    requiredText,
  );
}

test("fails when owner runtime is silent and not documented as an explicit risk", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeBaseline(root);
    rmSync(join(root, "specs/0099-rls-runtime-role-readiness.md"));

    const result = checkRlsRuntimeReadiness(root);

    assert.match(result.errors.join("\n"), /RUNTIME-RLS-001/);
    assert.match(result.errors.join("\n"), /0099-rls-runtime-role-readiness/);
  } finally {
    cleanup();
  }
});

test("fails when FORCE RLS is introduced before tenant context implementation exists", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeBaseline(root, {
      migration: [
        'CREATE TABLE "public"."service_orders" (',
        '  "id" uuid NOT NULL,',
        '  "organization_id" uuid NOT NULL',
        ");",
        'ALTER TABLE "public"."service_orders" ENABLE ROW LEVEL SECURITY;',
        'ALTER TABLE "public"."service_orders" FORCE ROW LEVEL SECURITY;',
        'CREATE POLICY "service_orders_tenant_isolation"',
        '  ON "public"."service_orders"',
        "  FOR ALL",
        '  USING ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid)',
        '  WITH CHECK ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid);',
      ].join("\n"),
    });

    const result = checkRlsRuntimeReadiness(root);

    assert.match(result.errors.join("\n"), /RUNTIME-RLS-002/);
    assert.match(result.errors.join("\n"), /packages\/db\/src\/tenant-context\.ts/);
  } finally {
    cleanup();
  }
});

test("fails when app runtime role is enabled before tenant context implementation exists", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeBaseline(root, {
      dockerCompose: [
        "services:",
        "  postgres:",
        "    environment:",
        "      POSTGRES_USER: afere",
        "  api:",
        "    environment:",
        "      DATABASE_URL: postgresql://afere_app:afere_app@postgres:5432/afere?schema=public",
      ].join("\n"),
    });

    const result = checkRlsRuntimeReadiness(root);

    assert.match(result.errors.join("\n"), /RUNTIME-RLS-003/);
  } finally {
    cleanup();
  }
});

test("passes for the committed repository readiness state", () => {
  const result = checkRlsRuntimeReadiness(process.cwd());

  assert.deepEqual(result.errors, []);
  assert.ok(result.checkedFiles >= 6);
});

test("wires runtime readiness into check:all and pre-commit", () => {
  const root = process.cwd();
  const packageJson = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  const preCommit = readFileSync(resolve(root, ".githooks/pre-commit"), "utf8");

  assert.equal(packageJson.scripts["rls-runtime-readiness-check"], "tsx tools/rls-runtime-readiness-check.ts");
  assert.match(packageJson.scripts["check:all"], /pnpm rls-runtime-readiness-check/);
  assert.match(preCommit, /rls-runtime-readiness-check/);
});
