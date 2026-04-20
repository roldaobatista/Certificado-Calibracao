import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { lintTenantSql } from "./lint.js";

function makeWorkspace(): string {
  const root = mkdtempSync(join(tmpdir(), "afere-tenant-lint-"));
  mkdirSync(join(root, "apps", "api", "src"), { recursive: true });
  mkdirSync(join(root, "packages", "db", "prisma", "migrations", "001_init"), { recursive: true });
  writeFileSync(join(root, "pnpm-workspace.yaml"), "packages:\n  - packages/*\n");
  return root;
}

test("flags raw API SQL against multitenant table without organization_id", async () => {
  const root = makeWorkspace();
  try {
    const file = join(root, "apps", "api", "src", "leaky-query.ts");
    writeFileSync(
      file,
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE id = ${certificateId}`;\n",
    );

    const result = await lintTenantSql({ cwd: root, paths: ["apps/api/src/leaky-query.ts"] });

    assert.equal(result.errors, 1);
    assert.equal(result.findings[0]?.ruleId, "TENANT-SQL-001");
    assert.equal(result.findings[0]?.table, "certificates");
    assert.match(result.findings[0]?.message ?? "", /organization_id/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("allows raw API SQL when organization_id scopes the query", async () => {
  const root = makeWorkspace();
  try {
    const file = join(root, "apps", "api", "src", "safe-query.ts");
    writeFileSync(
      file,
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE organization_id = ${organizationId} AND id = ${certificateId}`;\n",
    );

    const result = await lintTenantSql({ cwd: root, paths: ["apps/api/src/safe-query.ts"] });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("flags RLS policy that does not bind organization_id", async () => {
  const root = makeWorkspace();
  try {
    const file = join(root, "packages", "db", "prisma", "migrations", "001_init", "migration.sql");
    writeFileSync(
      file,
      "CREATE POLICY certificate_select ON certificates FOR SELECT USING (id = current_setting('app.certificate_id')::uuid);\n",
    );

    const result = await lintTenantSql({
      cwd: root,
      paths: ["packages/db/prisma/migrations/001_init/migration.sql"],
    });

    assert.equal(result.errors, 1);
    assert.equal(result.findings[0]?.ruleId, "TENANT-SQL-002");
    assert.equal(result.findings[0]?.table, "certificates");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("allows RLS policy that binds organization_id", async () => {
  const root = makeWorkspace();
  try {
    const file = join(root, "packages", "db", "prisma", "migrations", "001_init", "migration.sql");
    writeFileSync(
      file,
      "CREATE POLICY certificate_select ON certificates FOR SELECT USING (organization_id = current_setting('app.organization_id')::uuid);\n",
    );

    const result = await lintTenantSql({
      cwd: root,
      paths: ["packages/db/prisma/migrations/001_init/migration.sql"],
    });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("default scan ignores tenant-lint test fixtures", async () => {
  const root = makeWorkspace();
  try {
    const testDir = join(root, "packages", "db", "tools", "tenant-lint", "src");
    mkdirSync(testDir, { recursive: true });
    writeFileSync(
      join(testDir, "lint.test.ts"),
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE id = ${certificateId}`;\n",
    );

    const result = await lintTenantSql({ cwd: root });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("explicit scan ignores test fixtures so pre-commit can include tenant-lint tests", async () => {
  const root = makeWorkspace();
  try {
    const testDir = join(root, "packages", "db", "tools", "tenant-lint", "src");
    mkdirSync(testDir, { recursive: true });
    writeFileSync(
      join(testDir, "lint.test.ts"),
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE id = ${certificateId}`;\n",
    );

    const result = await lintTenantSql({
      cwd: root,
      paths: ["packages/db/tools/tenant-lint/src/lint.test.ts"],
    });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
