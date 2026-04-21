import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import os from "node:os";
import { test } from "node:test";

const workspaceRoot = process.cwd();

test("REQ-PRD-13-10 validates accredited scope and CMC policy in normative-rules", () => {
  const command =
    os.platform() === "win32"
      ? {
          file: "cmd.exe",
          args: [
            "/d",
            "/s",
            "/c",
            "pnpm --filter @afere/normative-rules exec tsx --test src/scope-cmc.test.ts",
          ],
        }
      : {
          file: "pnpm",
          args: ["--filter", "@afere/normative-rules", "exec", "tsx", "--test", "src/scope-cmc.test.ts"],
        };

  const result = spawnSync(command.file, command.args, {
    cwd: workspaceRoot,
    encoding: "utf8",
  });

  const combinedOutput = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  assert.equal(result.status, 0, combinedOutput);
});
