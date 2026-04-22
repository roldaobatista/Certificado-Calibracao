import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { lintOwnership } from "./lint.js";

const repoRoot = resolve(fileURLToPath(new URL("../../..", import.meta.url)));
const rulesPath = join(repoRoot, "packages", "ownership-lint", "src", "rules.yaml");

function createWorkspaceFixture() {
  const root = mkdtempSync(join(tmpdir(), "afere-ownership-lint-"));
  mkdirSync(join(root, "apps"), { recursive: true });
  writeFileSync(join(root, "pnpm-workspace.yaml"), "packages:\n  - apps/*\n");
  writeFileSync(join(root, "apps", ".gitkeep"), "");

  return {
    root,
    write(relativePath: string, content: string) {
      const target = join(root, relativePath);
      const directory = resolve(target, "..");
      mkdirSync(directory, { recursive: true });
      writeFileSync(target, content);
      return target;
    },
  };
}

test("paths constraint does not apply web or portal rules to backend files", async () => {
  const fixture = createWorkspaceFixture();

  try {
    fixture.write(
      "apps/api/src/domain/emission/dry-run.ts",
      'import { evaluateStandardEligibility } from "@afere/normative-rules";\n',
    );

    const result = await lintOwnership({
      cwd: fixture.root,
      rulesPath,
      paths: ["apps/api/src/domain/emission/dry-run.ts"],
    });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});

test("paths constraint still flags forbidden web imports inside scoped files", async () => {
  const fixture = createWorkspaceFixture();

  try {
    fixture.write(
      "apps/web/src/page.tsx",
      'import { buildCertificateMeasurementDeclaration } from "@afere/engine-uncertainty";\n',
    );

    const result = await lintOwnership({
      cwd: fixture.root,
      rulesPath,
      paths: ["apps/web/src/page.tsx"],
    });

    assert.equal(result.errors, 1);
    assert.equal(result.findings[0]?.ruleId, "OWN-002");
  } finally {
    rmSync(fixture.root, { recursive: true, force: true });
  }
});
