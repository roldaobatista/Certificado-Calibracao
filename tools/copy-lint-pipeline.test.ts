import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

type PackageJson = {
  scripts?: Record<string, string>;
};

test("check:all runs the full repository copy-lint gate", () => {
  const pkg = JSON.parse(readFileSync("package.json", "utf8")) as PackageJson;
  const scripts = pkg.scripts ?? {};

  assert.equal(
    scripts["copy-lint:check"],
    "pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts",
  );
  assert.match(scripts["check:all"] ?? "", /(?:^|&&)\s*pnpm copy-lint:check\s*(?:&&|$)/);
});
