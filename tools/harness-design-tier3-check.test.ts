import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkHarnessDesignTier3 } from "./harness-design-tier3-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-tier3-design-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(root, { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

test("fails for legacy backlog-drain Tier 3 wording", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(
      join(root, "HARNESS_DESIGN.md"),
      [
        "# Harness",
        "",
        "### 2.1 Três camadas (tier model 2026)",
        "",
        "| Camada | Uso | Ferramentas |",
        "|--------|-----|-------------|",
        "| **Tier 3 — Cloud agents** | Drain de *backlog* overnight (bugs Sev-3, refactors mecânicos). | Claude Code Web |",
        "",
        "### 2.2 Orquestrador",
        "",
      ].join("\n"),
    );

    const result = checkHarnessDesignTier3(root);

    assert.match(result.errors.join("\n"), /TIER3-003/);
    assert.match(result.errors.join("\n"), /TIER3-006/);
  } finally {
    cleanup();
  }
});

test("passes when Tier 3 is constrained by P1-2 policy and attestation", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(
      join(root, "HARNESS_DESIGN.md"),
      [
        "# Harness",
        "",
        "### 2.1 Três camadas (tier model 2026)",
        "",
        "| Camada | Uso | Ferramentas |",
        "|--------|-----|-------------|",
        "| **Tier 3 — Cloud agents** | Somente tarefas low-risk aprovadas pela política P1-2: docs, UI puro allowlisted e fixtures sintéticas; exige attestation verificável, revisão humana e product-governance. | Claude Code Web |",
        "",
        "Tier 3 não é fila geral de backlog. Ver `harness/09-cloud-agents-policy.md` e `compliance/cloud-agents/policy.yaml`.",
        "",
        "### 2.2 Orquestrador",
        "",
      ].join("\n"),
    );

    const result = checkHarnessDesignTier3(root);

    assert.deepEqual(result.errors, []);
  } finally {
    cleanup();
  }
});
