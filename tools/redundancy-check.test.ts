import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { buildRedundancyPlan, checkRedundancy } from "./redundancy-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-redundancy-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "validation-dossier"), { recursive: true });
  mkdirSync(join(root, "evals", "tenancy", "fuzz"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeRequirements(root: string) {
  writeFileSync(join(root, "compliance", "validation-dossier", "requirements.yaml"), [
    "- id: REQ-PRD-13-13-RLS-ISOLATION",
    "  source: { doc: PRD.md, section: \"§13.13\" }",
    "  description: Isolamento RLS",
    "  validation_status: validated",
    "  linked_specs: [specs/0001-harness-compliance-gates.md]",
    "  linked_tests: [evals/tenancy/fuzz/cross-tenant-fuzz.test.ts]",
    "  evidence_path: compliance/validation-dossier/evidence/REQ-PRD-13-13-RLS-ISOLATION/",
    "  owner: db-schema",
    "  criticality: blocker",
    "  critical_paths: [packages/db/**, evals/tenancy/**]",
  ].join("\n"));
}

function writeCompleteRedundancySet(root: string) {
  writeRequirements(root);
  writeFileSync(join(root, "evals", "tenancy", "fuzz", "cross-tenant-fuzz.test.ts"), "test('fuzz', () => {});\n");
  writeFileSync(join(root, "evals", "property-config.yaml"), [
    "- req: REQ-PRD-13-13-RLS-ISOLATION",
    "  criticality: blocker",
    "  N: 500",
    "  canonical_seeds: [3735928559, 3405691582, 324508639]",
    "  test: evals/tenancy/fuzz/cross-tenant-fuzz.test.ts",
    "  command: pnpm test:fuzz",
    "  report_path: evals/tenancy/fuzz/reports/",
  ].join("\n"));
  mkdirSync(join(root, "compliance", "validation-dossier", "flake-log"), { recursive: true });
  writeFileSync(join(root, "compliance", "validation-dossier", "flake-log", "README.md"), "# Flake log\n");
  mkdirSync(join(root, "compliance", "regulator-decisions"), { recursive: true });
  writeFileSync(join(root, "compliance", "regulator-decisions", "README.md"), "# Decisoes regulatorias\n");
  mkdirSync(join(root, ".github", "workflows"), { recursive: true });
  writeFileSync(join(root, ".github", "workflows", "nightly-flake-gate.yml"), [
    "name: nightly-flake-gate",
    "on:",
    "  schedule:",
    "    - cron: '0 6 * * *'",
    "jobs:",
    "  flake-gate:",
    "    runs-on: ubuntu-latest",
    "    steps:",
    "      - run: pnpm flake-gate",
  ].join("\n"));
}

test("fails when P0-11 redundancy artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkRedundancy(root);

    assert.match(result.errors.join("\n"), /REDUNDANCY-001/);
    assert.match(result.errors.join("\n"), /evals\/property-config\.yaml/);
    assert.match(result.errors.join("\n"), /flake-log\/README\.md/);
    assert.match(result.errors.join("\n"), /regulator-decisions\/README\.md/);
  } finally {
    cleanup();
  }
});

test("fails when property seed policy is weaker than criticality floor", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRedundancySet(root);
    writeFileSync(join(root, "evals", "property-config.yaml"), [
      "- req: REQ-PRD-13-13-RLS-ISOLATION",
      "  criticality: blocker",
      "  N: 100",
      "  canonical_seeds: []",
      "  test: evals/tenancy/fuzz/cross-tenant-fuzz.test.ts",
      "  command: pnpm test:fuzz",
      "  report_path: evals/tenancy/fuzz/reports/",
    ].join("\n"));

    const result = checkRedundancy(root);

    assert.match(result.errors.join("\n"), /REDUNDANCY-003/);
    assert.match(result.errors.join("\n"), /REQ-PRD-13-13-RLS-ISOLATION/);
    assert.match(result.errors.join("\n"), /N minimo 500/);
    assert.match(result.errors.join("\n"), /REDUNDANCY-004/);
  } finally {
    cleanup();
  }
});

test("passes for a complete P0-11 redundancy baseline", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRedundancySet(root);

    const result = checkRedundancy(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedProperties, 1);
    assert.equal(result.checkedFlakeGate, true);
    assert.equal(result.checkedRegulatoryRecords, true);
  } finally {
    cleanup();
  }
});

test("plans double regulatory checks and adjacent reviews for critical paths", () => {
  const plan = buildRedundancyPlan([
    "packages/normative-rules/src/profiles.ts",
    "packages/audit-log/src/verify.ts",
  ]);

  assert.equal(plan.requiresRegulatoryDoubleCheck, true);
  assert.deepEqual(plan.regulatoryDoubleCheckReasons, [
    "packages/normative-rules/** exige duas passagens do regulator.",
  ]);
  assert.deepEqual(plan.requiredReviewAgents, ["lgpd-security", "metrology-calc", "qa-acceptance"]);
});
