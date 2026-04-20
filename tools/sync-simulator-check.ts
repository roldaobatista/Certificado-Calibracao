import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

const ROOT = "evals/sync-simulator";
const REQUIRED_FILES = [
  `${ROOT}/README.md`,
  `${ROOT}/engine/simulator.ts`,
  `${ROOT}/sync-simulator.test.ts`,
  `${ROOT}/scenarios/canonical.yaml`,
  `${ROOT}/seeds/canonical/seeds.yaml`,
  `${ROOT}/reports/README.md`,
] as const;
const REQUIRED_PROPERTIES = ["convergence", "hash-chain-integrity", "signature-lock", "idempotency"] as const;
const REQUIRED_SCENARIOS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"] as const;

type ScenarioManifest = {
  scenarios?: Array<{ id?: string; expected?: string }>;
};

export type SyncSimulatorCheckResult = {
  errors: string[];
  checkedScenarios: number;
  checkedProperties: number;
};

export function checkSyncSimulator(root = process.cwd()): SyncSimulatorCheckResult {
  const errors: string[] = [];
  for (const file of REQUIRED_FILES) {
    if (!existsSync(resolve(root, file))) {
      errors.push(`SYNC-SIM-001: artefato obrigatório ausente: ${file}.`);
    }
  }

  const checkedProperties = checkProperties(root, errors);
  const checkedScenarios = checkScenarioManifest(root, errors);
  checkSeeds(root, errors);
  checkReadmeCoverage(root, errors);

  return { errors, checkedScenarios, checkedProperties };
}

function checkProperties(root: string, errors: string[]) {
  let checked = 0;
  for (const property of REQUIRED_PROPERTIES) {
    const path = `${ROOT}/properties/${property}.md`;
    if (!existsSync(resolve(root, path))) {
      errors.push(`SYNC-SIM-002: propriedade obrigatória ausente: ${path}.`);
      continue;
    }
    checked += 1;
  }
  return checked;
}

function checkScenarioManifest(root: string, errors: string[]) {
  const path = resolve(root, `${ROOT}/scenarios/canonical.yaml`);
  if (!existsSync(path)) return 0;

  const parsed = yamlLoad(readFileSync(path, "utf8")) as ScenarioManifest | undefined;
  const scenarios = Array.isArray(parsed?.scenarios) ? parsed.scenarios : [];
  if (!Array.isArray(parsed?.scenarios)) {
    errors.push(`SYNC-SIM-003: ${ROOT}/scenarios/canonical.yaml deve declarar scenarios.`);
    return 0;
  }

  const ids = scenarios.map((scenario) => scenario.id ?? "<sem id>");
  for (const required of REQUIRED_SCENARIOS) {
    if (!ids.includes(required)) {
      errors.push(`SYNC-SIM-003: cenário canônico ausente: ${required}.`);
    }
  }
  if (ids.join(",") !== REQUIRED_SCENARIOS.join(",")) {
    errors.push(`SYNC-SIM-003: cenários devem estar em ordem ${REQUIRED_SCENARIOS.join(" -> ")}.`);
  }

  for (const scenario of scenarios) {
    if (!scenario.expected) {
      errors.push(`SYNC-SIM-003: cenário ${scenario.id ?? "<sem id>"} sem expected.`);
    }
  }

  return scenarios.length;
}

function checkSeeds(root: string, errors: string[]) {
  const path = resolve(root, `${ROOT}/seeds/canonical/seeds.yaml`);
  if (!existsSync(path)) return;

  const parsed = yamlLoad(readFileSync(path, "utf8"));
  if (!Array.isArray(parsed) || parsed.length < 3) {
    errors.push(`SYNC-SIM-004: seeds canônicos devem conter pelo menos 3 seeds.`);
  }
  for (const seed of Array.isArray(parsed) ? parsed : []) {
    if (!Number.isInteger(seed)) {
      errors.push(`SYNC-SIM-004: seed inválido: ${String(seed)}.`);
    }
  }
}

function checkReadmeCoverage(root: string, errors: string[]) {
  const path = resolve(root, `${ROOT}/README.md`);
  if (!existsSync(path)) return;
  const readme = readFileSync(path, "utf8");
  for (const scenario of REQUIRED_SCENARIOS) {
    if (!readme.includes(scenario)) {
      errors.push(`SYNC-SIM-005: README não menciona ${scenario}.`);
    }
  }
}

function runCli() {
  const result = checkSyncSimulator();
  console.log(
    `sync-simulator-check: ${result.checkedScenarios}/8 cenário(s), ${result.checkedProperties}/4 propriedade(s).`,
  );
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
