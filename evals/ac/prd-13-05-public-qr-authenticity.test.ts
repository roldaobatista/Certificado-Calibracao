import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

test("REQ-PRD-13-05 validates public QR authenticity", () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? ["/d", "/s", "/c", "pnpm exec tsx --test apps/api/src/domain/certificates/public-qr.test.ts"]
      : ["exec", "tsx", "--test", "apps/api/src/domain/certificates/public-qr.test.ts"];

  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
