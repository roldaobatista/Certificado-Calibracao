import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

const repoRoot = process.cwd();
const cliPath = join(repoRoot, "packages", "db", "tools", "tenant-lint", "src", "cli.ts");

function makeWorkspace(): string {
  const root = mkdtempSync(join(tmpdir(), "afere-tenant-lint-cli-"));
  mkdirSync(join(root, "apps", "api", "src"), { recursive: true });
  writeFileSync(join(root, "pnpm-workspace.yaml"), "packages:\n  - packages/*\n");
  return root;
}

function runCli(root: string, args: string[] = []) {
  return spawnSync(process.execPath, ["--import", "tsx", cliPath, "--cwd", root, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
  });
}

test("CLI exits 1 and prints TENANT-LINT finding for unscoped SQL", () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "apps", "api", "src", "leak.ts"),
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE id = ${certificateId}`;\n",
    );

    const result = runCli(root, ["apps/api/src/leak.ts"]);

    assert.equal(result.status, 1);
    assert.match(result.stdout, /TENANT-LINT/);
    assert.match(result.stdout, /apps[/\\]api[/\\]src[/\\]leak\.ts:1:\d+/);
    assert.match(result.stdout, /certificates/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("CLI exits 0 for tenant-scoped SQL", () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "apps", "api", "src", "safe.ts"),
      "await prisma.$queryRaw`SELECT * FROM certificates WHERE organization_id = ${organizationId}`;\n",
    );

    const result = runCli(root, ["apps/api/src/safe.ts"]);

    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /errors: 0/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
