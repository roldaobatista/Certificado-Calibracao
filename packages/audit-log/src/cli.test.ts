import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { GENESIS_HASH, computeAuditHash, type AuditChainEntry } from "./verify.js";

const testDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(testDir, "../../..");
const cliPath = join(testDir, "cli.ts");

function entry(id: string, prevHash: string, payload: unknown): AuditChainEntry {
  return { id, prevHash, payload, hash: computeAuditHash(prevHash, payload) };
}

function runCli(args: string[]) {
  return spawnSync(process.execPath, ["--import", "tsx", cliPath, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
  });
}

test("CLI exits 0 for a valid JSONL hash chain", () => {
  const root = mkdtempSync(join(tmpdir(), "afere-audit-chain-"));
  try {
    const first = entry("evt-1", GENESIS_HASH, { action: "created" });
    const second = entry("evt-2", first.hash, { action: "approved" });
    const file = join(root, "audit.jsonl");
    writeFileSync(file, `${JSON.stringify(first)}\n${JSON.stringify(second)}\n`);

    const result = runCli([file]);

    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /2 registros verificados/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("CLI exits 1 for a tampered JSONL hash chain", () => {
  const root = mkdtempSync(join(tmpdir(), "afere-audit-chain-"));
  try {
    const first = entry("evt-1", GENESIS_HASH, { action: "created" });
    const second = entry("evt-2", first.hash, { action: "approved" });
    const file = join(root, "audit.jsonl");
    writeFileSync(file, `${JSON.stringify(first)}\n${JSON.stringify({ ...second, payload: { action: "rejected" } })}\n`);

    const result = runCli([file]);

    assert.equal(result.status, 1);
    assert.match(result.stdout, /hash_mismatch/);
    assert.match(result.stdout, /evt-2/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
