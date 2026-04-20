import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

import { buildCascadePlan, checkReleaseAudits, checkVerificationCascade } from "./verification-cascade";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-cascade-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "validation-dossier"), { recursive: true });
  mkdirSync(join(root, "evals", "audit"), { recursive: true });
  mkdirSync(join(root, "evals", "emission"), { recursive: true });
  mkdirSync(join(root, "evals", "docs"), { recursive: true });
  mkdirSync(join(root, "compliance", "verification-log"), { recursive: true });
  writeFileSync(join(root, "compliance", "verification-log", "README.md"), "# Verification log\n");
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

function writeSnapshotDossier(root: string, options: { diffCurrentId?: string } = {}) {
  const baselineDir = join(root, "compliance", "validation-dossier", "snapshots", "baseline");
  const currentDir = join(root, "compliance", "validation-dossier", "snapshots", "current");
  mkdirSync(baselineDir, { recursive: true });
  mkdirSync(currentDir, { recursive: true });

  const snapshots = [
    { id: "profile-a-minimal", profile: "A" },
    { id: "profile-b-minimal", profile: "B" },
    { id: "profile-c-minimal", profile: "C" },
  ];

  const manifestEntries: string[] = [];
  for (const snapshot of snapshots) {
    const baseline = snapshotText(snapshot.profile, snapshot.id);
    const current =
      options.diffCurrentId === snapshot.id
        ? baseline.replace("status: approved", "status: changed")
        : baseline;
    const baselinePath = `compliance/validation-dossier/snapshots/baseline/${snapshot.id}.txt`;
    const currentPath = `compliance/validation-dossier/snapshots/current/${snapshot.id}.txt`;
    writeFileSync(join(root, ...baselinePath.split("/")), baseline);
    writeFileSync(join(root, ...currentPath.split("/")), current);
    manifestEntries.push(
      [
        `  - id: ${snapshot.id}`,
        `    profile: ${snapshot.profile}`,
        `    baseline_path: ${baselinePath}`,
        `    current_path: ${currentPath}`,
        `    sha256: ${sha256(baseline)}`,
        "    renderer: dogfood-text-v1",
        "    requirement_refs: [REQ-EMISSION]",
      ].join("\n"),
    );
  }

  writeFileSync(
    join(root, "compliance", "validation-dossier", "snapshots", "manifest.yaml"),
    [
      "version: 1",
      "source: harness/05-guardrails.md",
      "policy:",
      "  profiles_required: [A, B, C]",
      "  snapshots_per_profile: 1",
      "  fail_on_diff: true",
      "  approval_required_for_baseline_update: [regulator, product-governance]",
      "snapshots:",
      ...manifestEntries,
      "",
    ].join("\n"),
  );
}

function snapshotText(profile: string, id: string) {
  return [
    `snapshot: ${id}`,
    `profile: ${profile}`,
    "certificate: canonical calibration certificate",
    "status: approved",
    "",
  ].join("\n");
}

function sha256(text: string) {
  return createHash("sha256").update(text).digest("hex");
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

test("verification cascade fails when snapshot manifest is absent", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkVerificationCascade(root);

    assert.match(result.errors.join("\n"), /CASCADE-002/);
    assert.match(result.errors.join("\n"), /compliance\/validation-dossier\/snapshots\/manifest\.yaml/);
    assert.equal(result.checkedSnapshots, 0);
  } finally {
    cleanup();
  }
});

test("verification cascade fails when current snapshot differs from baseline", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root, { diffCurrentId: "profile-b-minimal" });

    const result = checkVerificationCascade(root);

    assert.match(result.errors.join("\n"), /CASCADE-003/);
    assert.match(result.errors.join("\n"), /profile-b-minimal/);
    assert.equal(result.checkedSnapshots, 3);
  } finally {
    cleanup();
  }
});

test("verification cascade passes with canonical snapshot hashes for profiles A, B and C", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root);

    const result = checkVerificationCascade(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedSnapshots, 3);
    assert.deepEqual(result.checkedProfiles, ["A", "B", "C"]);
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

test("wires snapshot diff into the root pipeline and pre-commit", () => {
  const packageJson = JSON.parse(readFileSync(resolve(process.cwd(), "package.json"), "utf8"));
  const preCommit = readFileSync(resolve(process.cwd(), ".githooks/pre-commit"), "utf8");

  assert.equal(packageJson.scripts["snapshot-diff-check"], "tsx tools/verification-cascade.ts check");
  assert.match(packageJson.scripts["check:all"], /pnpm snapshot-diff-check/);
  assert.match(preCommit, /snapshot-diff-check/);
});
