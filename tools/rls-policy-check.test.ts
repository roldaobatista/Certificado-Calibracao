import assert from "node:assert/strict";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

const CHECKER_PATH = resolve(process.cwd(), "tools/rls-policy-check.ts");

async function loadChecker() {
  assert.equal(existsSync(CHECKER_PATH), true, "tools/rls-policy-check.ts deve existir.");
  return import("./rls-policy-check");
}

function makeWorkspace() {
  const root = join(tmpdir(), `afere-rls-policy-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(root, { recursive: true });
  mkdirSync(join(root, "packages/db/prisma/migrations/202604230001_base"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeMigration(root: string, name: string, content: string) {
  const dir = join(root, "packages/db/prisma/migrations", name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "migration.sql"), content);
}

test("fails when a multitenant table is created without RLS and tenant policy", async () => {
  const { checkRlsPolicies } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    writeMigration(
      root,
      "202604230001_base",
      [
        'CREATE TABLE "public"."certificate_publications" (',
        '  "id" uuid NOT NULL,',
        '  "organization_id" uuid NOT NULL,',
        '  CONSTRAINT "certificate_publications_pkey" PRIMARY KEY ("id")',
        ");",
      ].join("\n"),
    );

    const result = checkRlsPolicies(root);

    assert.equal(result.errors.length, 2);
    assert.match(result.errors.join("\n"), /RLS-001.*certificate_publications/);
    assert.match(result.errors.join("\n"), /RLS-002.*certificate_publications/);
  } finally {
    cleanup();
  }
});

test("passes when every multitenant table has RLS and a tenant isolation policy", async () => {
  const { checkRlsPolicies } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    writeMigration(
      root,
      "202604230001_base",
      [
        'CREATE TABLE "public"."service_orders" (',
        '  "id" uuid NOT NULL,',
        '  "organization_id" uuid NOT NULL,',
        '  CONSTRAINT "service_orders_pkey" PRIMARY KEY ("id")',
        ");",
        'ALTER TABLE "public"."service_orders" ENABLE ROW LEVEL SECURITY;',
        'CREATE POLICY "service_orders_tenant_isolation"',
        '  ON "public"."service_orders"',
        "  FOR ALL",
        '  USING ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid)',
        '  WITH CHECK ("organization_id" = NULLIF(current_setting(\'app.current_organization_id\', true), \'\')::uuid);',
      ].join("\n"),
    );

    const result = checkRlsPolicies(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedTables, 1);
  } finally {
    cleanup();
  }
});

test("passes for the committed Prisma migrations", async () => {
  const { checkRlsPolicies } = await loadChecker();

  const result = checkRlsPolicies(process.cwd());

  assert.deepEqual(result.errors, []);
  assert.ok(result.checkedTables >= 19);
});

test("wires rls-policy-check into the root pipeline and pre-commit", () => {
  const packageJson = JSON.parse(readFileSync(resolve(process.cwd(), "package.json"), "utf8"));
  const preCommit = readFileSync(resolve(process.cwd(), ".githooks/pre-commit"), "utf8");

  assert.equal(packageJson.scripts["rls-policy-check"], "tsx tools/rls-policy-check.ts");
  assert.match(packageJson.scripts["check:all"], /pnpm rls-policy-check/);
  assert.match(preCommit, /rls-policy-check/);
});
