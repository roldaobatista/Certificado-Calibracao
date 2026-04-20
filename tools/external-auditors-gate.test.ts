import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkExternalAuditors, checkReleaseAuditorOpinions } from "./external-auditors-gate";

const AUDITORS = [
  {
    name: "metrology-auditor",
    auditDir: "metrology",
    allowed: ["compliance/audits/metrology/**"],
  },
  {
    name: "legal-counsel",
    auditDir: "legal",
    allowed: ["compliance/audits/legal/**", "compliance/legal-opinions/**"],
  },
  {
    name: "senior-reviewer",
    auditDir: "code",
    allowed: ["compliance/audits/code/**"],
  },
] as const;

function makeWorkspace() {
  const root = join(tmpdir(), `afere-external-auditors-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, ".claude", "agents"), { recursive: true });
  mkdirSync(join(root, "compliance", "audits"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeAgent(root: string, auditor: (typeof AUDITORS)[number], allowed = auditor.allowed) {
  writeFileSync(
    join(root, ".claude", "agents", `${auditor.name}.md`),
    [
      "---",
      `name: ${auditor.name}`,
      "description: auditor externo",
      "model: opus",
      "tools: [Read, Grep, Glob, Bash]",
      "---",
      "",
      "## Mandato",
      "",
      "Auditor externo com parecer vinculante e bloqueio de release.",
      "",
      "## Paths permitidos (escrita)",
      "",
      ...allowed.map((path) => `- \`${path}\``),
      "",
      "## Paths bloqueados",
      "",
      "- Todo código de aplicação.",
      "",
      "## Formato de parecer",
      "",
      "```yaml",
      "---",
      `auditor: ${auditor.name}`,
      "release: <versao>",
      "verdict: PASS | FAIL | PASS_WITH_FINDINGS",
      "findings: [<lista>]",
      "blockers: [<lista>]",
      "date: <ISO>",
      "---",
      "```",
      "",
    ].join("\n"),
  );
}

function writeAuditTemplates(root: string) {
  writeFileSync(
    join(root, "compliance", "audits", "README.md"),
    [
      "# Audits",
      "",
      "Pareceres dos 3 auditores externos: metrology-auditor, legal-counsel e senior-reviewer.",
      "",
    ].join("\n"),
  );

  for (const auditor of AUDITORS) {
    mkdirSync(join(root, "compliance", "audits", auditor.auditDir), { recursive: true });
    writeFileSync(
      join(root, "compliance", "audits", auditor.auditDir, "README.md"),
      [`# ${auditor.auditDir}`, "", `Owner: ${auditor.name}`, ""].join("\n"),
    );
    writeFileSync(
      join(root, "compliance", "audits", auditor.auditDir, "_template.md"),
      [
        "---",
        `auditor: ${auditor.name}`,
        "release: <versao>",
        "verdict: PASS",
        "findings: []",
        "blockers: []",
        "date: 2026-04-20T09:00:00-04:00",
        "---",
        "",
        `# Parecer ${auditor.name}`,
        "",
        "## Escopo",
        "",
        "Release auditada.",
        "",
        "## Evidência revisada",
        "",
        "- Gates L4 verdes.",
        "",
        "## Achados",
        "",
        "- Nenhum.",
        "",
        "## Veredito",
        "",
        "PASS.",
        "",
      ].join("\n"),
    );
  }

  mkdirSync(join(root, "compliance", "audits", "escalations"), { recursive: true });
  writeFileSync(
    join(root, "compliance", "audits", "escalations", "README.md"),
    [
      "# Escalations",
      "",
      "Briefings para os 5 casos-limite que exigem humano real.",
      "",
      "- Auditoria CGCRE agendada",
      "- Processo judicial aberto",
      "- Incidente LGPD com dados vazados",
      "- Acidente metrológico",
      "- Reclamação formal em órgão regulador",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(root, "compliance", "audits", "escalations", "_template.md"),
    [
      "---",
      "case: incidente-lgpd",
      "requires_human: true",
      "status: open",
      "date: 2026-04-20T09:00:00-04:00",
      "recommended_specialist: advogado LGPD",
      "---",
      "",
      "# Briefing de escalonamento humano",
      "",
      "## Caso-limite",
      "",
      "Incidente LGPD com dados vazados.",
      "",
      "## Evidência",
      "",
      "- Evidência objetiva.",
      "",
      "## Recomendação",
      "",
      "Contratar humano especialista.",
      "",
    ].join("\n"),
  );
}

function writeCompleteAuditorWorkspace(root: string) {
  for (const auditor of AUDITORS) writeAgent(root, auditor);
  writeAuditTemplates(root);
}

function writeOpinion(root: string, auditDir: string, auditor: string, release: string, verdict = "PASS", blockers: string[] = []) {
  writeFileSync(
    join(root, "compliance", "audits", auditDir, `${release}.md`),
    [
      "---",
      `auditor: ${auditor}`,
      `release: ${release}`,
      `verdict: ${verdict}`,
      "findings: []",
      `blockers: [${blockers.map((blocker) => `"${blocker}"`).join(", ")}]`,
      "date: 2026-04-20T09:00:00-04:00",
      "---",
      "",
      `# Parecer ${auditor}`,
      "",
      "## Escopo",
      "",
      "Release auditada.",
      "",
      "## Evidência revisada",
      "",
      "- Gates L4 verdes.",
      "",
      "## Achados",
      "",
      "- Nenhum.",
      "",
      "## Veredito",
      "",
      verdict,
      "",
    ].join("\n"),
  );
}

test("fails when external auditor governance artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkExternalAuditors(root);

    assert.match(result.errors.join("\n"), /AUDITOR-001/);
    assert.match(result.errors.join("\n"), /metrology-auditor\.md/);
    assert.match(result.errors.join("\n"), /compliance\/audits\/metrology\/_template\.md/);
    assert.match(result.errors.join("\n"), /compliance\/audits\/escalations\/_template\.md/);
  } finally {
    cleanup();
  }
});

test("fails when an external auditor can write audited source paths", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteAuditorWorkspace(root);
    writeAgent(root, AUDITORS[2], ["compliance/audits/code/**", "packages/audit-log/**"]);

    const result = checkExternalAuditors(root);

    assert.match(result.errors.join("\n"), /AUDITOR-003/);
    assert.match(result.errors.join("\n"), /senior-reviewer/);
    assert.match(result.errors.join("\n"), /packages\/audit-log/);
  } finally {
    cleanup();
  }
});

test("passes for complete external auditor governance artifacts", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteAuditorWorkspace(root);

    const result = checkExternalAuditors(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedAuditors, 3);
    assert.equal(result.checkedTemplates, 4);
  } finally {
    cleanup();
  }
});

test("accepts annotated legal-opinion paths and non-file PR review permissions", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteAuditorWorkspace(root);
    writeFileSync(
      join(root, ".claude", "agents", "legal-counsel.md"),
      [
        "---",
        "name: legal-counsel",
        "description: auditor jurídico",
        "model: opus",
        "tools: [Read, Grep, Glob, Bash]",
        "---",
        "",
        "## Paths permitidos (escrita)",
        "",
        "- `compliance/audits/legal/**`",
        "- `compliance/legal-opinions/**` (co-autoria com `lgpd-security`)",
        "",
      ].join("\n"),
    );
    writeFileSync(
      join(root, ".claude", "agents", "senior-reviewer.md"),
      [
        "---",
        "name: senior-reviewer",
        "description: auditor de código",
        "model: opus",
        "tools: [Read, Grep, Glob, Bash]",
        "---",
        "",
        "## Paths permitidos (escrita)",
        "",
        "- `compliance/audits/code/**`",
        "- Comentários e reviews de PR (via `gh pr review`).",
        "",
      ].join("\n"),
    );

    const result = checkExternalAuditors(root);

    assert.deepEqual(result.errors, []);
  } finally {
    cleanup();
  }
});

test("release opinions require the three auditors and block FAIL verdicts", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteAuditorWorkspace(root);
    const missing = checkReleaseAuditorOpinions(root, "v0.1.0");
    assert.deepEqual(missing.missing, [
      "compliance/audits/metrology/v0.1.0.md",
      "compliance/audits/legal/v0.1.0.md",
      "compliance/audits/code/v0.1.0.md",
    ]);

    writeOpinion(root, "metrology", "metrology-auditor", "v0.1.0");
    writeOpinion(root, "legal", "legal-counsel", "v0.1.0", "FAIL", ["risco jurídico alto"]);
    writeOpinion(root, "code", "senior-reviewer", "v0.1.0");

    const blocked = checkReleaseAuditorOpinions(root, "v0.1.0");

    assert.deepEqual(blocked.missing, []);
    assert.match(blocked.errors.join("\n"), /AUDITOR-006/);
    assert.match(blocked.errors.join("\n"), /legal-counsel/);

    writeOpinion(root, "legal", "legal-counsel", "v0.1.0", "PASS_WITH_FINDINGS");
    assert.deepEqual(checkReleaseAuditorOpinions(root, "v0.1.0").errors, []);
  } finally {
    cleanup();
  }
});
