import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { dump as yamlDump, load as yamlLoad } from "js-yaml";

const REQUIREMENTS_PATH = "compliance/validation-dossier/requirements.yaml";
const TRACEABILITY_PATH = "compliance/validation-dossier/traceability-matrix.yaml";
const COVERAGE_REPORT_PATH = "compliance/validation-dossier/coverage-report.md";

const CRITICALITIES = new Set(["blocker", "high", "medium", "low"]);

export type Criticality = "blocker" | "high" | "medium" | "low";

export type Requirement = {
  id: string;
  source: {
    doc: string;
    section: string;
  };
  description: string;
  linked_specs: string[];
  linked_tests: string[];
  evidence_path: string;
  owner: string;
  criticality: Criticality;
  critical_paths?: string[];
};

export type PrdAcceptanceCriterion = {
  number: number;
  section: string;
  text: string;
};

type ValidateOptions = {
  root?: string;
  checkTraceability?: boolean;
  strictPrdCoverage?: boolean;
};

type CoverageSummary = {
  totalPrdCriteria: number;
  coveredPrdCriteria: number;
  missingPrdSections: string[];
};

export type ValidationResult = {
  errors: string[];
  warnings: string[];
  coverage: CoverageSummary;
};

type TraceabilityCriterion = {
  section: string;
  text: string;
  status: "covered" | "missing";
  requirement_ids: string[];
  linked_tests: string[];
};

type TraceabilityMatrix = {
  generated_by: string;
  sources: {
    requirements: string;
    prd: string;
  };
  prd_section_13: {
    total: number;
    covered: number;
    missing: number;
  };
  criteria: TraceabilityCriterion[];
  requirements: Array<{
    id: string;
    source: string;
    criticality: Criticality;
    owner: string;
    linked_specs: string[];
    linked_tests: string[];
    evidence_path: string;
    critical_paths: string[];
  }>;
};

export function parsePrdAcceptanceCriteria(markdown: string): PrdAcceptanceCriterion[] {
  const lines = markdown.split(/\r?\n/);
  const criteria: PrdAcceptanceCriterion[] = [];
  let inSection13 = false;

  for (const line of lines) {
    if (/^##\s+13\./.test(line)) {
      inSection13 = true;
      continue;
    }

    if (inSection13 && /^##\s+\d+\./.test(line)) {
      break;
    }

    if (!inSection13) continue;

    const match = line.match(/^\s*(\d+)\.\s*(.*)$/u);
    if (!match) continue;

    const number = Number(match[1]);
    const text = match[2].replace(/^\u2705\s*/u, "").trim();
    criteria.push({ number, section: `§13.${number}`, text });
  }

  return criteria;
}

export function loadRequirements(root = process.cwd()): Requirement[] {
  const requirementsFile = resolve(root, REQUIREMENTS_PATH);
  if (!existsSync(requirementsFile)) return [];

  const parsed = yamlLoad(readFileSync(requirementsFile, "utf8"));
  if (!Array.isArray(parsed)) {
    throw new Error(`${REQUIREMENTS_PATH} deve conter uma lista YAML.`);
  }

  return parsed as Requirement[];
}

export function buildDossierArtifacts(root = process.cwd()) {
  const resolvedRoot = resolve(root);
  const requirements = loadRequirements(resolvedRoot);
  const prdFile = resolve(resolvedRoot, "PRD.md");
  const prdCriteria = existsSync(prdFile)
    ? parsePrdAcceptanceCriteria(readFileSync(prdFile, "utf8"))
    : [];
  const traceabilityMatrix = buildTraceabilityMatrix(requirements, prdCriteria);

  return {
    requirements,
    prdCriteria,
    traceabilityMatrix,
    traceabilityMatrixYaml: renderTraceabilityMatrix(traceabilityMatrix),
    coverageReportMd: renderCoverageReport(traceabilityMatrix),
  };
}

export function validateDossier(options: ValidateOptions = {}): ValidationResult {
  const root = resolve(options.root ?? process.cwd());
  const checkTraceability = options.checkTraceability ?? true;
  const strictPrdCoverage = options.strictPrdCoverage ?? false;
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!existsSync(resolve(root, REQUIREMENTS_PATH))) {
    errors.push(`REQ-001: ${REQUIREMENTS_PATH} não encontrado.`);
  }

  let artifacts;
  try {
    artifacts = buildDossierArtifacts(root);
  } catch (error) {
    errors.push(`REQ-000: ${(error as Error).message}`);
    return {
      errors,
      warnings,
      coverage: { totalPrdCriteria: 0, coveredPrdCriteria: 0, missingPrdSections: [] },
    };
  }

  const seenIds = new Set<string>();
  for (const requirement of artifacts.requirements) {
    const label = requirement?.id ?? "<sem id>";

    if (!requirement?.id) errors.push("REQ-003: requisito sem campo obrigatório id.");
    if (requirement?.id && seenIds.has(requirement.id)) {
      errors.push(`REQ-002: requisito duplicado ${requirement.id}.`);
    }
    if (requirement?.id) seenIds.add(requirement.id);

    if (!requirement?.source?.doc || !requirement?.source?.section) {
      errors.push(`REQ-003: ${label} sem source.doc/source.section.`);
    }
    if (!requirement?.description) errors.push(`REQ-003: ${label} sem description.`);
    if (!Array.isArray(requirement?.linked_specs) || requirement.linked_specs.length === 0) {
      errors.push(`REQ-003: ${label} sem linked_specs.`);
    }
    if (!Array.isArray(requirement?.linked_tests) || requirement.linked_tests.length === 0) {
      errors.push(`REQ-003: ${label} sem linked_tests.`);
    }
    if (!requirement?.evidence_path) errors.push(`REQ-003: ${label} sem evidence_path.`);
    if (!requirement?.owner) errors.push(`REQ-003: ${label} sem owner.`);
    if (!CRITICALITIES.has(requirement?.criticality)) {
      errors.push(`REQ-004: ${label} tem criticality inválida: ${requirement?.criticality}.`);
    }

    if (requirement?.source?.doc) {
      assertPathExists(root, requirement.source.doc, `REQ-005: ${label} source.doc`, errors);
    }
    for (const spec of requirement?.linked_specs ?? []) {
      assertPathExists(root, spec, `REQ-005: ${label} linked_specs`, errors);
    }
    for (const testPath of requirement?.linked_tests ?? []) {
      assertPathExists(root, testPath, `REQ-006: ${label} linked_tests`, errors);
    }

    if (
      requirement?.evidence_path &&
      !normalizePath(requirement.evidence_path).startsWith("compliance/validation-dossier/evidence/")
    ) {
      errors.push(`REQ-007: ${label} evidence_path fora de compliance/validation-dossier/evidence/.`);
    }
  }

  const coverage = summarizeCoverage(artifacts.traceabilityMatrix);
  for (const section of coverage.missingPrdSections) {
    const message = `REQ-PRD-001: PRD ${section} não possui requisito em ${REQUIREMENTS_PATH}.`;
    if (strictPrdCoverage) errors.push(message);
    else warnings.push(message);
  }

  if (checkTraceability) {
    const traceabilityFile = resolve(root, TRACEABILITY_PATH);
    if (!existsSync(traceabilityFile)) {
      errors.push(`TRACE-001: ${TRACEABILITY_PATH} não encontrado. Rode pnpm validation-dossier:write.`);
    } else {
      const current = readFileSync(traceabilityFile, "utf8").trimEnd();
      const expected = artifacts.traceabilityMatrixYaml.trimEnd();
      if (current !== expected) {
        errors.push(`TRACE-001: ${TRACEABILITY_PATH} está desatualizado. Rode pnpm validation-dossier:write.`);
      }
    }
  }

  return { errors, warnings, coverage };
}

export function buildTraceabilityMatrix(
  requirements: Requirement[],
  prdCriteria: PrdAcceptanceCriterion[],
): TraceabilityMatrix {
  const requirementsBySection = new Map<string, Requirement[]>();
  for (const requirement of requirements) {
    const section = requirement?.source?.section;
    if (!section) continue;
    const existing = requirementsBySection.get(section) ?? [];
    existing.push(requirement);
    requirementsBySection.set(section, existing);
  }

  const criteria = prdCriteria.map((criterion) => {
    const linkedRequirements = requirementsBySection.get(criterion.section) ?? [];
    const linkedTests = uniqueSorted(linkedRequirements.flatMap((requirement) => requirement.linked_tests ?? []));
    return {
      section: criterion.section,
      text: criterion.text,
      status: linkedRequirements.length > 0 ? "covered" : "missing",
      requirement_ids: linkedRequirements.map((requirement) => requirement.id).sort(),
      linked_tests: linkedTests,
    } satisfies TraceabilityCriterion;
  });

  return {
    generated_by: "tools/validation-dossier.ts",
    sources: {
      requirements: REQUIREMENTS_PATH,
      prd: "PRD.md",
    },
    prd_section_13: {
      total: criteria.length,
      covered: criteria.filter((criterion) => criterion.status === "covered").length,
      missing: criteria.filter((criterion) => criterion.status === "missing").length,
    },
    criteria,
    requirements: requirements
      .map((requirement) => ({
        id: requirement.id,
        source: `${requirement.source.doc} ${requirement.source.section}`,
        criticality: requirement.criticality,
        owner: requirement.owner,
        linked_specs: requirement.linked_specs ?? [],
        linked_tests: requirement.linked_tests ?? [],
        evidence_path: requirement.evidence_path,
        critical_paths: requirement.critical_paths ?? [],
      }))
      .sort((left, right) => left.id.localeCompare(right.id)),
  };
}

export function renderTraceabilityMatrix(matrix: TraceabilityMatrix): string {
  return `${yamlDump(matrix, {
    lineWidth: 120,
    noRefs: true,
    sortKeys: false,
  }).trimEnd()}\n`;
}

export function renderCoverageReport(matrix: TraceabilityMatrix): string {
  const missing = matrix.criteria.filter((criterion) => criterion.status === "missing");
  const covered = matrix.criteria.filter((criterion) => criterion.status === "covered");

  return [
    "# Coverage Report",
    "",
    "> Gerado por `pnpm validation-dossier:write`. Não editar manualmente.",
    "",
    "## PRD §13",
    "",
    `- Total de critérios: ${matrix.prd_section_13.total}`,
    `- Critérios com requisito mapeado: ${matrix.prd_section_13.covered}`,
    `- Critérios pendentes: ${matrix.prd_section_13.missing}`,
    "",
    "## Cobertos",
    "",
    ...renderCriterionLines(covered),
    "",
    "## Pendentes",
    "",
    ...renderCriterionLines(missing),
    "",
  ].join("\n");
}

export function writeDossierArtifacts(root = process.cwd()) {
  const artifacts = buildDossierArtifacts(root);
  writeFileSync(resolve(root, TRACEABILITY_PATH), artifacts.traceabilityMatrixYaml);
  writeFileSync(resolve(root, COVERAGE_REPORT_PATH), artifacts.coverageReportMd);
  return artifacts;
}

export function selectCriticalRegressionTests(
  requirements: Requirement[],
  changedFiles: string[],
): string[] {
  const normalizedChangedFiles = changedFiles.map(normalizePath);
  const selected = requirements
    .filter((requirement) => requirement.criticality === "blocker" || requirement.criticality === "high")
    .filter((requirement) => {
      const paths = requirement.critical_paths ?? [];
      return paths.some((pattern) =>
        normalizedChangedFiles.some((changedFile) => matchesPathPattern(changedFile, pattern)),
      );
    })
    .flatMap((requirement) => requirement.linked_tests ?? []);

  return uniqueSorted(selected);
}

function assertPathExists(root: string, path: string, label: string, errors: string[]) {
  if (!existsSync(resolve(root, path))) {
    errors.push(`${label} aponta para arquivo inexistente: ${path}.`);
  }
}

function summarizeCoverage(matrix: TraceabilityMatrix): CoverageSummary {
  return {
    totalPrdCriteria: matrix.prd_section_13.total,
    coveredPrdCriteria: matrix.prd_section_13.covered,
    missingPrdSections: matrix.criteria
      .filter((criterion) => criterion.status === "missing")
      .map((criterion) => criterion.section),
  };
}

function renderCriterionLines(criteria: TraceabilityCriterion[]) {
  if (criteria.length === 0) return ["- Nenhum."];
  return criteria.map((criterion) => {
    const requirements = criterion.requirement_ids.length > 0
      ? criterion.requirement_ids.join(", ")
      : "sem requisito";
    return `- ${criterion.section}: ${requirements} — ${criterion.text}`;
  });
}

function matchesPathPattern(path: string, pattern: string) {
  const normalizedPattern = normalizePath(pattern);
  if (normalizedPattern.endsWith("/**")) {
    return path.startsWith(normalizedPattern.slice(0, -3));
  }
  if (normalizedPattern.includes("*")) {
    const regex = new RegExp(`^${escapeRegex(normalizedPattern).replace(/\\\*/g, ".*")}$`);
    return regex.test(path);
  }
  return path === normalizedPattern;
}

function normalizePath(path: string) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "");
}

function uniqueSorted(values: string[]) {
  return [...new Set(values)].sort();
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function findWorkspaceRoot(startDir: string) {
  let dir = resolve(startDir);
  while (dir !== dirname(dir)) {
    if (existsSync(resolve(dir, "pnpm-workspace.yaml"))) return dir;
    dir = dirname(dir);
  }
  return resolve(startDir);
}

function parseCliArgs(argv: string[]) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "check";
  let root = findWorkspaceRoot(process.cwd());
  const changedFiles: string[] = [];
  let json = false;
  let quiet = false;
  let strictPrdCoverage = false;
  let write = command === "generate";

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--root") {
      root = resolve(args[++index]);
    } else if (arg === "--write") {
      write = true;
    } else if (arg === "--json") {
      json = true;
    } else if (arg === "--quiet") {
      quiet = true;
    } else if (arg === "--strict-prd") {
      strictPrdCoverage = true;
    } else if (arg === "--changed") {
      changedFiles.push(args[++index]);
    } else {
      changedFiles.push(arg);
    }
  }

  return { command, root, changedFiles, json, quiet, strictPrdCoverage, write };
}

function runCli() {
  const { command, root, changedFiles, json, quiet, strictPrdCoverage, write } = parseCliArgs(process.argv.slice(2));

  if (command === "critical-tests") {
    const tests = selectCriticalRegressionTests(loadRequirements(root), changedFiles);
    if (json) console.log(JSON.stringify({ tests }, null, 2));
    else console.log(tests.join("\n"));
    return tests.length > 0 ? 0 : 0;
  }

  if (command !== "check" && command !== "generate") {
    console.error("Uso: validation-dossier [check|generate|critical-tests] [--write] [--strict-prd] [--json] [--quiet]");
    return 2;
  }

  if (write) {
    writeDossierArtifacts(root);
  }

  const result = validateDossier({
    root,
    checkTraceability: true,
    strictPrdCoverage,
  });

  if (json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(
      `validation-dossier: ${result.coverage.coveredPrdCriteria}/${result.coverage.totalPrdCriteria} critérios do PRD §13 mapeados.`,
    );
    if (!quiet) {
      for (const warning of result.warnings) console.warn(`WARN ${warning}`);
    }
    for (const error of result.errors) console.error(`ERROR ${error}`);
  }

  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
