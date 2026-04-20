import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkSyncSimulator } from "./sync-simulator-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-sync-sim-check-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "evals", "sync-simulator", "scenarios"), { recursive: true });
  mkdirSync(join(root, "evals", "sync-simulator", "engine"), { recursive: true });
  mkdirSync(join(root, "evals", "sync-simulator", "properties"), { recursive: true });
  mkdirSync(join(root, "evals", "sync-simulator", "seeds", "canonical"), { recursive: true });
  mkdirSync(join(root, "evals", "sync-simulator", "reports"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeCompleteSyncSimulatorWorkspace(root: string) {
  writeFileSync(
    join(root, "evals", "sync-simulator", "README.md"),
    "# Sync simulator\n\nC1 C2 C3 C4 C5 C6 C7 C8\n",
  );
  writeFileSync(join(root, "evals", "sync-simulator", "engine", "simulator.ts"), "export {}\n");
  writeFileSync(join(root, "evals", "sync-simulator", "sync-simulator.test.ts"), "test('sync', () => {});\n");
  writeFileSync(join(root, "evals", "sync-simulator", "reports", "README.md"), "# Reports\n");
  for (const property of ["convergence", "hash-chain-integrity", "signature-lock", "idempotency"]) {
    writeFileSync(join(root, "evals", "sync-simulator", "properties", `${property}.md`), `# ${property}\n`);
  }
  writeFileSync(
    join(root, "evals", "sync-simulator", "seeds", "canonical", "seeds.yaml"),
    ["- 3735928559", "- 3405691582", "- 324508639", ""].join("\n"),
  );
  writeFileSync(
    join(root, "evals", "sync-simulator", "scenarios", "canonical.yaml"),
    [
      "scenarios:",
      "  - id: C1",
      "    expected: human_review_required",
      "  - id: C2",
      "    expected: OS_LOCKED_FOR_SIGNATURE",
      "  - id: C3",
      "    expected: single_signature",
      "  - id: C4",
      "    expected: reissue_preserves_hash_chain",
      "  - id: C5",
      "    expected: deterministic_convergence",
      "  - id: C6",
      "    expected: idempotent_replay",
      "  - id: C7",
      "    expected: lamport_reorder",
      "  - id: C8",
      "    expected: server_clock_normalization",
      "",
    ].join("\n"),
  );
}

test("fails when sync simulator artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkSyncSimulator(root);

    assert.match(result.errors.join("\n"), /SYNC-SIM-001/);
    assert.match(result.errors.join("\n"), /canonical\.yaml/);
    assert.match(result.errors.join("\n"), /sync-simulator\.test\.ts/);
  } finally {
    cleanup();
  }
});

test("fails when canonical scenarios do not cover C1-C8", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteSyncSimulatorWorkspace(root);
    writeFileSync(
      join(root, "evals", "sync-simulator", "scenarios", "canonical.yaml"),
      ["scenarios:", "  - id: C1", "    expected: human_review_required", ""].join("\n"),
    );

    const result = checkSyncSimulator(root);

    assert.match(result.errors.join("\n"), /SYNC-SIM-003/);
    assert.match(result.errors.join("\n"), /C8/);
  } finally {
    cleanup();
  }
});

test("passes for complete sync simulator structure", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteSyncSimulatorWorkspace(root);

    const result = checkSyncSimulator(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedScenarios, 8);
    assert.equal(result.checkedProperties, 4);
  } finally {
    cleanup();
  }
});
