import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import {
  isEmitCertDryCliEntry,
  parseEmitCertDryArgs,
  renderEmissionDryRunReport,
  resolveEmitCertDryScenario,
  runEmitCertDryCli,
} from "./emit-cert-dry";

type PackageJson = {
  scripts?: Record<string, string>;
};

const testDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(testDir, "..");
const cliPath = join(repoRoot, "tools", "emit-cert-dry.ts");
const tsxLoaderUrl = pathToFileURL(join(repoRoot, "node_modules", "tsx", "dist", "loader.mjs")).href;

function runCli(args: string[]) {
  return spawnSync(process.execPath, ["--import", tsxLoaderUrl, cliPath, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
  });
}

test("parses canonical profile selection for emit-cert-dry", () => {
  const options = parseEmitCertDryArgs(["--profile", "C", "--json"]);

  assert.deepEqual(options, {
    profile: "C",
    json: true,
  });
});

test("resolves the default ready scenario for profile B", () => {
  const scenarioPromise = resolveEmitCertDryScenario({ profile: "B" });

  return scenarioPromise.then((scenario) => {
    assert.equal(scenario.id, "type-b-ready");
    assert.equal(scenario.result.status, "ready");
  });
});

test("renders a human-readable report with checks and artifacts", () => {
  const scenarioPromise = resolveEmitCertDryScenario({ profile: "A" });

  return scenarioPromise.then((scenario) => {
    const report = renderEmissionDryRunReport(scenario);

    assert.match(report, /Scenario: type-a-suppressed/);
    assert.match(report, /Status: READY/);
    assert.match(report, /Checks:/);
    assert.match(report, /\[OK\] Politica regulatoria/);
  });
});

test("returns exit code 1 for a blocked dry-run profile", () => {
  const resultPromise = runEmitCertDryCli(["--profile", "C"]);

  return resultPromise.then((result) => {
    assert.equal(result.exitCode, 1);
    assert.match(result.output, /Status: BLOCKED/);
  });
});

test("package.json exposes the emit-cert-dry script", () => {
  const pkg = JSON.parse(readFileSync("package.json", "utf8")) as PackageJson;

  assert.equal(pkg.scripts?.["emit-cert-dry"], "tsx tools/emit-cert-dry.ts");
});

test("detects direct CLI execution from argv[1]", () => {
  const previousArgv = process.argv;

  try {
    process.argv = [process.execPath, cliPath];
    assert.equal(isEmitCertDryCliEntry(pathToFileURL(cliPath).href), true);
  } finally {
    process.argv = previousArgv;
  }
});

test("CLI prints the dry-run report for a ready profile", () => {
  const result = runCli(["--profile", "B"]);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Scenario: type-b-ready/);
  assert.match(result.stdout, /Status: READY/);
});

test("CLI prints blockers to stderr for a blocked profile", () => {
  const result = runCli(["--profile", "C"]);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Scenario: type-c-blocked/);
  assert.match(result.stderr, /Status: BLOCKED/);
});
