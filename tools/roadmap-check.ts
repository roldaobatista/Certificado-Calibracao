import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

import { loadRequirements } from "./validation-dossier";

const ROADMAP_README = "compliance/roadmap/README.md";
const ROADMAP_YAML = "compliance/roadmap/v1-v5.yaml";
const ROADMAP_TRANSVERSAL_TRACKS_YAML = "compliance/roadmap/transversal-tracks.yaml";
const REQUIREMENTS_PATH = "compliance/validation-dossier/requirements.yaml";
const HARNESS_ROADMAP = "harness/10-roadmap.md";
const EXPECTED_SLICES = ["V1", "V2", "V3", "V4", "V5"] as const;
const REQUIRED_POLICY_FLAGS = [
  "no_slice_starts_without_previous_gate",
  "release_norm_required",
  "validation_dossier_required",
  "normative_package_required",
] as const;

type RoadmapDocument = {
  version?: number;
  source?: string;
  policy?: Record<string, unknown>;
  coverage?: RoadmapCoverage;
  slices?: RoadmapSlice[];
};

type RoadmapCoverage = {
  tracked_requirement_prefixes?: string[];
  excluded_requirements?: string[];
};

type TransversalTrackDocument = {
  version?: number;
  source?: string;
  tracks?: TransversalTrack[];
};

type TransversalTrack = {
  id?: string;
  title?: string;
  owner?: string;
  harness_refs?: string[];
  gate_commands?: string[];
  linked_requirements?: string[];
};

type RoadmapSlice = {
  id?: string;
  epic_id?: string;
  title?: string;
  depends_on?: string[];
  estimated_duration_weeks?: string | number;
  release_norm_path?: string;
  validation_dossier_path?: string;
  primary_agents?: string[];
  linked_requirements?: string[];
  scope?: string[];
  exit_gates?: string[];
};

export type RoadmapCheckResult = {
  errors: string[];
  checkedSlices: number;
};

export function checkRoadmap(root = process.cwd()): RoadmapCheckResult {
  const errors: string[] = [];

  for (const path of [ROADMAP_README, ROADMAP_YAML, HARNESS_ROADMAP]) {
    if (!existsSync(resolve(root, path))) {
      errors.push(`ROADMAP-001: artefato obrigatório ausente: ${path}.`);
    }
  }

  const roadmap = loadRoadmap(root, errors);
  if (roadmap) {
    checkRoadmapDocument(roadmap, errors);
    checkRequirementLinks(root, roadmap, errors);
    checkRequirementCoverage(root, roadmap, errors);
    checkTransversalTracks(root, roadmap, errors);
  }

  if (existsSync(resolve(root, HARNESS_ROADMAP))) {
    checkHarnessCoverage(root, errors);
  }

  return {
    errors,
    checkedSlices: Array.isArray(roadmap?.slices) ? roadmap.slices.length : 0,
  };
}

function loadRoadmap(root: string, errors: string[]): RoadmapDocument | undefined {
  const path = resolve(root, ROADMAP_YAML);
  if (!existsSync(path)) return undefined;

  const parsed = yamlLoad(readFileSync(path, "utf8"));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    errors.push(`ROADMAP-002: ${ROADMAP_YAML} deve conter um objeto YAML.`);
    return undefined;
  }

  return parsed as RoadmapDocument;
}

function checkRoadmapDocument(roadmap: RoadmapDocument, errors: string[]) {
  if (roadmap.version !== 1) {
    errors.push(`ROADMAP-002: ${ROADMAP_YAML} deve declarar version: 1.`);
  }
  if (roadmap.source !== HARNESS_ROADMAP) {
    errors.push(`ROADMAP-002: ${ROADMAP_YAML} deve apontar source: ${HARNESS_ROADMAP}.`);
  }

  for (const flag of REQUIRED_POLICY_FLAGS) {
    if (roadmap.policy?.[flag] !== true) {
      errors.push(`ROADMAP-002: policy.${flag} deve ser true.`);
    }
  }

  if (!Array.isArray(roadmap.slices)) {
    errors.push(`ROADMAP-003: ${ROADMAP_YAML} deve declarar slices.`);
    return;
  }

  const ids = roadmap.slices.map((slice) => slice.id ?? "<sem id>");
  for (const expectedId of EXPECTED_SLICES) {
    if (!ids.includes(expectedId)) {
      errors.push(`ROADMAP-003: roadmap deve conter fatia ${expectedId}.`);
    }
  }
  if (ids.join(",") !== EXPECTED_SLICES.join(",")) {
    errors.push(`ROADMAP-003: fatias devem estar em ordem estrita ${EXPECTED_SLICES.join(" -> ")}; recebido ${ids.join(" -> ")}.`);
  }

  roadmap.slices.forEach((slice, index) => checkSlice(slice, index, errors));
}

function checkSlice(slice: RoadmapSlice, index: number, errors: string[]) {
  const label = slice.id ?? `slice[${index}]`;
  const expectedId = EXPECTED_SLICES[index];
  if (slice.id !== expectedId) {
    errors.push(`ROADMAP-003: posição ${index + 1} deve ser ${expectedId}, recebeu ${label}.`);
  }

  const expectedDependency = index === 0 ? [] : [EXPECTED_SLICES[index - 1]];
  if (!arraysEqual(slice.depends_on ?? [], expectedDependency)) {
    errors.push(`ROADMAP-003: ${label} deve depender de [${expectedDependency.join(", ")}].`);
  }

  for (const field of [
    "epic_id",
    "title",
    "estimated_duration_weeks",
    "release_norm_path",
    "validation_dossier_path",
  ] as const) {
    if (!slice[field]) {
      errors.push(`ROADMAP-004: ${label} sem campo obrigatório ${field}.`);
    }
  }

  if (slice.release_norm_path && slice.release_norm_path !== `compliance/release-norm/${label.toLowerCase()}.md`) {
    errors.push(`ROADMAP-004: ${label} release_norm_path deve ser compliance/release-norm/${label.toLowerCase()}.md.`);
  }
  if (
    slice.validation_dossier_path &&
    slice.validation_dossier_path !== `compliance/validation-dossier/releases/${label.toLowerCase()}.md`
  ) {
    errors.push(
      `ROADMAP-004: ${label} validation_dossier_path deve ser compliance/validation-dossier/releases/${label.toLowerCase()}.md.`,
    );
  }

  for (const [field, min] of [
    ["primary_agents", 1],
    ["linked_requirements", 0],
    ["scope", 2],
    ["exit_gates", 3],
  ] as const) {
    const value = slice[field];
    if (!Array.isArray(value) || value.length < min) {
      errors.push(`ROADMAP-004: ${label} deve declarar ${field} com pelo menos ${min} item(ns).`);
    }
  }
}

function checkHarnessCoverage(root: string, errors: string[]) {
  const text = readFileSync(resolve(root, HARNESS_ROADMAP), "utf8");
  for (const id of EXPECTED_SLICES) {
    if (!new RegExp(`^###\\s+${id}\\b`, "im").test(text)) {
      errors.push(`ROADMAP-005: ${HARNESS_ROADMAP} não descreve ${id}.`);
    }
  }
}

function checkRequirementLinks(root: string, roadmap: RoadmapDocument, errors: string[]) {
  if (!Array.isArray(roadmap.slices)) return;

  try {
    const requirements = loadRequirements(root);
    if (requirements.length === 0) {
      errors.push(`ROADMAP-006: ${REQUIREMENTS_PATH} deve existir e conter requisitos para validar linked_requirements.`);
      return;
    }

    const knownRequirementIds = new Set(requirements.map((requirement) => requirement.id));
    const requirementLinks = new Map<string, string[]>();

    roadmap.slices.forEach((slice, index) => {
      const label = slice.id ?? `slice[${index}]`;
      const linkedRequirements = Array.isArray(slice.linked_requirements) ? slice.linked_requirements : [];

      for (const requirementId of linkedRequirements) {
        if (!knownRequirementIds.has(requirementId)) {
          errors.push(`ROADMAP-006: ${label} referencia linked_requirements desconhecido: ${requirementId}.`);
          continue;
        }

        const existing = requirementLinks.get(requirementId);
        if (existing) existing.push(label);
        else requirementLinks.set(requirementId, [label]);
      }
    });

    for (const [requirementId, linkedSlices] of requirementLinks.entries()) {
      if (linkedSlices.length > 1) {
        errors.push(
          `ROADMAP-006: ${requirementId} não pode aparecer em mais de uma fatia; encontrado em ${linkedSlices.join(", ")}.`,
        );
      }
    }
  } catch (error) {
    errors.push(`ROADMAP-006: falha ao carregar ${REQUIREMENTS_PATH}: ${(error as Error).message}`);
  }
}

function checkRequirementCoverage(root: string, roadmap: RoadmapDocument, errors: string[]) {
  const coverage = roadmap.coverage;
  const trackedPrefixes = Array.isArray(coverage?.tracked_requirement_prefixes)
    ? coverage.tracked_requirement_prefixes.filter((value) => typeof value === "string" && value.trim().length > 0)
    : [];
  const excludedRequirements = Array.isArray(coverage?.excluded_requirements)
    ? coverage.excluded_requirements.filter((value) => typeof value === "string" && value.trim().length > 0)
    : [];

  if (trackedPrefixes.length === 0) {
    errors.push("ROADMAP-007: coverage.tracked_requirement_prefixes deve declarar ao menos um prefixo monitorado.");
    return;
  }
  if (!Array.isArray(coverage?.excluded_requirements)) {
    errors.push("ROADMAP-007: coverage.excluded_requirements deve existir, mesmo quando vazio.");
    return;
  }

  try {
    const requirements = loadRequirements(root);
    if (requirements.length === 0) {
      errors.push(`ROADMAP-007: ${REQUIREMENTS_PATH} deve existir e conter requisitos para validar coverage.`);
      return;
    }

    const knownRequirementIds = new Set(requirements.map((requirement) => requirement.id));
    const linkedRequirements = new Set(
      (roadmap.slices ?? [])
        .flatMap((slice) => (Array.isArray(slice.linked_requirements) ? slice.linked_requirements : []))
        .filter((value): value is string => typeof value === "string" && value.trim().length > 0),
    );
    const excludedRequirementSet = new Set<string>();

    for (const requirementId of excludedRequirements) {
      if (!knownRequirementIds.has(requirementId)) {
        errors.push(`ROADMAP-007: coverage.excluded_requirements referencia REQ desconhecido: ${requirementId}.`);
        continue;
      }
      if (excludedRequirementSet.has(requirementId)) {
        errors.push(`ROADMAP-007: coverage.excluded_requirements repete REQ: ${requirementId}.`);
        continue;
      }
      excludedRequirementSet.add(requirementId);

      if (linkedRequirements.has(requirementId)) {
        errors.push(`ROADMAP-007: ${requirementId} não pode estar excluido e ligado a uma fatia ao mesmo tempo.`);
      }
    }

    const trackedRequirementIds = requirements
      .map((requirement) => requirement.id)
      .filter((requirementId) => trackedPrefixes.some((prefix) => requirementId.startsWith(prefix)))
      .sort();

    for (const requirementId of trackedRequirementIds) {
      if (!linkedRequirements.has(requirementId) && !excludedRequirementSet.has(requirementId)) {
        errors.push(`ROADMAP-007: ${requirementId} não está coberto por nenhuma fatia nem listado em coverage.excluded_requirements.`);
      }
    }
  } catch (error) {
    errors.push(`ROADMAP-007: falha ao carregar ${REQUIREMENTS_PATH}: ${(error as Error).message}`);
  }
}

function checkTransversalTracks(root: string, roadmap: RoadmapDocument, errors: string[]) {
  const excludedRequirements = Array.isArray(roadmap.coverage?.excluded_requirements)
    ? roadmap.coverage.excluded_requirements.filter((value) => typeof value === "string" && value.trim().length > 0)
    : [];
  if (excludedRequirements.length === 0) return;

  const path = resolve(root, ROADMAP_TRANSVERSAL_TRACKS_YAML);
  if (!existsSync(path)) {
    errors.push(
      `ROADMAP-008: ${ROADMAP_TRANSVERSAL_TRACKS_YAML} é obrigatório quando coverage.excluded_requirements não estiver vazio.`,
    );
    return;
  }

  let document: TransversalTrackDocument;
  try {
    const parsed = yamlLoad(readFileSync(path, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      errors.push(`ROADMAP-008: ${ROADMAP_TRANSVERSAL_TRACKS_YAML} deve conter um objeto YAML.`);
      return;
    }
    document = parsed as TransversalTrackDocument;
  } catch (error) {
    errors.push(`ROADMAP-008: falha ao carregar ${ROADMAP_TRANSVERSAL_TRACKS_YAML}: ${(error as Error).message}`);
    return;
  }

  if (document.version !== 1) {
    errors.push(`ROADMAP-008: ${ROADMAP_TRANSVERSAL_TRACKS_YAML} deve declarar version: 1.`);
  }
  if (document.source !== HARNESS_ROADMAP) {
    errors.push(`ROADMAP-008: ${ROADMAP_TRANSVERSAL_TRACKS_YAML} deve apontar source: ${HARNESS_ROADMAP}.`);
  }
  if (!Array.isArray(document.tracks) || document.tracks.length === 0) {
    errors.push(`ROADMAP-008: ${ROADMAP_TRANSVERSAL_TRACKS_YAML} deve declarar tracks.`);
    return;
  }

  try {
    const requirements = loadRequirements(root);
    const knownRequirementIds = new Set(requirements.map((requirement) => requirement.id));
    const excludedRequirementSet = new Set(excludedRequirements);
    const packageScripts = loadPackageScripts(root, errors);
    const requirementTracks = new Map<string, string[]>();

    document.tracks.forEach((track, index) => {
      const label = track.id ?? `track[${index}]`;

      for (const field of ["id", "title", "owner"] as const) {
        if (!track[field]) {
          errors.push(`ROADMAP-008: ${label} sem campo obrigatório ${field}.`);
        }
      }

      if (!Array.isArray(track.harness_refs) || track.harness_refs.length === 0) {
        errors.push(`ROADMAP-008: ${label} deve declarar harness_refs com pelo menos 1 item.`);
      } else {
        for (const harnessRef of track.harness_refs) {
          if (!existsSync(resolve(root, harnessRef))) {
            errors.push(`ROADMAP-008: ${label} referencia harness inexistente: ${harnessRef}.`);
          }
        }
      }

      if (!Array.isArray(track.gate_commands) || track.gate_commands.length === 0) {
        errors.push(`ROADMAP-008: ${label} deve declarar gate_commands com pelo menos 1 item.`);
      } else {
        for (const command of track.gate_commands) {
          const scriptName = parsePnpmScriptCommand(command);
          if (!scriptName) {
            errors.push(`ROADMAP-008: ${label} gate_commands deve usar o formato "pnpm <script>": ${command}.`);
            continue;
          }
          if (!packageScripts.has(scriptName)) {
            errors.push(`ROADMAP-008: ${label} referencia script inexistente em gate_commands: ${command}.`);
          }
        }
      }

      if (!Array.isArray(track.linked_requirements) || track.linked_requirements.length === 0) {
        errors.push(`ROADMAP-008: ${label} deve declarar linked_requirements com pelo menos 1 item.`);
        return;
      }

      for (const requirementId of track.linked_requirements) {
        if (!knownRequirementIds.has(requirementId)) {
          errors.push(`ROADMAP-008: ${label} referencia REQ desconhecido: ${requirementId}.`);
          continue;
        }
        if (!excludedRequirementSet.has(requirementId)) {
          errors.push(
            `ROADMAP-008: ${label} só pode referenciar requisitos listados em coverage.excluded_requirements; recebido ${requirementId}.`,
          );
          continue;
        }

        const existing = requirementTracks.get(requirementId);
        if (existing) existing.push(label);
        else requirementTracks.set(requirementId, [label]);
      }
    });

    for (const requirementId of excludedRequirementSet) {
      if (!requirementTracks.has(requirementId)) {
        errors.push(`ROADMAP-008: ${requirementId} está em coverage.excluded_requirements, mas não foi mapeado em nenhuma trilha transversal.`);
      }
    }

    for (const [requirementId, tracks] of requirementTracks.entries()) {
      if (tracks.length > 1) {
        errors.push(`ROADMAP-008: ${requirementId} não pode aparecer em mais de uma trilha transversal; encontrado em ${tracks.join(", ")}.`);
      }
    }
  } catch (error) {
    errors.push(`ROADMAP-008: falha ao validar ${ROADMAP_TRANSVERSAL_TRACKS_YAML}: ${(error as Error).message}`);
  }
}

function loadPackageScripts(root: string, errors: string[]) {
  const packageJsonPath = resolve(root, "package.json");
  if (!existsSync(packageJsonPath)) {
    errors.push("ROADMAP-008: package.json é obrigatório para validar gate_commands das trilhas transversais.");
    return new Set<string>();
  }

  try {
    const parsed = JSON.parse(readFileSync(packageJsonPath, "utf8")) as { scripts?: Record<string, string> };
    return new Set(Object.keys(parsed.scripts ?? {}));
  } catch (error) {
    errors.push(`ROADMAP-008: falha ao carregar package.json para validar gate_commands: ${(error as Error).message}`);
    return new Set<string>();
  }
}

function parsePnpmScriptCommand(command: string) {
  const match = /^pnpm\s+([a-z0-9:-]+)$/i.exec(command.trim());
  return match?.[1];
}

function arraysEqual(left: readonly string[], right: readonly string[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function runCli() {
  const result = checkRoadmap();
  console.log(`roadmap-check: ${result.checkedSlices}/5 fatia(s) V1-V5.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
