import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { buildHarnessDashboard, checkHarnessDashboard, writeHarnessDashboard } from "./harness-dashboard";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-harness-dashboard-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "harness"), { recursive: true });
  mkdirSync(join(root, "compliance", "validation-dossier"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeFixture(root: string) {
  writeFileSync(
    join(root, "harness", "STATUS.md"),
    [
      "# STATUS — Checklist",
      "",
      "## P0 — Hard blockers",
      "",
      "| ID | Correção | Arquivo | Status |",
      "|----|----------|---------|--------|",
      "| P0-1 | Backend | [02](./02.md) | [~] Em implementação |",
      "| P0-2 | Budgets | [11](./11.md) | [✓] Implementado |",
      "",
      "## P1 — Estrutural",
      "",
      "| ID | Correção | Arquivo | Status |",
      "|----|----------|---------|--------|",
      "| P1-1 | Sync | [08](./08.md) | [~] Em implementação |",
      "",
      "## P2 — Refinamento",
      "",
      "| ID | Correção | Onde | Status |",
      "|----|----------|------|--------|",
      "| P2-3 | Dashboard | pendente | [ ] Não iniciado |",
      "",
    ].join("\n"),
  );

  writeFileSync(
    join(root, "package.json"),
    JSON.stringify(
      {
        scripts: {
          "check:all": "pnpm typecheck && pnpm test:tools && pnpm slash-commands-check && pnpm harness-dashboard:check",
          "slash-commands-check": "tsx tools/slash-commands-check.ts",
          "harness-dashboard:check": "tsx tools/harness-dashboard.ts check",
        },
      },
      null,
      2,
    ),
  );

  writeFileSync(
    join(root, "compliance", "validation-dossier", "coverage-report.md"),
    [
      "# Coverage Report",
      "",
      "- Total de critérios: 22",
      "- Critérios com requisito mapeado: 22",
      "- Critérios validados por teste ativo: 3",
      "- Critérios sem requisito mapeado: 0",
      "",
    ].join("\n"),
  );
}

test("builds a deterministic dashboard from harness status and gates", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFixture(root);

    const dashboard = buildHarnessDashboard(root);

    assert.match(dashboard.markdown, /# Harness Dashboard/);
    assert.match(dashboard.markdown, /P0\s+\|\s+2\s+\|\s+1\s+\|\s+1/);
    assert.match(dashboard.markdown, /P2-3/);
    assert.match(dashboard.markdown, /slash-commands-check/);
    assert.match(dashboard.markdown, /22\/22 mapeados/);
    assert.equal(dashboard.items.length, 4);
  } finally {
    cleanup();
  }
});

test("check mode fails when dashboard is missing or stale", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFixture(root);

    const missing = checkHarnessDashboard(root);
    assert.match(missing.errors.join("\n"), /DASH-001/);

    writeFileSync(join(root, "compliance", "harness-dashboard.md"), "stale\n");
    const stale = checkHarnessDashboard(root);
    assert.match(stale.errors.join("\n"), /DASH-002/);
  } finally {
    cleanup();
  }
});

test("write mode creates a dashboard accepted by check mode", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFixture(root);

    writeHarnessDashboard(root);

    const result = checkHarnessDashboard(root);
    assert.deepEqual(result.errors, []);
    assert.equal(result.itemCount, 4);
  } finally {
    cleanup();
  }
});
