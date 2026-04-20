import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { buildCascadePlan, checkReleaseAudits } from "./verification-cascade";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-cascade-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "validation-dossier"), { recursive: true });
  mkdirSync(join(root, "evals", "audit"), { recursive: true });
  mkdirSync(join(root, "evals", "emission"), { recursive: true });
  mkdirSync(join(root, "evals", "docs"), { recursive: true });
  writeFileSync(join(root, "evals", "audit", "hash-chain.test.ts"), "test('audit', () => {});\n");
  writeFileSync(join(root, "evals", "emission", "certificate.test.ts"), "test('emission', () => {});\n");
  writeFileSync(join(root, "evals", "docs", "readme.test.ts"), "test('docs', () => {});\n");
  writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), [
    "- id: REQ-AUDIT",
    "  source: { doc: PRD.md, section: \"§13.6\" }",
    "  description: Audit log",
    "  validation_status: validated",
    "  linked_specs: [specs/audit.md]",
    "  linked_tests: [evals/audit/hash-chain.test.ts]",
    "  evidence_path: compliance/validation-dossier/evidence/REQ-AUDIT/",
    "  owner: db-schema",
    "  criticality: blocker",
    "  critical_paths: [packages/audit-log/**]",
    "- id: REQ-EMISSION",
    "  source: { doc: PRD.md, section: \"§13.3\" }",
    "  description: Emission",
    "  validation_status: validated",
    "  linked_specs: [specs/emission.md]",
    "  linked_tests: [evals/emission/certificate.test.ts]",
    "  evidence_path: compliance/validation-dossier/evidence/REQ-EMISSION/",
    "  owner: backend-api",
    "  criticality: high",
    "  critical_paths: [apps/api/src/domain/emission/**]",
    "- id: REQ-DOC",
    "  source: { doc: PRD.md, section: \"§13.18\" }",
    "  description: Documentation",
    "  validation_status: validated",
    "  linked_specs: [specs/docs.md]",
    "  linked_tests: [evals/docs/readme.test.ts]",
    "  evidence_path: compliance/validation-dossier/evidence/REQ-DOC/",
    "  owner: qa-acceptance",
    "  criticality: medium",
    "  critical_paths: [docs/**]",
  ].join("\n"));
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

test("critical area changes require L4 full regression and snapshot diff", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const plan = buildCascadePlan(root, ["packages/audit-log/src/verify.ts"]);

    assert.equal(plan.requiresFullRegression, true);
    assert.equal(plan.requiresSnapshotDiff, true);
    assert.deepEqual(plan.criticalAreas, ["packages/audit-log/**"]);
    assert.deepEqual(plan.regressionTests, ["evals/audit/hash-chain.test.ts"]);
    assert.match(plan.gates.map((gate) => gate.level).join(","), /L4/);
  } finally {
    cleanup();
  }
});

test("non-critical changes keep L4 full regression and snapshot diff off", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const plan = buildCascadePlan(root, ["docs/README.md"]);

    assert.equal(plan.requiresFullRegression, false);
    assert.equal(plan.requiresSnapshotDiff, false);
    assert.deepEqual(plan.criticalAreas, []);
    assert.deepEqual(plan.regressionTests, []);
  } finally {
    cleanup();
  }
});

test("release audit check requires the three L5 auditor opinions", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const missing = checkReleaseAudits(root, "v0.1.0");

    assert.deepEqual(missing.missing, [
      "compliance/audits/metrology/v0.1.0.md",
      "compliance/audits/legal/v0.1.0.md",
      "compliance/audits/code/v0.1.0.md",
    ]);

    mkdirSync(join(root, "compliance", "audits", "metrology"), { recursive: true });
    mkdirSync(join(root, "compliance", "audits", "legal"), { recursive: true });
    mkdirSync(join(root, "compliance", "audits", "code"), { recursive: true });
    writeFileSync(join(root, "compliance", "audits", "metrology", "v0.1.0.md"), "PASS\n");
    writeFileSync(join(root, "compliance", "audits", "legal", "v0.1.0.md"), "PASS\n");
    writeFileSync(join(root, "compliance", "audits", "code", "v0.1.0.md"), "PASS\n");

    assert.deepEqual(checkReleaseAudits(root, "v0.1.0").missing, []);
  } finally {
    cleanup();
  }
});
