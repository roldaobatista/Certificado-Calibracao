import assert from "node:assert/strict";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";

const CHECKER_PATH = resolve(process.cwd(), "tools/compliance-structure-check.ts");

async function loadChecker() {
  assert.equal(existsSync(CHECKER_PATH), true, "tools/compliance-structure-check.ts deve existir.");
  return import("./compliance-structure-check");
}

function makeWorkspace() {
  const root = join(tmpdir(), `afere-compliance-structure-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(root, { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeFile(root: string, path: string, text = "# Placeholder\n") {
  const fullPath = join(root, ...path.split("/"));
  mkdirSync(join(fullPath, ".."), { recursive: true });
  writeFileSync(fullPath, text);
}

function writeDir(root: string, path: string) {
  mkdirSync(join(root, ...path.split("/")), { recursive: true });
}

function writeCompleteComplianceTree(root: string) {
  const dirs = [
    "compliance/audits/code",
    "compliance/audits/legal",
    "compliance/audits/metrology",
    "compliance/budget-log",
    "compliance/cloud-agents/attestations",
    "compliance/escalations",
    "compliance/incidents",
    "compliance/legal-opinions",
    "compliance/normative-packages/approved",
    "compliance/normative-packages/releases",
    "compliance/regulator-decisions",
    "compliance/release-norm",
    "compliance/roadmap",
    "compliance/runbooks/executions",
    "compliance/sessions-log",
    "compliance/validation-dossier/evidence",
    "compliance/validation-dossier/findings",
    "compliance/validation-dossier/flake-log",
    "compliance/validation-dossier/releases",
    "compliance/validation-dossier/snapshots",
    "compliance/validation-dossier/snapshots/baseline",
    "compliance/validation-dossier/snapshots/current",
    "compliance/verification-log",
    "compliance/verification-log/issues",
    "compliance/verification-log/issues/drafts",
  ];
  for (const dir of dirs) writeDir(root, dir);

  const files = [
    "compliance/approved-claims.md",
    "compliance/audits/README.md",
    "compliance/budget-log/README.md",
    "compliance/cloud-agents-log.md",
    "compliance/cloud-agents-policy.md",
    "compliance/cloud-agents/policy.yaml",
    "compliance/escalations/README.md",
    "compliance/guardrails.md",
    "compliance/legal-opinions/README.md",
    "compliance/normative-packages/README.md",
    "compliance/normative-packages/releases/manifest.yaml",
    "compliance/regulator-decisions/README.md",
    "compliance/release-norm/README.md",
    "compliance/roadmap/README.md",
    "compliance/roadmap/v1-v5.yaml",
    "compliance/runbooks/README.md",
    "compliance/runbooks/drill-schedule.yaml",
    "compliance/sessions-log/README.md",
    "compliance/validation-dossier/README.md",
    "compliance/validation-dossier/coverage-report.md",
    "compliance/validation-dossier/requirements.yaml",
    "compliance/validation-dossier/snapshots/README.md",
    "compliance/validation-dossier/snapshots/manifest.yaml",
    "compliance/validation-dossier/traceability-matrix.yaml",
    "compliance/verification-log/README.md",
    "compliance/verification-log/_template.yaml",
    "compliance/verification-log/issues/README.md",
    "compliance/verification-log/issues/_template.md",
    "compliance/verification-log/issues/drafts/.gitkeep",
  ];
  for (const file of files) writeFile(root, file);

  writeFile(
    root,
    "compliance/README.md",
    [
      "# compliance/",
      "",
      "- `normative-packages/`",
      "- `validation-dossier/`",
      "- `release-norm/`",
      "- `legal-opinions/`",
      "- `audits/metrology|legal|code/`",
      "- `approved-claims.md`",
      "- `guardrails.md`",
      "- `runbooks/`",
      "- `verification-log/`",
      "- `cloud-agents-policy.md`",
      "- `budget-log/`",
      "- `sessions-log/`",
      "- `roadmap/`",
      "",
    ].join("\n"),
  );
}

test("fails when canonical compliance artifacts are missing", async () => {
  const { checkComplianceStructure } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkComplianceStructure(root);

    assert.match(result.errors.join("\n"), /COMP-001/);
    assert.match(result.errors.join("\n"), /compliance\/README\.md/);
    assert.match(result.errors.join("\n"), /compliance\/validation-dossier\/requirements\.yaml/);
    assert.match(result.errors.join("\n"), /compliance\/release-norm/);
  } finally {
    cleanup();
  }
});

test("fails when compliance README drops canonical references", async () => {
  const { checkComplianceStructure } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteComplianceTree(root);
    writeFile(root, "compliance/README.md", "# compliance/\n\n- `normative-packages/`\n");

    const result = checkComplianceStructure(root);

    assert.match(result.errors.join("\n"), /COMP-002/);
    assert.match(result.errors.join("\n"), /validation-dossier/);
    assert.match(result.errors.join("\n"), /approved-claims\.md/);
  } finally {
    cleanup();
  }
});

test("passes when the canonical compliance tree and README references are present", async () => {
  const { checkComplianceStructure } = await loadChecker();
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteComplianceTree(root);

    const result = checkComplianceStructure(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedArtifacts, 55);
    assert.equal(result.checkedReadmeReferences, 13);
  } finally {
    cleanup();
  }
});

test("wires compliance-structure-check into the root pipeline and pre-commit", () => {
  const packageJson = JSON.parse(readFileSync(resolve(process.cwd(), "package.json"), "utf8"));
  const preCommit = readFileSync(resolve(process.cwd(), ".githooks/pre-commit"), "utf8");

  assert.equal(packageJson.scripts["compliance-structure-check"], "tsx tools/compliance-structure-check.ts");
  assert.match(packageJson.scripts["check:all"], /pnpm compliance-structure-check/);
  assert.match(preCommit, /compliance-structure-check/);
});
