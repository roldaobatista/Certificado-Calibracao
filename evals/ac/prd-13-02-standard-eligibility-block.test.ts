import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

test("REQ-PRD-13-02 validates fail-closed standard eligibility rules in normative-rules", () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? ["/d", "/s", "/c", "pnpm exec tsx --test packages/normative-rules/src/standard-eligibility.test.ts"]
      : ["exec", "tsx", "--test", "packages/normative-rules/src/standard-eligibility.test.ts"];

  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
