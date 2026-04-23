import assert from "node:assert/strict";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

const CHECKER_PATH = resolve(process.cwd(), "tools/roadmap-backlog-check.ts");

async function loadChecker() {
  assert.equal(existsSync(CHECKER_PATH), true, "tools/roadmap-backlog-check.ts deve existir.");
  return import("./roadmap-backlog-check");
}

function makeWorkspace() {
  const root = join(tmpdir(), `afere-roadmap-backlog-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "roadmap"), { recursive: true });
  mkdirSync(join(root, "compliance", "validation-dossier"), { recursive: true });
  mkdirSync(join(root, "harness"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function seedCanonicalWorkspace(root: string) {
  for (const relativePath of [
    "compliance/roadmap/README.md",
    "compliance/roadmap/v1-v5.yaml",
    "compliance/roadmap/execution-backlog.yaml",
    "compliance/validation-dossier/requirements.yaml",
    "harness/10-roadmap.md",
  ]) {
    const source = resolve(process.cwd(), relativePath);
    const target = join(root, ...relativePath.split("/"));
    mkdirSync(join(target, ".."), { recursive: true });
    writeFileSync(target, readFileSync(source, "utf8"));
  }
}

test("fails when the canonical execution backlog artifacts are missing", async () => {
  const { checkRoadmapBacklog } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkRoadmapBacklog(root);

    assert.match(result.errors.join("\n"), /BACKLOG-001/);
    assert.match(result.errors.join("\n"), /execution-backlog\.yaml/);
    assert.match(result.errors.join("\n"), /v1-v5\.yaml/);
    assert.match(result.errors.join("\n"), /README\.md/);
  } finally {
    cleanup();
  }
});

test("fails when backlog order breaks the execution chain", async () => {
  const { checkRoadmapBacklog } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    seedCanonicalWorkspace(root);
    writeFileSync(
      join(root, "compliance", "roadmap", "execution-backlog.yaml"),
      readFileSync(join(root, "compliance", "roadmap", "execution-backlog.yaml"), "utf8").replace(
        "  - id: V1.2",
        "  - id: V1.3",
      ),
    );

    const result = checkRoadmapBacklog(root);

    assert.match(result.errors.join("\n"), /BACKLOG-003/);
    assert.match(result.errors.join("\n"), /cadeia estrita/);
  } finally {
    cleanup();
  }
});

test("fails when an item links a requirement that does not belong to its slice", async () => {
  const { checkRoadmapBacklog } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    seedCanonicalWorkspace(root);
    const backlogPath = join(root, "compliance", "roadmap", "execution-backlog.yaml");
    const original = readFileSync(backlogPath, "utf8");
    const mutated = original.replace(
      /(\s+linked_requirements:\r?\n\s+- )REQ-PRD-13-11-AUTH-SSO-MFA/,
      "$1REQ-PRD-13-16-CONTROLLED-REISSUE",
    );
    assert.notEqual(
      mutated,
      original,
      "o fixture do backlog deve permitir trocar o requisito de V1 por um requisito de outra fatia.",
    );

    writeFileSync(
      backlogPath,
      mutated,
    );

    const result = checkRoadmapBacklog(root);

    assert.match(result.errors.join("\n"), /BACKLOG-004/);
    assert.match(result.errors.join("\n"), /REQ-PRD-13-16-CONTROLLED-REISSUE/);
    assert.match(result.errors.join("\n"), /V1/);
  } finally {
    cleanup();
  }
});

test("fails when roadmap README omits the backlog executable reference", async () => {
  const { checkRoadmapBacklog } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    seedCanonicalWorkspace(root);
    writeFileSync(join(root, "compliance", "roadmap", "README.md"), "# Roadmap\n");

    const result = checkRoadmapBacklog(root);

    assert.match(result.errors.join("\n"), /BACKLOG-005/);
    assert.match(result.errors.join("\n"), /execution-backlog\.yaml/);
    assert.match(result.errors.join("\n"), /roadmap-backlog-check/);
  } finally {
    cleanup();
  }
});

test("passes for the canonical execution backlog", async () => {
  const { checkRoadmapBacklog } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    seedCanonicalWorkspace(root);

    const result = checkRoadmapBacklog(root);

    assert.deepEqual(result.errors, []);
  assert.equal(result.checkedItems, 30);
  } finally {
    cleanup();
  }
});

test("wires roadmap-backlog-check into the root pipeline and pre-commit", () => {
  const packageJson = JSON.parse(readFileSync(resolve(process.cwd(), "package.json"), "utf8"));
  const preCommit = readFileSync(resolve(process.cwd(), ".githooks/pre-commit"), "utf8");
  const hook = readFileSync(resolve(process.cwd(), ".claude/hooks/roadmap-backlog-check.sh"), "utf8");

  assert.equal(packageJson.scripts["roadmap-backlog-check"], "tsx tools/roadmap-backlog-check.ts");
  assert.match(packageJson.scripts["check:all"], /pnpm roadmap-backlog-check/);
  assert.match(preCommit, /roadmap-backlog-check/);
  assert.match(hook, /run_pnpm roadmap-backlog-check/);
});
