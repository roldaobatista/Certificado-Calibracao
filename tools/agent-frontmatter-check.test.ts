import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkAgentFrontmatter } from "./agent-frontmatter-check";

const EXPECTED_AGENTS = [
  "android",
  "backend-api",
  "copy-compliance",
  "db-schema",
  "legal-counsel",
  "lgpd-security",
  "metrology-auditor",
  "metrology-calc",
  "product-governance",
  "qa-acceptance",
  "regulator",
  "senior-reviewer",
  "web-ui",
] as const;

function makeWorkspace() {
  const root = join(tmpdir(), `afere-agent-frontmatter-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, ".claude", "agents"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeAgent(root: string, name: string, overrides: string[] = []) {
  const role = ["legal-counsel", "metrology-auditor", "senior-reviewer"].includes(name) ? "auditor" : "executor";
  const tools = role === "auditor" ? "[Read, Grep, Glob, Bash]" : "[Read, Edit, Write, Grep, Glob, Bash]";
  const model = role === "auditor" ? "opus" : "sonnet";
  const baseFields = [
    "schema_version: 1",
    `name: ${name}`,
    `role: ${role}`,
    `description: ${name} agent`,
    `model: ${model}`,
    `tools: ${tools}`,
    "owner_paths: [apps/example/**]",
    "blocked_write_paths: [PRD.md]",
    "handoff_targets: [product-governance]",
  ];
  const overrideKeys = new Set(overrides.map((line) => line.split(":", 1)[0]));
  const fields = [...baseFields.filter((line) => !overrideKeys.has(line.split(":", 1)[0])), ...overrides];

  writeFileSync(
    join(root, ".claude", "agents", `${name}.md`),
    [
      "---",
      ...fields,
      "---",
      "",
      "## Mandato",
      "",
      "Agente de teste.",
      "",
      "## Paths permitidos (escrita)",
      "",
      "- `apps/example/**`",
      "",
      "## Paths bloqueados (leitura ok, escrita não)",
      "",
      "- `PRD.md`",
      "",
      "## Hand-offs",
      "",
      "- Quando precisar de governança → delegar para `product-governance`.",
      "",
    ].join("\n"),
  );
}

function writeCompleteWorkspace(root: string) {
  for (const agent of EXPECTED_AGENTS) writeAgent(root, agent);
}

test("fails closed when agent frontmatter is missing standard fields", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);
    writeFileSync(
      join(root, ".claude", "agents", "backend-api.md"),
      [
        "---",
        "name: backend-api",
        "description: backend",
        "model: gpt-4",
        "tools: [Read, Write]",
        "---",
        "",
        "## Mandato",
        "",
        "Sem frontmatter padronizado.",
        "",
      ].join("\n"),
    );

    const result = checkAgentFrontmatter(root);

    assert.match(result.errors.join("\n"), /AGENT-FM-002/);
    assert.match(result.errors.join("\n"), /schema_version/);
    assert.match(result.errors.join("\n"), /role/);
    assert.match(result.errors.join("\n"), /model/);
    assert.match(result.errors.join("\n"), /owner_paths/);
  } finally {
    cleanup();
  }
});

test("fails when an auditor has write-capable tools", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);
    writeAgent(root, "senior-reviewer", ["tools: [Read, Edit, Grep, Glob, Bash]"]);

    const result = checkAgentFrontmatter(root);

    assert.match(result.errors.join("\n"), /AGENT-FM-005/);
    assert.match(result.errors.join("\n"), /senior-reviewer/);
    assert.match(result.errors.join("\n"), /Edit/);
  } finally {
    cleanup();
  }
});

test("fails when file names and handoff targets are not canonical", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);
    writeFileSync(
      join(root, ".claude", "agents", "bad_name.md"),
      [
        "---",
        "schema_version: 1",
        "name: bad_name",
        "role: executor",
        "description: invalid",
        "model: sonnet",
        "tools: [Read, Edit, Write]",
        "owner_paths: [apps/example/**]",
        "blocked_write_paths: [PRD.md]",
        "handoff_targets: [missing-agent]",
        "---",
        "",
      ].join("\n"),
    );

    const result = checkAgentFrontmatter(root);

    assert.match(result.errors.join("\n"), /AGENT-FM-001/);
    assert.match(result.errors.join("\n"), /bad_name/);
    assert.match(result.errors.join("\n"), /AGENT-FM-006/);
    assert.match(result.errors.join("\n"), /missing-agent/);
  } finally {
    cleanup();
  }
});

test("passes for a complete standardized agent set", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);

    const result = checkAgentFrontmatter(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedAgents, 13);
  } finally {
    cleanup();
  }
});
