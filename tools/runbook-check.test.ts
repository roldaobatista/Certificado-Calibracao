import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkRunbooks } from "./runbook-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-runbooks-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "runbooks"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeRunbook(root: string, fileName: string, id: string) {
  writeFileSync(join(root, "compliance", "runbooks", fileName), [
    "---",
    `id: ${id}`,
    "version: 1",
    "status: approved",
    "owner: product-governance",
    "rto: 4h",
    "rpo: 0",
    "---",
    "",
    `# ${id} — Runbook`,
    "",
    "## Trigger",
    "",
    "Evento de teste.",
    "",
    "## Impacto",
    "",
    "Impacto de teste.",
    "",
    "## Papéis",
    "",
    "- Dispatcher: product-governance",
    "- Executor: operador responsável",
    "",
    "## Passos",
    "",
    "1. Executar contenção.",
    "",
    "## Validação",
    "",
    "1. Rodar verificação aplicável.",
    "",
    "## Evidência",
    "",
    "Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-slug/`.",
    "",
    "## Drill",
    "",
    "Frequência semestral.",
    "",
    "## Revisão",
    "",
    "Revisão anual ou pós-incidente.",
    "",
  ].join("\n"));
}

function writeCompleteRunbookSet(root: string) {
  writeRunbook(root, "r1-kms-key-rotation.md", "R1");
  writeRunbook(root, "r2-audit-hash-chain-divergence.md", "R2");
  writeRunbook(root, "r3-worm-object-lock-violation.md", "R3");
  writeRunbook(root, "r4-normative-package-disaster-recovery.md", "R4");
  mkdirSync(join(root, "compliance", "runbooks", "executions"), { recursive: true });
  writeFileSync(join(root, "compliance", "runbooks", "executions", "README.md"), "# Execuções\n");
  writeFileSync(join(root, "compliance", "runbooks", "drill-schedule.yaml"), [
    "- id: R1",
    "  runbook: compliance/runbooks/r1-kms-key-rotation.md",
    "  cadence: quarterly",
    "  next_due: 2026-07-20",
    "  owner: lgpd-security",
    "  evidence_path: compliance/runbooks/executions/",
    "- id: R2",
    "  runbook: compliance/runbooks/r2-audit-hash-chain-divergence.md",
    "  cadence: semiannual",
    "  next_due: 2026-10-20",
    "  owner: lgpd-security",
    "  evidence_path: compliance/runbooks/executions/",
    "- id: R3",
    "  runbook: compliance/runbooks/r3-worm-object-lock-violation.md",
    "  cadence: semiannual",
    "  next_due: 2026-10-20",
    "  owner: product-governance",
    "  evidence_path: compliance/runbooks/executions/",
    "- id: R4",
    "  runbook: compliance/runbooks/r4-normative-package-disaster-recovery.md",
    "  cadence: semiannual",
    "  next_due: 2026-10-20",
    "  owner: regulator",
    "  evidence_path: compliance/runbooks/executions/",
  ].join("\n"));
}

test("fails when required recovery runbooks are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkRunbooks(root);

    assert.match(result.errors.join("\n"), /RUNBOOK-001/);
    assert.match(result.errors.join("\n"), /r1-kms-key-rotation\.md/);
    assert.match(result.errors.join("\n"), /drill-schedule\.yaml/);
  } finally {
    cleanup();
  }
});

test("fails when drill schedule does not cover every required runbook", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRunbookSet(root);
    writeFileSync(join(root, "compliance", "runbooks", "drill-schedule.yaml"), [
      "- id: R1",
      "  runbook: compliance/runbooks/r1-kms-key-rotation.md",
      "  cadence: quarterly",
      "  next_due: 2026-07-20",
      "  owner: lgpd-security",
      "  evidence_path: compliance/runbooks/executions/",
    ].join("\n"));

    const result = checkRunbooks(root);

    assert.match(result.errors.join("\n"), /RUNBOOK-004/);
    assert.match(result.errors.join("\n"), /R2/);
    assert.match(result.errors.join("\n"), /R3/);
    assert.match(result.errors.join("\n"), /R4/);
  } finally {
    cleanup();
  }
});

test("passes for a complete recovery runbook set", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRunbookSet(root);

    const result = checkRunbooks(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedRunbooks, 4);
    assert.equal(result.checkedDrills, 4);
  } finally {
    cleanup();
  }
});
