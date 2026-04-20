import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const repoRoot = process.cwd();
const scriptPath = join(repoRoot, "tools", "check-agents-drift.ts");
const tsxLoaderUrl = pathToFileURL(join(repoRoot, "node_modules", "tsx", "dist", "loader.mjs")).href;

function makeWorkspace(): string {
  const root = mkdtempSync(join(tmpdir(), "afere-check-agents-drift-"));
  mkdirSync(join(root, ".claude", "agents"), { recursive: true });
  mkdirSync(join(root, ".codex", "agents"), { recursive: true });
  return root;
}

function runDriftCheck(root: string) {
  return spawnSync(process.execPath, ["--import", tsxLoaderUrl, scriptPath], {
    cwd: root,
    encoding: "utf8",
  });
}

test("accepts Claude agent frontmatter with CRLF line endings", () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, ".claude", "agents", "backend-api.md"),
      [
        "---",
        "name: backend-api",
        "description: Backend tecnico",
        "---",
        "",
        "## Mandato",
        "",
        "Implementa backend.",
        "",
      ].join("\r\n"),
    );
    writeFileSync(
      join(root, ".codex", "agents", "backend-api.toml"),
      'name = "backend-api"\ndescription = "Backend tecnico"\n',
    );

    const result = runDriftCheck(root);

    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.match(result.stdout, /Claude agents: 1 \| Codex agents: 1/);
    assert.match(result.stdout, /sem drift/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
