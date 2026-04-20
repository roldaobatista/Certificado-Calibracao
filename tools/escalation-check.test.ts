import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkEscalations } from "./escalation-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-escalations-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "escalations"), { recursive: true });
  mkdirSync(join(root, "adr"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeTiebreakerAdr(root: string) {
  writeFileSync(
    join(root, "adr", "0009-tiebreaker-designation.md"),
    [
      "# ADR 0009 — Designação do tiebreaker",
      "",
      "Status: Aprovado",
      "",
      "O tiebreaker humano único é o Responsável Técnico do Produto.",
      "",
      "Sucessão exige nova ADR aprovada por product-governance.",
      "",
    ].join("\n"),
  );
}

function writeTemplate(root: string) {
  writeFileSync(
    join(root, "compliance", "escalations", "_template.md"),
    [
      "---",
      "id: ESC-YYYY-MM-DD-SLUG",
      "status: open",
      "type: D1",
      "opened_at: 2026-04-20T09:00:00-04:00",
      "trigger: PR ou incidente",
      "agents:",
      "  - regulator",
      "  - metrology-calc",
      "affected_paths:",
      "  - packages/normative-rules/**",
      "tiebreaker_adr: adr/0009-tiebreaker-designation.md",
      "sla: 48h úteis",
      "owner: product-governance",
      "---",
      "",
      "# Escalation ESC-YYYY-MM-DD-SLUG",
      "",
      "## Posições",
      "",
      "### regulator",
      "",
      "Argumento + referência normativa/técnica.",
      "",
      "### metrology-calc",
      "",
      "Argumento + referência.",
      "",
      "## Impacto se não resolvido",
      "",
      "Bloqueio de release, risco regulatório ou dívida técnica.",
      "",
      "## Resolução",
      "",
      "Preencher ao resolver.",
      "",
      "## Assinaturas",
      "",
      "- Nome, papel, 2026-04-20T09:00:00-04:00",
      "",
      "## Aprendizado",
      "",
      "Política/ADR/spec atualizada quando aplicável.",
      "",
    ].join("\n"),
  );
}

function writeReadme(root: string) {
  writeFileSync(
    join(root, "compliance", "escalations", "README.md"),
    [
      "# Escalations",
      "",
      "Registro canônico de divergências D1-D9 descritas em `harness/12-escalation-matrix.md`.",
      "",
      "Entradas com `status: open` não podem ser mergeadas.",
      "",
    ].join("\n"),
  );
}

function writeResolvedEscalation(root: string) {
  writeFileSync(
    join(root, "compliance", "escalations", "2026-04-20-cache-normativo.md"),
    [
      "---",
      "id: ESC-2026-04-20-CACHE-NORMATIVO",
      "status: resolved",
      "type: D2",
      "opened_at: 2026-04-20T09:00:00-04:00",
      "resolved_at: 2026-04-20T11:00:00-04:00",
      "trigger: PR #42",
      "agents:",
      "  - regulator",
      "  - backend-api",
      "affected_paths:",
      "  - apps/api/src/domain/emission/**",
      "  - packages/normative-rules/**",
      "tiebreaker_adr: adr/0009-tiebreaker-designation.md",
      "sla: 48h úteis",
      "owner: product-governance",
      "---",
      "",
      "# Escalation ESC-2026-04-20-CACHE-NORMATIVO",
      "",
      "## Posições",
      "",
      "### regulator",
      "",
      "Decisão normativa de bloqueio deve ser recomputada por emissão.",
      "",
      "### backend-api",
      "",
      "Cache só pode cobrir leitura do pacote normativo vigente.",
      "",
      "## Impacto se não resolvido",
      "",
      "Release fica bloqueada por risco regulatório em emissão.",
      "",
      "## Resolução",
      "",
      "Cache permitido apenas para pacote vigente; decisão de bloqueio é sempre recomputada.",
      "",
      "## Assinaturas",
      "",
      "- Responsável Técnico do Produto, tiebreaker, 2026-04-20T11:00:00-04:00",
      "",
      "## Aprendizado",
      "",
      "Regra incorporada à matriz de escalonamento.",
      "",
    ].join("\n"),
  );
}

function writeCompleteEscalationWorkspace(root: string) {
  writeReadme(root);
  writeTemplate(root);
  writeTiebreakerAdr(root);
  writeResolvedEscalation(root);
}

test("fails when escalation governance artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkEscalations(root);

    assert.match(result.errors.join("\n"), /ESC-001/);
    assert.match(result.errors.join("\n"), /README\.md/);
    assert.match(result.errors.join("\n"), /_template\.md/);
    assert.match(result.errors.join("\n"), /0009-tiebreaker-designation\.md/);
  } finally {
    cleanup();
  }
});

test("fails closed when an escalation is still open", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteEscalationWorkspace(root);
    writeFileSync(
      join(root, "compliance", "escalations", "2026-04-20-open.md"),
      [
        "---",
        "id: ESC-2026-04-20-OPEN",
        "status: open",
        "type: D9",
        "opened_at: 2026-04-20T09:00:00-04:00",
        "trigger: PR #43",
        "agents:",
        "  - metrology-auditor",
        "  - regulator",
        "affected_paths:",
        "  - packages/normative-rules/**",
        "tiebreaker_adr: adr/0009-tiebreaker-designation.md",
        "sla: 48h úteis",
        "owner: product-governance",
        "---",
        "",
        "# Escalation ESC-2026-04-20-OPEN",
        "",
        "## Posições",
        "",
        "### metrology-auditor",
        "",
        "Bloqueio emitido.",
        "",
        "### regulator",
        "",
        "Discordância registrada.",
        "",
        "## Impacto se não resolvido",
        "",
        "Release bloqueada.",
        "",
        "## Resolução",
        "",
        "Pendente.",
        "",
        "## Assinaturas",
        "",
        "- Pendente",
        "",
        "## Aprendizado",
        "",
        "Pendente.",
        "",
      ].join("\n"),
    );

    const result = checkEscalations(root);

    assert.match(result.errors.join("\n"), /ESC-004/);
    assert.match(result.errors.join("\n"), /status: open/);
  } finally {
    cleanup();
  }
});

test("passes for complete resolved escalation governance", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteEscalationWorkspace(root);

    const result = checkEscalations(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedEscalations, 1);
    assert.equal(result.openEscalations, 0);
  } finally {
    cleanup();
  }
});
