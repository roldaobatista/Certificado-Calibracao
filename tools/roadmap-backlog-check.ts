import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

import { loadRequirements } from "./validation-dossier";

const ROADMAP_BACKLOG_YAML = "compliance/roadmap/execution-backlog.yaml";
const ROADMAP_YAML = "compliance/roadmap/v1-v5.yaml";
const ROADMAP_README = "compliance/roadmap/README.md";
const HARNESS_ROADMAP = "harness/10-roadmap.md";
const REQUIREMENTS_PATH = "compliance/validation-dossier/requirements.yaml";
const ALLOWED_WINDOWS = ["now", "next", "later"] as const;
const EXPECTED_POLICY_FLAGS = [
  "foundation_first",
  "backlog_item_does_not_close_slice",
  "slice_gate_still_required",
  "planning_windows_are_advisory",
] as const;

type RoadmapBacklogDocument = {
  version?: number;
  source?: string;
  roadmap_path?: string;
  policy?: Record<string, unknown>;
  items?: RoadmapBacklogItem[];
};

type RoadmapBacklogItem = {
  id?: string;
  slice?: string;
  planning_window?: string;
  title?: string;
  depends_on?: string[];
  primary_agents?: string[];
  linked_requirements?: string[];
  objective?: string;
  deliverables?: string[];
  done_when?: string[];
};

type RoadmapDocument = {
  slices?: Array<{
    id?: string;
    linked_requirements?: string[];
  }>;
};

export type RoadmapBacklogCheckResult = {
  errors: string[];
  checkedItems: number;
};

export function checkRoadmapBacklog(root = process.cwd()): RoadmapBacklogCheckResult {
  const errors: string[] = [];

  for (const path of [ROADMAP_BACKLOG_YAML, ROADMAP_YAML, ROADMAP_README, HARNESS_ROADMAP]) {
    if (!existsSync(resolve(root, path))) {
      errors.push(`BACKLOG-001: artefato obrigatório ausente: ${path}.`);
    }
  }

  const backlog = loadBacklog(root, errors);
  const roadmap = loadRoadmap(root, errors);

  if (backlog) {
    checkBacklogDocument(backlog, errors);
    checkDocumentationCoverage(root, errors);
  }

  if (backlog && roadmap) {
    checkItemsAgainstRoadmap(root, backlog, roadmap, errors);
  }

  return {
    errors,
    checkedItems: Array.isArray(backlog?.items) ? backlog.items.length : 0,
  };
}

function loadBacklog(root: string, errors: string[]) {
  const path = resolve(root, ROADMAP_BACKLOG_YAML);
  if (!existsSync(path)) return undefined;

  try {
    const parsed = yamlLoad(readFileSync(path, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      errors.push(`BACKLOG-002: ${ROADMAP_BACKLOG_YAML} deve conter um objeto YAML.`);
      return undefined;
    }
    return parsed as RoadmapBacklogDocument;
  } catch (error) {
    errors.push(`BACKLOG-002: falha ao carregar ${ROADMAP_BACKLOG_YAML}: ${(error as Error).message}`);
    return undefined;
  }
}

function loadRoadmap(root: string, errors: string[]) {
  const path = resolve(root, ROADMAP_YAML);
  if (!existsSync(path)) return undefined;

  try {
    const parsed = yamlLoad(readFileSync(path, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      errors.push(`BACKLOG-004: ${ROADMAP_YAML} deve conter um objeto YAML válido.`);
      return undefined;
    }
    return parsed as RoadmapDocument;
  } catch (error) {
    errors.push(`BACKLOG-004: falha ao carregar ${ROADMAP_YAML}: ${(error as Error).message}`);
    return undefined;
  }
}

function checkBacklogDocument(backlog: RoadmapBacklogDocument, errors: string[]) {
  if (backlog.version !== 1) {
    errors.push(`BACKLOG-002: ${ROADMAP_BACKLOG_YAML} deve declarar version: 1.`);
  }
  if (backlog.source !== HARNESS_ROADMAP) {
    errors.push(`BACKLOG-002: ${ROADMAP_BACKLOG_YAML} deve apontar source: ${HARNESS_ROADMAP}.`);
  }
  if (backlog.roadmap_path !== ROADMAP_YAML) {
    errors.push(`BACKLOG-002: ${ROADMAP_BACKLOG_YAML} deve apontar roadmap_path: ${ROADMAP_YAML}.`);
  }

  for (const flag of EXPECTED_POLICY_FLAGS) {
    if (backlog.policy?.[flag] !== true) {
      errors.push(`BACKLOG-002: policy.${flag} deve ser true.`);
    }
  }

  if (!Array.isArray(backlog.items) || backlog.items.length === 0) {
    errors.push(`BACKLOG-003: ${ROADMAP_BACKLOG_YAML} deve declarar items.`);
    return;
  }

  const ids = new Set<string>();
  let previousWindowRank = -1;
  let previousKey: [number, number] | undefined;

  backlog.items.forEach((item, index) => {
    const label = item.id ?? `item[${index}]`;

    for (const field of ["id", "slice", "planning_window", "title", "objective"] as const) {
      if (!item[field]) {
        errors.push(`BACKLOG-003: ${label} sem campo obrigatório ${field}.`);
      }
    }

    if (!Array.isArray(item.depends_on)) {
      errors.push(`BACKLOG-003: ${label} deve declarar depends_on como lista.`);
    }
    if (!Array.isArray(item.primary_agents) || item.primary_agents.length === 0) {
      errors.push(`BACKLOG-003: ${label} deve declarar primary_agents com pelo menos 1 item.`);
    }
    if (!Array.isArray(item.linked_requirements)) {
      errors.push(`BACKLOG-003: ${label} deve declarar linked_requirements, mesmo quando vazio.`);
    }
    if (!Array.isArray(item.deliverables) || item.deliverables.length < 2) {
      errors.push(`BACKLOG-003: ${label} deve declarar deliverables com pelo menos 2 itens.`);
    }
    if (!Array.isArray(item.done_when) || item.done_when.length < 2) {
      errors.push(`BACKLOG-003: ${label} deve declarar done_when com pelo menos 2 itens.`);
    }

    if (!item.id || !item.slice) {
      return;
    }

    if (ids.has(item.id)) {
      errors.push(`BACKLOG-003: id duplicado no backlog: ${item.id}.`);
      return;
    }
    ids.add(item.id);

    const parsedId = parseBacklogId(item.id);
    if (!parsedId) {
      errors.push(`BACKLOG-003: ${label} deve usar o formato Vn.m.`);
      return;
    }

    if (item.slice !== `V${parsedId.slice}`) {
      errors.push(`BACKLOG-003: ${label} deve apontar slice ${`V${parsedId.slice}`}, recebeu ${item.slice}.`);
    }

    if (previousKey) {
      const expected =
        parsedId.slice === previousKey[0]
          ? [previousKey[0], previousKey[1] + 1]
          : [previousKey[0] + 1, 1];
      if (parsedId.slice !== expected[0] || parsedId.item !== expected[1]) {
        errors.push(
          `BACKLOG-003: ordem do backlog deve seguir cadeia estrita; esperado V${expected[0]}.${expected[1]}, recebeu ${item.id}.`,
        );
      }
    } else if (parsedId.slice !== 1 || parsedId.item !== 1) {
      errors.push(`BACKLOG-003: o backlog deve começar em V1.1, recebeu ${item.id}.`);
    }
    previousKey = [parsedId.slice, parsedId.item];

    const currentWindowRank = windowRank(item.planning_window);
    if (currentWindowRank === -1) {
      errors.push(`BACKLOG-003: ${label} deve usar planning_window em ${ALLOWED_WINDOWS.join(", ")}.`);
    } else if (currentWindowRank < previousWindowRank) {
      errors.push(`BACKLOG-003: planning_window não pode regredir; recebido ${item.planning_window} após janela mais tardia.`);
    } else {
      previousWindowRank = currentWindowRank;
    }
  });

  const knownIds = backlog.items.map((item) => item.id).filter((value): value is string => typeof value === "string");
  const knownIdSet = new Set(knownIds);
  backlog.items.forEach((item, index) => {
    const label = item.id ?? `item[${index}]`;
    const dependsOn = Array.isArray(item.depends_on) ? item.depends_on : [];

    if (index === 0) {
      if (dependsOn.length !== 0) {
        errors.push(`BACKLOG-003: ${label} deve começar sem dependências.`);
      }
      return;
    }

    if (dependsOn.length === 0) {
      errors.push(`BACKLOG-003: ${label} deve depender do item anterior da cadeia.`);
      return;
    }

    for (const dependency of dependsOn) {
      if (!knownIdSet.has(dependency)) {
        errors.push(`BACKLOG-003: ${label} depende de item inexistente: ${dependency}.`);
        continue;
      }

      const dependencyIndex = knownIds.indexOf(dependency);
      if (dependencyIndex >= index) {
        errors.push(`BACKLOG-003: ${label} não pode depender de item futuro ou da própria posição: ${dependency}.`);
      }
    }
  });
}

function checkItemsAgainstRoadmap(
  root: string,
  backlog: RoadmapBacklogDocument,
  roadmap: RoadmapDocument,
  errors: string[],
) {
  const slices = Array.isArray(roadmap.slices) ? roadmap.slices : [];
  const sliceMap = new Map(
    slices
      .filter((slice): slice is { id: string; linked_requirements?: string[] } => typeof slice.id === "string")
      .map((slice) => [slice.id, new Set(slice.linked_requirements ?? [])]),
  );

  for (const expectedSlice of ["V1", "V2", "V3", "V4", "V5"]) {
    if (!sliceMap.has(expectedSlice)) {
      errors.push(`BACKLOG-004: ${ROADMAP_YAML} deve conter ${expectedSlice} para validar o backlog.`);
    }
  }

  const seenSlices = new Set<string>();
  for (const item of backlog.items ?? []) {
    if (!item.id || !item.slice) continue;

    const sliceRequirements = sliceMap.get(item.slice);
    if (!sliceRequirements) {
      errors.push(`BACKLOG-004: ${item.id} referencia fatia inexistente no roadmap: ${item.slice}.`);
      continue;
    }

    seenSlices.add(item.slice);
    for (const requirementId of item.linked_requirements ?? []) {
      if (!sliceRequirements.has(requirementId)) {
        errors.push(
          `BACKLOG-004: ${item.id} só pode ligar requisitos pertencentes a ${item.slice} em ${ROADMAP_YAML}; recebido ${requirementId}.`,
        );
      }
    }
  }

  for (const expectedSlice of ["V1", "V2", "V3", "V4", "V5"]) {
    if (!seenSlices.has(expectedSlice)) {
      errors.push(`BACKLOG-004: o backlog deve cobrir ao menos um item para ${expectedSlice}.`);
    }
  }

  try {
    const requirements = loadRequirements(root);
    const knownRequirementIds = new Set(requirements.map((requirement) => requirement.id));
    for (const item of backlog.items ?? []) {
      for (const requirementId of item.linked_requirements ?? []) {
        if (!knownRequirementIds.has(requirementId)) {
          errors.push(`BACKLOG-004: ${item.id ?? "<sem id>"} referencia REQ desconhecido: ${requirementId}.`);
        }
      }
    }
  } catch (error) {
    errors.push(`BACKLOG-004: falha ao carregar ${REQUIREMENTS_PATH}: ${(error as Error).message}`);
  }
}

function checkDocumentationCoverage(root: string, errors: string[]) {
  const readme = readTextIfExists(root, ROADMAP_README);
  if (readme) {
    for (const snippet of ["execution-backlog.yaml", "pnpm roadmap-backlog-check"]) {
      if (!readme.includes(snippet)) {
        errors.push(`BACKLOG-005: ${ROADMAP_README} deve mencionar ${snippet}.`);
      }
    }
  }

  const harness = readTextIfExists(root, HARNESS_ROADMAP);
  if (harness && !harness.includes("execution-backlog.yaml")) {
    errors.push(`BACKLOG-005: ${HARNESS_ROADMAP} deve documentar execution-backlog.yaml.`);
  }
}

function readTextIfExists(root: string, relativePath: string) {
  const path = resolve(root, relativePath);
  return existsSync(path) ? readFileSync(path, "utf8") : undefined;
}

function parseBacklogId(id: string) {
  const match = /^V([1-5])\.(\d+)$/.exec(id);
  if (!match) return undefined;
  return {
    slice: Number(match[1]),
    item: Number(match[2]),
  };
}

function windowRank(value: string | undefined) {
  return ALLOWED_WINDOWS.indexOf((value ?? "") as (typeof ALLOWED_WINDOWS)[number]);
}

function runCli() {
  const result = checkRoadmapBacklog();
  console.log(`roadmap-backlog-check: ${result.checkedItems} item(ns) no backlog executável.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
