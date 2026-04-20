import assert from "node:assert/strict";
import { test } from "node:test";

import { lintFiles } from "../packages/copy-lint/src/lint";

test("PRD does not contain prohibited regulatory claims", async () => {
  const result = await lintFiles({ paths: ["PRD.md"] });

  assert.deepEqual(
    result.findings.map((finding) => ({
      ruleId: finding.ruleId,
      severity: finding.severity,
      match: finding.match,
    })),
    [],
  );
  assert.equal(result.errors, 0);
});
