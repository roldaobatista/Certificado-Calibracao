import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

test("REQ-PRD-13-11 validates self-signup providers and MFA policy", () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? [
          "/d",
          "/s",
          "/c",
          "pnpm exec tsx --test apps/api/src/domain/auth/self-signup-policy.test.ts apps/web/src/auth/self-signup-checklist.test.ts",
        ]
      : [
          "exec",
          "tsx",
          "--test",
          "apps/api/src/domain/auth/self-signup-policy.test.ts",
          "apps/web/src/auth/self-signup-checklist.test.ts",
        ];

  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
