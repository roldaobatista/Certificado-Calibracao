import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

test("REQ-PRD-13-03 validates structured certificate measurement declarations in the uncertainty engine", () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? ["/d", "/s", "/c", "pnpm exec tsx --test packages/engine-uncertainty/src/measurement-declarations.test.ts"]
      : ["exec", "tsx", "--test", "packages/engine-uncertainty/src/measurement-declarations.test.ts"];

  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
