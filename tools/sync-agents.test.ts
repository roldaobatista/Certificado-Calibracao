import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { spawnSync } from "node:child_process";

const repoRoot = process.cwd();
const scriptPath = join(repoRoot, "tools", "sync-agents.ts");

function makeWorkspace(): string {
  const root = mkdtempSync(join(tmpdir(), "afere-sync-agents-"));
  mkdirSync(join(root, ".claude", "agents"), { recursive: true });
  mkdirSync(join(root, ".codex", "agents"), { recursive: true });

  writeFileSync(
    join(root, ".claude", "agents", "backend-api.md"),
    `---
name: backend-api
description: Backend técnico — auth, RBAC, emissão oficial
model: sonnet
tools: [Read, Edit, Bash]
---

## Mandato

Dono único de \`apps/api/**\`. Implementa workflows de OS.

**Não faz:**
- UI (→ \`web-ui\`).

## Paths permitidos (escrita)

- \`apps/api/**\`

## Paths bloqueados

- \`apps/web/**\`
`,
  );

  writeFileSync(
    join(root, ".codex", "agents", "backend-api.toml"),
    `name = "backend-api"
description = "desatualizado"
developer_instructions = "stale"
`,
  );

  return root;
}

function runSync(root: string, args: string[] = []) {
  return spawnSync(process.execPath, ["--import", "tsx", scriptPath, "--workspace", root, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
  });
}

test("check mode fails when generated Codex agent differs", () => {
  const root = makeWorkspace();
  try {
    const result = runSync(root, ["--check"]);

    assert.notEqual(result.status, 0);
    assert.match(result.stdout + result.stderr, /desatualizado: \.codex\/agents\/backend-api\.toml/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("write mode regenerates Codex agents from Claude agents using supported fields only", () => {
  const root = makeWorkspace();
  try {
    const result = runSync(root);
    assert.equal(result.status, 0, result.stderr);

    const generated = readFileSync(join(root, ".codex", "agents", "backend-api.toml"), "utf8");
    assert.match(generated, /name = "backend-api"/);
    assert.match(generated, /description = "Backend técnico — auth, RBAC, emissão oficial"/);
    assert.match(generated, /developer_instructions = """[\s\S]*Paths permitidos \(escrita\): `apps\/api\/\*\*`/);
    assert.match(generated, /Dono único de `apps\/api\/\*\*`\. Implementa workflows de OS\./);
    assert.match(generated, /UI \(→ `web-ui`\)\./);
    assert.doesNotMatch(generated, /^model\s*=/m);
    assert.doesNotMatch(generated, /^paths\s*=/m);
    assert.doesNotMatch(generated, /^sandbox_mode\s*=/m);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("check mode accepts generated Codex agent with CRLF line endings", () => {
  const root = makeWorkspace();
  try {
    const writeResult = runSync(root);
    assert.equal(writeResult.status, 0, writeResult.stderr);

    const codexAgentPath = join(root, ".codex", "agents", "backend-api.toml");
    const generated = readFileSync(codexAgentPath, "utf8");
    writeFileSync(codexAgentPath, generated.replace(/\n/g, "\r\n"));

    const checkResult = runSync(root, ["--check"]);

    assert.equal(checkResult.status, 0, checkResult.stdout + checkResult.stderr);
    assert.match(checkResult.stdout, /sync-agents: 1 agente\(s\) sincronizados/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
