import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

import {
  buildCascadePlan,
  buildVerificationIssueDrafts,
  checkReleaseAudits,
  checkVerificationCascade,
  planVerificationIssueReconciliation,
  writeVerificationIssueDrafts,
} from "./verification-cascade";

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

function writeIssueDraftArtifacts(root: string) {
  const issuesRoot = join(root, "compliance", "verification-log", "issues");
  mkdirSync(join(issuesRoot, "drafts"), { recursive: true });
  writeFileSync(join(issuesRoot, "README.md"), "# Verification issues\n");
  writeFileSync(
    join(issuesRoot, "_template.md"),
    [
      "---",
      "issue_type: {{issue_type}}",
      "status: open",
      "severity: {{severity}}",
      "labels:",
      "{{labels_yaml}}",
      "---",
      "",
      "# {{issue_title}}",
      "",
      "## Contexto",
      "{{context_list}}",
      "",
      "## Evidencia",
      "{{evidence_list}}",
      "",
      "## Reauditoria obrigatoria",
      "{{reaudit_list}}",
      "",
      "## Fechamento",
      "{{closing_list}}",
      "",
    ].join("\n"),
  );
}

function writeVerificationLogTemplate(root: string) {
  writeFileSync(
    join(root, "compliance", "verification-log", "_template.yaml"),
    [
      "- date: 2026-04-22",
      "  trigger: L3 correction in critical flow",
      "  ac_changed: false",
      "  reqs_changed: false",
      "  propagated_up:",
      "    - L1/REQ-EXAMPLE",
      "  propagated_down:",
      "    - L4/full-regression",
      "  re_audits_completed:",
      "    - L4: 2026-04-23 via pnpm check:all",
      "",
    ].join("\n"),
  );
}

function writeVerificationLog(
  root: string,
  reqId: string,
  entries: Array<{
    date: string;
    trigger: string;
    ac_changed?: boolean;
    reqs_changed?: boolean;
    propagated_up?: string[];
    propagated_down?: string[];
    re_audits_completed?: string[];
  }>,
) {
  writeFileSync(
    join(root, "compliance", "verification-log", `${reqId}.yaml`),
    entries
      .map((entry) =>
        [
          `- date: "${entry.date}"`,
          `  trigger: "${entry.trigger}"`,
          `  ac_changed: ${entry.ac_changed ? "true" : "false"}`,
          `  reqs_changed: ${entry.reqs_changed ? "true" : "false"}`,
          "  propagated_up:",
          ...(entry.propagated_up ?? []).map((value) => `    - "${value}"`),
          "  propagated_down:",
          ...(entry.propagated_down ?? []).map((value) => `    - "${value}"`),
          "  re_audits_completed:",
          ...(entry.re_audits_completed ?? []).map((value) => `    - "${value}"`),
        ].join("\n"),
      )
      .join("\n"),
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
    writeVerificationLogTemplate(root);

    const result = checkVerificationCascade(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedSnapshots, 3);
    assert.deepEqual(result.checkedProfiles, ["A", "B", "C"]);
  } finally {
    cleanup();
  }
});

test("verification cascade produces no issue drafts when there are no issue-worthy findings", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    process.env.AFERE_CASCADE_TODAY = "2026-04-20";
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);

    const drafts = buildVerificationIssueDrafts(root, checkVerificationCascade(root));

    assert.deepEqual(drafts, []);
  } finally {
    delete process.env.AFERE_CASCADE_TODAY;
    cleanup();
  }
});

test("verification cascade writes deterministic issue drafts for snapshot diffs", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    process.env.AFERE_CASCADE_TODAY = "2026-04-20";
    writeSnapshotDossier(root, { diffCurrentId: "profile-b-minimal" });
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);

    const result = checkVerificationCascade(root);
    const drafts = buildVerificationIssueDrafts(root, result);
    const written = writeVerificationIssueDrafts(root, drafts);

    assert.equal(drafts.length, 1);
    assert.match(drafts[0].title, /profile-b-minimal/);
    assert.match(drafts[0].body, /CASCADE-003/);
    assert.match(drafts[0].body, /baseline/);
    assert.equal(
      drafts[0].path,
      "compliance/verification-log/issues/drafts/2026-04-20-snapshot-diff-profile-b-minimal.md",
    );
    assert.deepEqual(written, [drafts[0].path]);
    const draftBody = readFileSync(resolve(root, drafts[0].path), "utf8");
    assert.match(draftBody, /profile-b-minimal/);
    assert.match(draftBody, /status: open/);
    assert.match(draftBody, /regulator/);
  } finally {
    delete process.env.AFERE_CASCADE_TODAY;
    cleanup();
  }
});

test("verification cascade flags spec review after three consecutive AC or REQ corrections", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
      {
        date: "2026-04-20",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-20 via pnpm check:all"],
      },
    ]);

    const result = checkVerificationCascade(root);

    assert.match(result.errors.join("\n"), /CASCADE-007/);
    assert.match(result.errors.join("\n"), /REQ-EMISSION/);
    assert.match(result.findings.map((finding) => finding.code).join(","), /CASCADE-007/);
  } finally {
    cleanup();
  }
});

test("verification cascade accepts repeated corrections once L1 reauditoria is registered", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
      {
        date: "2026-04-20",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: [
          "L1/REQ-EMISSION: 2026-04-20 by regulator + qa-acceptance",
          "L4: 2026-04-20 via pnpm check:all",
        ],
      },
    ]);

    const result = checkVerificationCascade(root);

    assert.doesNotMatch(result.errors.join("\n"), /CASCADE-007/);
  } finally {
    cleanup();
  }
});

test("verification cascade writes deterministic issue drafts for spec-review-flag", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    process.env.AFERE_CASCADE_TODAY = "2026-04-20";
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
      {
        date: "2026-04-20",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-20 via pnpm check:all"],
      },
    ]);

    const result = checkVerificationCascade(root);
    const drafts = buildVerificationIssueDrafts(root, result);
    const draft = drafts.find((entry) => entry.slug === "spec-review-flag-req-emission");

    assert.ok(draft);
    assert.equal(
      draft.path,
      "compliance/verification-log/issues/drafts/2026-04-20-spec-review-flag-req-emission.md",
    );
    assert.match(draft.title, /REQ-EMISSION/);
    assert.match(draft.body, /CASCADE-007/);
    assert.match(draft.body, /3 correcoes consecutivas/);
    assert.match(draft.body, /L1\/REQ-EMISSION/);
  } finally {
    delete process.env.AFERE_CASCADE_TODAY;
    cleanup();
  }
});

test("verification cascade emits independent drafts for snapshot diff and spec-review-flag in the same run", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    process.env.AFERE_CASCADE_TODAY = "2026-04-20";
    writeSnapshotDossier(root, { diffCurrentId: "profile-b-minimal" });
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
      {
        date: "2026-04-20",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-20 via pnpm check:all"],
      },
    ]);

    const drafts = buildVerificationIssueDrafts(root, checkVerificationCascade(root));

    assert.deepEqual(
      drafts.map((draft) => draft.slug).sort(),
      ["snapshot-diff-profile-b-minimal", "spec-review-flag-req-emission"],
    );
  } finally {
    delete process.env.AFERE_CASCADE_TODAY;
    cleanup();
  }
});

test("verification cascade flags epic review after three consecutive corrections across specs in the same epic", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
    ]);
    writeVerificationLog(root, "REQ-DOC", [
      {
        date: "2026-04-20",
        trigger: "L3 correction in portal flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-DOC", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-20 via pnpm check:all"],
      },
    ]);

    const result = checkVerificationCascade(root);

    assert.match(result.errors.join("\n"), /CASCADE-008/);
    assert.match(result.errors.join("\n"), /EPIC-EMISSION/);
    assert.match(result.findings.map((finding) => finding.code).join(","), /CASCADE-008/);
  } finally {
    cleanup();
  }
});

test("verification cascade accepts epic corrections once L0 reauditoria is registered", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
    ]);
    writeVerificationLog(root, "REQ-DOC", [
      {
        date: "2026-04-20",
        trigger: "L3 correction in portal flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-DOC", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: [
          "L0/EPIC-EMISSION: 2026-04-20 by regulator + product-governance",
          "L4: 2026-04-20 via pnpm check:all",
        ],
      },
    ]);

    const result = checkVerificationCascade(root);

    assert.doesNotMatch(result.errors.join("\n"), /CASCADE-008/);
  } finally {
    cleanup();
  }
});

test("verification cascade writes deterministic issue drafts for epic-review-flag", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    process.env.AFERE_CASCADE_TODAY = "2026-04-20";
    writeSnapshotDossier(root);
    writeIssueDraftArtifacts(root);
    writeVerificationLogTemplate(root);
    writeVerificationLog(root, "REQ-EMISSION", [
      {
        date: "2026-04-18",
        trigger: "L3 correction in emission flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-18 via pnpm check:all"],
      },
      {
        date: "2026-04-19",
        trigger: "L3 correction in emission flow",
        reqs_changed: true,
        propagated_up: ["L1/REQ-EMISSION", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-19 via pnpm check:all"],
      },
    ]);
    writeVerificationLog(root, "REQ-DOC", [
      {
        date: "2026-04-20",
        trigger: "L3 correction in portal flow",
        ac_changed: true,
        propagated_up: ["L1/REQ-DOC", "L0/EPIC-EMISSION"],
        propagated_down: ["L4/full-regression"],
        re_audits_completed: ["L4: 2026-04-20 via pnpm check:all"],
      },
    ]);

    const result = checkVerificationCascade(root);
    const drafts = buildVerificationIssueDrafts(root, result);
    const draft = drafts.find((entry) => entry.slug === "epic-review-flag-epic-emission");

    assert.ok(draft);
    assert.equal(
      draft.path,
      "compliance/verification-log/issues/drafts/2026-04-20-epic-review-flag-epic-emission.md",
    );
    assert.match(draft.title, /EPIC-EMISSION/);
    assert.match(draft.body, /CASCADE-008/);
    assert.match(draft.body, /2 spec/);
    assert.match(draft.body, /REQ-EMISSION/);
    assert.match(draft.body, /REQ-DOC/);
  } finally {
    delete process.env.AFERE_CASCADE_TODAY;
    cleanup();
  }
});

test("verification issue reconciliation plans create reopen keep and close actions", () => {
  const plan = planVerificationIssueReconciliation(
    [
      {
        slug: "snapshot-diff-profile-b-minimal",
        path: "compliance/verification-log/issues/drafts/2026-04-20-snapshot-diff-profile-b-minimal.md",
        title: "P0-10 snapshot-diff blocker: profile-b-minimal",
        body: "---\nissue_type: verification-cascade-snapshot-diff\n---",
        labels: ["compliance", "verification-cascade", "snapshot-diff", "blocker"],
      },
      {
        slug: "epic-review-flag-epic-emission",
        path: "compliance/verification-log/issues/drafts/2026-04-20-epic-review-flag-epic-emission.md",
        title: "P0-10 epic-review-flag: EPIC-EMISSION precisa re-auditoria L0",
        body: "---\nissue_type: verification-cascade-epic-review-flag\n---",
        labels: ["compliance", "verification-cascade", "epic-review-flag", "l0-reaudit"],
      },
      {
        slug: "spec-review-flag-req-emission",
        path: "compliance/verification-log/issues/drafts/2026-04-20-spec-review-flag-req-emission.md",
        title: "P0-10 spec-review-flag: REQ-EMISSION precisa re-auditoria L1",
        body: "---\nissue_type: verification-cascade-spec-review-flag\n---",
        labels: ["compliance", "verification-cascade", "spec-review-flag", "l1-reaudit"],
      },
    ],
    [
      {
        number: 10,
        title: "P0-10 snapshot-diff blocker: profile-b-minimal",
        body: "---\nissue_type: verification-cascade-snapshot-diff\n---",
        labels: ["verification-cascade", "snapshot-diff"],
        state: "open",
      },
      {
        number: 11,
        title: "P0-10 spec-review-flag: REQ-EMISSION precisa re-auditoria L1",
        body: "---\nissue_type: verification-cascade-spec-review-flag\n---",
        labels: ["verification-cascade", "spec-review-flag"],
        state: "closed",
      },
      {
        number: 12,
        title: "P0-10 spec-review-flag: REQ-DOC precisa re-auditoria L1",
        body: "---\nissue_type: verification-cascade-spec-review-flag\n---",
        labels: ["verification-cascade", "spec-review-flag"],
        state: "open",
      },
      {
        number: 13,
        title: "Discussão manual fora da automação",
        body: "sem frontmatter canônico",
        labels: ["verification-cascade"],
        state: "open",
      },
    ],
  );

  assert.deepEqual(plan.keepOpen.map((issue) => issue.number), [10]);
  assert.deepEqual(plan.reopen.map((issue) => issue.number), [11]);
  assert.deepEqual(plan.create.map((draft) => draft.title), [
    "P0-10 epic-review-flag: EPIC-EMISSION precisa re-auditoria L0",
  ]);
  assert.deepEqual(plan.close.map((issue) => issue.number), [12]);
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
  const workflow = readFileSync(resolve(process.cwd(), ".github", "workflows", "required-gates.yml"), "utf8");

  assert.equal(packageJson.scripts["snapshot-diff-check"], "tsx tools/verification-cascade.ts check");
  assert.equal(packageJson.scripts["verification-cascade:issue-drafts"], "tsx tools/verification-cascade.ts issue-drafts");
  assert.match(packageJson.scripts["check:all"], /pnpm snapshot-diff-check/);
  assert.match(preCommit, /snapshot-diff-check/);
  assert.match(workflow, /Generate verification issue drafts/);
  assert.match(workflow, /if: \$\{\{ always\(\) \}\}/);
  assert.match(workflow, /planVerificationIssueReconciliation/);
  assert.match(workflow, /Closed verification issue/);
  assert.match(workflow, /Reopened verification issue/);
});
