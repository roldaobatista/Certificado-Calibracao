import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

const repoRoot = process.cwd();

test("PRD §13.15: profile A/B/C selects the matching PDF template and blocks improper Cgcre/RBC symbol usage", () => {
  const command = process.platform === "win32" ? (process.env.ComSpec ?? "cmd.exe") : "pnpm";
  const args =
    process.platform === "win32"
      ? ["/d", "/s", "/c", "pnpm --filter @afere/normative-rules exec tsx --test src/regulatory-profiles.test.ts"]
      : ["--filter", "@afere/normative-rules", "exec", "tsx", "--test", "src/regulatory-profiles.test.ts"];

  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: "utf8",
  });

  assert.equal(result.status, 0, `${String(result.error ?? "")}\n${result.stdout}${result.stderr}`);
});
