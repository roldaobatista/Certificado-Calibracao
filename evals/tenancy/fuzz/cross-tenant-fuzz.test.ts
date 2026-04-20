import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

const repoRoot = process.cwd();
const sqlPath = join(repoRoot, "evals", "tenancy", "fuzz", "cross-tenant-fuzz.sql");

test("RLS fuzz blocks 500 deterministic cross-tenant payloads", () => {
  assert.equal(existsSync(sqlPath), true, "missing evals/tenancy/fuzz/cross-tenant-fuzz.sql");
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

  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.match(result.stdout, /RLS fuzz blocked 500 cross-tenant payloads/);
});
