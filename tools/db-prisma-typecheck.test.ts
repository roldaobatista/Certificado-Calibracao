import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

const repoRoot = process.cwd();
test("db package typecheck generates and resolves Prisma Client", { timeout: 30_000 }, () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? ["/d", "/s", "/c", "pnpm --filter @afere/db typecheck"]
      : ["--filter", "@afere/db", "typecheck"];
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
