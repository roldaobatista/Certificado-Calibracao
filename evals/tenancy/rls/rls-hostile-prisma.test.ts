import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

const repoRoot = process.cwd();
const sqlPath = join(repoRoot, "evals", "tenancy", "rls", "rls-hostile-prisma.sql");

test("RLS hostile scenario with FORCE RLS blocks cross-tenant reads, forged inserts, and privilege escalation", () => {
  assert.equal(existsSync(sqlPath), true, "missing evals/tenancy/rls/rls-hostile-prisma.sql");
  const sql = readFileSync(sqlPath, "utf8");

  const result = spawnSync(
    "docker",
    ["compose", "exec", "-T", "postgres", "psql", "-U", "afere", "-d", "afere", "-X", "-v", "ON_ERROR_STOP=1"],
    {
      cwd: repoRoot,
      encoding: "utf8",
      input: sql,
    },
  );

  const fallback =
    result.status === 0
      ? result
      : spawnSync("psql", ["-X", "-v", "ON_ERROR_STOP=1", process.env.DATABASE_URL ?? "", "-f", sqlPath], {
          cwd: repoRoot,
          encoding: "utf8",
        });

  assert.equal(fallback.status, 0, fallback.stderr || fallback.stdout);
  assert.match(fallback.stdout, /RLS hostile Prisma scenario passed/);
});
