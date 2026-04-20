import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import {
  buildDossierArtifacts,
  parsePrdAcceptanceCriteria,
  selectCriticalRegressionTests,
  validateDossier,
} from "./validation-dossier";

function makeWorkspace() {
  const root = mkdtempSync(join(tmpdir(), "afere-dossier-"));
  mkdirSync(join(root, "compliance", "validation-dossier", "evidence"), { recursive: true });
  mkdirSync(join(root, "specs"), { recursive: true });
  mkdirSync(join(root, "evals"), { recursive: true });
  writeFileSync(join(root, "PRD.md"), [
    "# PRD",
    "",
    "## 13. Critérios de aceite do MVP",
    "",
    "1. ✅ Primeiro critério coberto.",
    "2. ✅ Segundo critério ainda sem requisito.",
    "",
    "---",
    "",
    "## 14. Riscos",
  ].join("\n"));
  writeFileSync(join(root, "specs", "0001-primeiro.md"), "# Spec\n");
  writeFileSync(join(root, "evals", "primeiro.test.ts"), "test('placeholder', () => {});\n");
  mkdirSync(join(root, "compliance", "validation-dossier", "evidence", "REQ-PRD-13-01"), {
    recursive: true,
  });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

test("parses PRD section 13 acceptance criteria into stable numbers", () => {
  const criteria = parsePrdAcceptanceCriteria([
    "## 13. Critérios de aceite do MVP",
    "",
    "1. ✅ Uma calibração funciona.",
    "2. ✅ O sistema bloqueia padrão vencido.",
    "",
    "## 14. Riscos",
  ].join("\n"));

  assert.deepEqual(criteria, [
    { number: 1, section: "§13.1", text: "Uma calibração funciona." },
    { number: 2, section: "§13.2", text: "O sistema bloqueia padrão vencido." },
  ]);
});

test("validates requirements and reports PRD coverage gaps without failing non-strict mode", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), [
      "- id: REQ-PRD-13-01",
      "  source:",
      "    doc: PRD.md",
      "    section: \"§13.1\"",
      "  description: Primeiro critério coberto",
      "  linked_specs:",
      "    - specs/0001-primeiro.md",
      "  linked_tests:",
      "    - evals/primeiro.test.ts",
      "  evidence_path: compliance/validation-dossier/evidence/REQ-PRD-13-01/",
      "  owner: qa-acceptance",
      "  criticality: blocker",
    ].join("\n"));

    const result = validateDossier({ root, checkTraceability: false, strictPrdCoverage: false });

    assert.deepEqual(result.errors, []);
    assert.equal(result.coverage.coveredPrdCriteria, 1);
    assert.equal(result.coverage.totalPrdCriteria, 2);
    assert.match(result.warnings.join("\n"), /§13\.2/);
  } finally {
    cleanup();
  }
});

test("strict PRD coverage fails when section 13 acceptance criteria are not mapped", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), "[]\n");

    const result = validateDossier({ root, checkTraceability: false, strictPrdCoverage: true });

    assert.match(result.errors.join("\n"), /REQ-PRD-001/);
    assert.match(result.errors.join("\n"), /§13\.1/);
    assert.match(result.errors.join("\n"), /§13\.2/);
  } finally {
    cleanup();
  }
});

test("detects stale traceability matrix", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), [
      "- id: REQ-PRD-13-01",
      "  source:",
      "    doc: PRD.md",
      "    section: \"§13.1\"",
      "  description: Primeiro critério coberto",
      "  linked_specs:",
      "    - specs/0001-primeiro.md",
      "  linked_tests:",
      "    - evals/primeiro.test.ts",
      "  evidence_path: compliance/validation-dossier/evidence/REQ-PRD-13-01/",
      "  owner: qa-acceptance",
      "  criticality: blocker",
    ].join("\n"));

    const artifacts = buildDossierArtifacts(root);
    writeFileSync(
      join(root, "compliance", "validation-dossier", "traceability-matrix.yaml"),
      artifacts.traceabilityMatrixYaml,
    );
    assert.equal(validateDossier({ root, checkTraceability: true }).errors.length, 0);

    writeFileSync(
      join(root, "compliance", "validation-dossier", "traceability-matrix.yaml"),
      "stale: true\n",
    );

    const result = validateDossier({ root, checkTraceability: true });
    assert.match(result.errors.join("\n"), /TRACE-001/);
  } finally {
    cleanup();
  }
});

test("flags duplicate requirements and missing linked test files", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), [
      "- id: REQ-DUP",
      "  source: { doc: PRD.md, section: \"§13.1\" }",
      "  description: Duplicado A",
      "  linked_specs: [specs/0001-primeiro.md]",
      "  linked_tests: [evals/missing.test.ts]",
      "  evidence_path: compliance/validation-dossier/evidence/REQ-PRD-13-01/",
      "  owner: qa-acceptance",
      "  criticality: blocker",
      "- id: REQ-DUP",
      "  source: { doc: PRD.md, section: \"§13.1\" }",
      "  description: Duplicado B",
      "  linked_specs: [specs/0001-primeiro.md]",
      "  linked_tests: [evals/primeiro.test.ts]",
      "  evidence_path: compliance/validation-dossier/evidence/REQ-PRD-13-01/",
      "  owner: qa-acceptance",
      "  criticality: blocker",
    ].join("\n"));

    const result = validateDossier({ root, checkTraceability: false });

    assert.match(result.errors.join("\n"), /REQ-002/);
    assert.match(result.errors.join("\n"), /REQ-006/);
    assert.match(result.errors.join("\n"), /evals\/missing\.test\.ts/);
  } finally {
    cleanup();
  }
});

test("selects full-regression tests for blocker or high requirements in touched critical paths", () => {
  const tests = selectCriticalRegressionTests(
    [
      {
        id: "REQ-AUDIT",
        source: { doc: "PRD.md", section: "§13.19" },
        description: "Audit log imutável",
        linked_specs: ["specs/audit.md"],
        linked_tests: ["packages/audit-log/src/verify.test.ts"],
        evidence_path: "compliance/validation-dossier/evidence/REQ-AUDIT/",
        owner: "db-schema",
        criticality: "blocker",
        critical_paths: ["packages/audit-log/**"],
      },
      {
        id: "REQ-DOC",
        source: { doc: "PRD.md", section: "§13.19" },
        description: "Documentação",
        linked_specs: ["specs/doc.md"],
        linked_tests: ["evals/doc.test.ts"],
        evidence_path: "compliance/validation-dossier/evidence/REQ-DOC/",
        owner: "qa-acceptance",
        criticality: "medium",
        critical_paths: ["packages/audit-log/**"],
      },
    ],
    ["packages/audit-log/src/verify.ts"],
  );

  assert.deepEqual(tests, ["packages/audit-log/src/verify.test.ts"]);
});
