import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { load as yamlLoad } from "js-yaml";

import { loadRequirements, type Requirement } from "./validation-dossier";

const VERIFICATION_LOG_README = "compliance/verification-log/README.md";
const VERIFICATION_LOG_TEMPLATE = "compliance/verification-log/_template.yaml";
const VERIFICATION_ISSUES_ROOT = "compliance/verification-log/issues";
const VERIFICATION_ISSUES_README = `${VERIFICATION_ISSUES_ROOT}/README.md`;
const VERIFICATION_ISSUE_TEMPLATE = `${VERIFICATION_ISSUES_ROOT}/_template.md`;
const VERIFICATION_ISSUE_DRAFTS_DIR = `${VERIFICATION_ISSUES_ROOT}/drafts`;
const ROADMAP_YAML = "compliance/roadmap/v1-v5.yaml";
const SNAPSHOT_MANIFEST = "compliance/validation-dossier/snapshots/manifest.yaml";
const REQUIRED_SNAPSHOT_SOURCE = "harness/05-guardrails.md";
const REQUIRED_SNAPSHOT_PROFILES = ["A", "B", "C"] as const;
const REQUIRED_BASELINE_APPROVERS = ["regulator", "product-governance"] as const;
const SNAPSHOT_DIFF_ISSUE_LABELS = ["compliance", "verification-cascade", "snapshot-diff", "blocker"] as const;
const SPEC_REVIEW_FLAG_LABELS = ["compliance", "verification-cascade", "spec-review-flag", "l1-reaudit"] as const;
const EPIC_REVIEW_FLAG_LABELS = ["compliance", "verification-cascade", "epic-review-flag", "l0-reaudit"] as const;

export const CRITICAL_AREAS = [
  "apps/api/src/domain/emission/**",
  "apps/api/src/domain/audit/**",
  "packages/engine-uncertainty/**",
  "packages/normative-rules/**",
  "packages/audit-log/**",
] as const;

const RELEASE_AUDITOR_PATHS = [
  "compliance/audits/metrology",
  "compliance/audits/legal",
  "compliance/audits/code",
] as const;

export type CascadeGate = {
  level: "L0" | "L1" | "L2" | "L3" | "L4" | "L5";
  gate: string;
  required: boolean;
  reason: string;
};

export type CascadePlan = {
  changedFiles: string[];
  criticalAreas: string[];
  requiresFullRegression: boolean;
  requiresSnapshotDiff: boolean;
  regressionTests: string[];
  gates: CascadeGate[];
};

export type ReleaseAuditCheck = {
  release: string;
  required: string[];
  missing: string[];
};

export type VerificationCascadeCheck = {
  errors: string[];
  checkedSnapshots: number;
  checkedProfiles: string[];
  findings: VerificationCascadeFinding[];
};

export type SnapshotDiffFinding = {
  code: "CASCADE-003";
  issueKind: "snapshot-diff";
  message: string;
  snapshotId: string;
  profile: string;
  baselinePath: string;
  currentPath: string;
  expectedHash?: string;
  baselineHash?: string;
  currentHash?: string;
};

export type SpecReviewFlagFinding = {
  code: "CASCADE-007";
  issueKind: "spec-review-flag";
  message: string;
  reqId: string;
  logPath: string;
  correctionCount: number;
  latestDate: string;
  propagatedUp: string[];
  reAuditsCompleted: string[];
};

export type EpicReviewFlagFinding = {
  code: "CASCADE-008";
  issueKind: "epic-review-flag";
  message: string;
  epicId: string;
  correctionCount: number;
  latestDate: string;
  reqIds: string[];
  logPaths: string[];
  reAuditsCompleted: string[];
};

export type VerificationCascadeFinding = SnapshotDiffFinding | SpecReviewFlagFinding | EpicReviewFlagFinding;

export type VerificationIssueDraft = {
  slug: string;
  path: string;
  title: string;
  body: string;
  labels: string[];
};

export type VerificationManagedIssue = {
  number: number;
  title: string;
  body?: string;
  labels: string[];
  state: "open" | "closed";
};

export type VerificationIssueReconciliationPlan = {
  create: VerificationIssueDraft[];
  reopen: VerificationManagedIssue[];
  keepOpen: VerificationManagedIssue[];
  close: VerificationManagedIssue[];
};

type SnapshotManifest = {
  version?: number;
  source?: string;
  policy?: {
    profiles_required?: unknown;
    snapshots_per_profile?: unknown;
    fail_on_diff?: unknown;
    approval_required_for_baseline_update?: unknown;
  };
  snapshots?: unknown;
};

type SnapshotManifestEntry = {
  id?: unknown;
  profile?: unknown;
  baseline_path?: unknown;
  current_path?: unknown;
  sha256?: unknown;
  renderer?: unknown;
  requirement_refs?: unknown;
};

type VerificationLogEntry = {
  date?: unknown;
  trigger?: unknown;
  ac_changed?: unknown;
  reqs_changed?: unknown;
  propagated_up?: unknown;
  propagated_down?: unknown;
  re_audits_completed?: unknown;
};

type VerificationLogRecord = {
  reqId: string;
  logPath: string;
  entry: VerificationLogEntry;
  index: number;
};

type RoadmapEpicMapDocument = {
  slices?: unknown;
};

type RoadmapEpicMapSlice = {
  epic_id?: unknown;
  linked_requirements?: unknown;
};

export function buildCascadePlan(root: string, changedFiles: string[]): CascadePlan {
  const normalizedChangedFiles = changedFiles.map(normalizePath);
  const criticalAreas = CRITICAL_AREAS.filter((area) =>
    normalizedChangedFiles.some((changedFile) => matchesPathPattern(changedFile, area)),
  );
  const requiresFullRegression = criticalAreas.length > 0;
  const regressionTests = requiresFullRegression
    ? selectAreaRegressionTests(loadRequirements(root), criticalAreas)
    : [];

  return {
    changedFiles: normalizedChangedFiles,
    criticalAreas,
    requiresFullRegression,
    requiresSnapshotDiff: requiresFullRegression,
    regressionTests,
    gates: buildGates(requiresFullRegression),
  };
}

export function checkReleaseAudits(root: string, release: string): ReleaseAuditCheck {
  const required = RELEASE_AUDITOR_PATHS.map((path) => `${path}/${release}.md`);
  return {
    release,
    required,
    missing: required.filter((path) => !existsSync(resolve(root, path))),
  };
}

export function checkVerificationCascade(root = process.cwd()): VerificationCascadeCheck {
  const errors: string[] = [];
  if (!existsSync(resolve(root, VERIFICATION_LOG_README))) {
    errors.push(`CASCADE-001: ${VERIFICATION_LOG_README} não encontrado.`);
  }
  const snapshotCheck = checkSnapshotDiff(root);
  const verificationLogCheck = checkVerificationLogs(root);
  errors.push(...snapshotCheck.errors);
  errors.push(...verificationLogCheck.errors);
  return {
    errors,
    checkedSnapshots: snapshotCheck.checkedSnapshots,
    checkedProfiles: snapshotCheck.checkedProfiles,
    findings: [...snapshotCheck.findings, ...verificationLogCheck.findings],
  };
}

export function buildVerificationIssueDrafts(
  root = process.cwd(),
  result = checkVerificationCascade(root),
): VerificationIssueDraft[] {
  const findings = result.findings.filter(
    (finding) =>
      finding.issueKind === "snapshot-diff" ||
      finding.issueKind === "spec-review-flag" ||
      finding.issueKind === "epic-review-flag",
  );
  if (findings.length === 0) return [];

  const template = readVerificationIssueTemplate(root);
  const groups = new Map<string, VerificationCascadeFinding[]>();
  for (const finding of findings) {
    const entityId =
      finding.issueKind === "snapshot-diff"
        ? finding.snapshotId
        : finding.issueKind === "spec-review-flag"
          ? finding.reqId
          : finding.epicId;
    const groupKey = `${finding.issueKind}:${entityId}`;
    const existing = groups.get(groupKey);
    if (existing) existing.push(finding);
    else groups.set(groupKey, [finding]);
  }

  return [...groups.entries()].map(([groupKey, groupedFindings]) => {
    const first = groupedFindings[0];
    if (first.issueKind === "snapshot-diff") {
      const snapshotId = first.snapshotId;
      const slug = `snapshot-diff-${slugify(snapshotId)}`;
      const path = `${VERIFICATION_ISSUE_DRAFTS_DIR}/${issueDraftDate()}-${slug}.md`;
      const title = `P0-10 snapshot-diff blocker: ${snapshotId}`;
      const issueContext = verificationIssueContext();
      const baselineHash = groupedFindings
        .filter(isSnapshotDiffFinding)
        .map((finding) => finding.baselineHash)
        .find(Boolean) ?? "n/a";
      const currentHash = groupedFindings
        .filter(isSnapshotDiffFinding)
        .map((finding) => finding.currentHash)
        .find(Boolean) ?? "n/a";
      const expectedHash = groupedFindings
        .filter(isSnapshotDiffFinding)
        .map((finding) => finding.expectedHash)
        .find(Boolean) ?? "n/a";
      const body = renderIssueDraft(template, {
        issueType: "verification-cascade-snapshot-diff",
        severity: "blocker",
        labels: [...SNAPSHOT_DIFF_ISSUE_LABELS],
        title,
        context: [
          `Código: ${first.code}`,
          `Snapshot: ${first.snapshotId}`,
          `Perfil: ${first.profile}`,
          `Manifesto: ${SNAPSHOT_MANIFEST}`,
          `Baseline: ${first.baselinePath}`,
          `Current: ${first.currentPath}`,
          `Branch: ${issueContext.branch}`,
          `Commit: ${issueContext.commitSha}`,
          `Workflow run: ${issueContext.workflowRun}`,
        ],
        evidence: [
          `Baseline SHA-256: ${baselineHash}`,
          `Current SHA-256: ${currentHash}`,
          `Hash esperado no manifesto: ${expectedHash}`,
          "Findings:",
          ...groupedFindings.map((finding) => `  - ${finding.message}`),
          "Comando local: `pnpm snapshot-diff-check`",
        ],
        reaudits: ["regulator", "product-governance", "qa-acceptance"],
        closing: ["ADR/PR de correção:", "Novo baseline aprovado:", "Issue GitHub vinculada:"],
      });

      return {
        slug,
        path,
        title,
        body,
        labels: [...SNAPSHOT_DIFF_ISSUE_LABELS],
      };
    }

    if (first.issueKind === "spec-review-flag") {
      const specFinding = groupedFindings.find(isSpecReviewFlagFinding);
      if (!specFinding) {
        throw new Error(`CASCADE-004: finding sem suporte para issue draft: ${groupKey}.`);
      }
      const reqId = specFinding.reqId;
      const slug = `spec-review-flag-${slugify(reqId)}`;
      const path = `${VERIFICATION_ISSUE_DRAFTS_DIR}/${issueDraftDate()}-${slug}.md`;
      const title = `P0-10 spec-review-flag: ${reqId} precisa re-auditoria L1`;
      const body = renderIssueDraft(template, {
        issueType: "verification-cascade-spec-review-flag",
        severity: "high",
        labels: [...SPEC_REVIEW_FLAG_LABELS],
        title,
        context: [
          `Código: ${specFinding.code}`,
          `REQ-ID: ${specFinding.reqId}`,
          `Log: ${specFinding.logPath}`,
          `Última correção observada: ${specFinding.latestDate}`,
        ],
        evidence: [
          `${specFinding.correctionCount} correcoes consecutivas alteraram AC/REQ sem evidência de reauditoria L1 concluída.`,
          "Propagated up:",
          ...specFinding.propagatedUp.map((value) => `  - ${value}`),
          "Reaudits completed registrados:",
          ...(specFinding.reAuditsCompleted.length > 0
            ? specFinding.reAuditsCompleted.map((value) => `  - ${value}`)
            : ["  - <ausente>"]),
          "Comando local: `pnpm verification-cascade:check`",
        ],
        reaudits: ["regulator", "qa-acceptance", `L1/${specFinding.reqId}`],
        closing: ["Spec reaberta:", "Evidência de reauditoria L1:", "Issue GitHub vinculada:"],
      });

      return {
        slug,
        path,
        title,
        body,
        labels: [...SPEC_REVIEW_FLAG_LABELS],
      };
    }

    const epicFinding = groupedFindings.find(isEpicReviewFlagFinding);
    if (!epicFinding) {
      throw new Error(`CASCADE-004: finding sem suporte para issue draft: ${groupKey}.`);
    }
    const epicId = epicFinding.epicId;
    const slug = `epic-review-flag-${slugify(epicId)}`;
    const path = `${VERIFICATION_ISSUE_DRAFTS_DIR}/${issueDraftDate()}-${slug}.md`;
    const title = `P0-10 epic-review-flag: ${epicId} precisa re-auditoria L0`;
    const body = renderIssueDraft(template, {
      issueType: "verification-cascade-epic-review-flag",
      severity: "high",
      labels: [...EPIC_REVIEW_FLAG_LABELS],
      title,
      context: [
        `Código: ${epicFinding.code}`,
        `EPIC-ID: ${epicFinding.epicId}`,
        `Última correção observada: ${epicFinding.latestDate}`,
      ],
      evidence: [
        `${epicFinding.correctionCount} correcoes consecutivas em ${epicFinding.reqIds.length} specs do épico alteraram AC/REQ sem evidência de reauditoria L0 concluída.`,
        "REQs afetados:",
        ...epicFinding.reqIds.map((value) => `  - ${value}`),
        "Logs envolvidos:",
        ...epicFinding.logPaths.map((value) => `  - ${value}`),
        "Reaudits completed registrados:",
        ...(epicFinding.reAuditsCompleted.length > 0
          ? epicFinding.reAuditsCompleted.map((value) => `  - ${value}`)
          : ["  - <ausente>"]),
        "Comando local: `pnpm verification-cascade:check`",
      ],
      reaudits: ["regulator", "product-governance", `L0/${epicFinding.epicId}`],
      closing: ["Épico reaberto:", "Evidência de reauditoria L0:", "Issue GitHub vinculada:"],
    });

    return {
      slug,
      path,
      title,
      body,
      labels: [...EPIC_REVIEW_FLAG_LABELS],
    };
  });
}

export function planVerificationIssueReconciliation(
  drafts: VerificationIssueDraft[],
  issues: VerificationManagedIssue[],
): VerificationIssueReconciliationPlan {
  const managedIssues = issues.filter(isManagedVerificationIssue);
  const draftTitles = new Set(drafts.map((draft) => draft.title));
  const create: VerificationIssueDraft[] = [];
  const reopen: VerificationManagedIssue[] = [];
  const keepOpen: VerificationManagedIssue[] = [];

  for (const draft of drafts) {
    const matchingOpenIssue = managedIssues.find((issue) => issue.state === "open" && issue.title === draft.title);
    if (matchingOpenIssue) {
      keepOpen.push(matchingOpenIssue);
      continue;
    }

    const matchingClosedIssue = managedIssues.find((issue) => issue.state === "closed" && issue.title === draft.title);
    if (matchingClosedIssue) {
      reopen.push(matchingClosedIssue);
      continue;
    }

    create.push(draft);
  }

  const close = managedIssues.filter((issue) => issue.state === "open" && !draftTitles.has(issue.title));
  return { create, reopen, keepOpen, close };
}

export function writeVerificationIssueDrafts(
  root = process.cwd(),
  drafts = buildVerificationIssueDrafts(root),
) {
  const writtenPaths: string[] = [];
  if (drafts.length === 0) return writtenPaths;

  const draftsDir = resolve(root, VERIFICATION_ISSUE_DRAFTS_DIR);
  mkdirSync(draftsDir, { recursive: true });
  for (const draft of drafts) {
    const fullPath = resolve(root, draft.path);
    writeFileSync(fullPath, draft.body);
    writtenPaths.push(draft.path);
  }
  return writtenPaths;
}

function checkSnapshotDiff(root: string) {
  const errors: string[] = [];
  const findings: VerificationCascadeFinding[] = [];
  const manifestPath = resolve(root, SNAPSHOT_MANIFEST);
  if (!existsSync(manifestPath)) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} não encontrado.`);
    return { errors, checkedSnapshots: 0, checkedProfiles: [], findings };
  }

  const manifest = loadSnapshotManifest(manifestPath, errors);
  if (!manifest) return { errors, checkedSnapshots: 0, checkedProfiles: [], findings };

  validateSnapshotPolicy(manifest, errors);

  const snapshots = Array.isArray(manifest.snapshots) ? (manifest.snapshots as SnapshotManifestEntry[]) : [];
  if (snapshots.length === 0) {
      errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar snapshots.`);
  }

  const checkedProfiles: string[] = [];
  let checkedSnapshots = 0;
  for (const [index, snapshot] of snapshots.entries()) {
    if (!isRecord(snapshot)) {
      errors.push(`CASCADE-002: snapshot #${index + 1} deve ser objeto.`);
      continue;
    }

    const id = asNonEmptyString(snapshot.id);
    const profile = asNonEmptyString(snapshot.profile);
    const baselinePath = asNonEmptyString(snapshot.baseline_path);
    const currentPath = asNonEmptyString(snapshot.current_path);
    const expectedHash = asNonEmptyString(snapshot.sha256);
    const renderer = asNonEmptyString(snapshot.renderer);
    const label = id ?? `snapshot #${index + 1}`;

    if (!id) errors.push(`CASCADE-002: ${label} deve declarar id.`);
    if (!profile) errors.push(`CASCADE-002: ${label} deve declarar profile.`);
    if (!baselinePath) errors.push(`CASCADE-002: ${label} deve declarar baseline_path.`);
    if (!currentPath) errors.push(`CASCADE-002: ${label} deve declarar current_path.`);
    if (!expectedHash) errors.push(`CASCADE-002: ${label} deve declarar sha256.`);
    if (!renderer) errors.push(`CASCADE-002: ${label} deve declarar renderer.`);
    if (!Array.isArray(snapshot.requirement_refs) || snapshot.requirement_refs.length === 0) {
      errors.push(`CASCADE-002: ${label} deve declarar requirement_refs.`);
    }
    if (profile && !REQUIRED_SNAPSHOT_PROFILES.includes(profile as (typeof REQUIRED_SNAPSHOT_PROFILES)[number])) {
      errors.push(`CASCADE-002: ${label} usa perfil inválido: ${profile}.`);
    }
    if (!id || !profile || !baselinePath || !currentPath || !expectedHash) continue;

    const baselineFullPath = resolveSafePath(root, baselinePath);
    const currentFullPath = resolveSafePath(root, currentPath);
    if (!baselineFullPath) {
      errors.push(`CASCADE-002: ${label} baseline_path deve ser relativo ao repositório.`);
      continue;
    }
    if (!currentFullPath) {
      errors.push(`CASCADE-002: ${label} current_path deve ser relativo ao repositório.`);
      continue;
    }
    if (!existsSync(baselineFullPath)) {
      errors.push(`CASCADE-002: ${label} baseline ausente: ${normalizePath(baselinePath)}.`);
      continue;
    }
    if (!existsSync(currentFullPath)) {
      errors.push(`CASCADE-002: ${label} snapshot atual ausente: ${normalizePath(currentPath)}.`);
      continue;
    }

    const baselineHash = sha256File(baselineFullPath);
    const currentHash = sha256File(currentFullPath);
    checkedSnapshots += 1;
    checkedProfiles.push(profile);

    if (baselineHash !== expectedHash.toLowerCase()) {
      const message = `CASCADE-003: ${label} baseline diverge do sha256 do manifest (${baselineHash} != ${expectedHash.toLowerCase()}).`;
      errors.push(message);
      findings.push({
        code: "CASCADE-003",
        issueKind: "snapshot-diff",
        message,
        snapshotId: id,
        profile,
        baselinePath: normalizePath(baselinePath),
        currentPath: normalizePath(currentPath),
        expectedHash: expectedHash.toLowerCase(),
        baselineHash,
        currentHash,
      });
    }
    if (currentHash !== baselineHash) {
      const message = `CASCADE-003: ${label} snapshot atual diverge do baseline (${currentHash} != ${baselineHash}).`;
      errors.push(message);
      findings.push({
        code: "CASCADE-003",
        issueKind: "snapshot-diff",
        message,
        snapshotId: id,
        profile,
        baselinePath: normalizePath(baselinePath),
        currentPath: normalizePath(currentPath),
        expectedHash: expectedHash.toLowerCase(),
        baselineHash,
        currentHash,
      });
    }
  }

  const snapshotsPerProfile = snapshotCountPolicy(manifest);
  for (const profile of REQUIRED_SNAPSHOT_PROFILES) {
    const count = checkedProfiles.filter((checkedProfile) => checkedProfile === profile).length;
    if (count < snapshotsPerProfile) {
      errors.push(`CASCADE-002: perfil ${profile} tem ${count}/${snapshotsPerProfile} snapshot(s) canônico(s).`);
    }
  }

  return {
    errors,
    checkedSnapshots,
    checkedProfiles: uniqueSorted(checkedProfiles),
    findings,
  };
}

function checkVerificationLogs(root: string) {
  const errors: string[] = [];
  const findings: VerificationCascadeFinding[] = [];
  const records: VerificationLogRecord[] = [];
  if (!existsSync(resolve(root, VERIFICATION_LOG_TEMPLATE))) {
    errors.push(`CASCADE-006: ${VERIFICATION_LOG_TEMPLATE} não encontrado.`);
    return { errors, findings };
  }

  for (const relativePath of listVerificationLogFiles(root)) {
    const path = resolve(root, relativePath);
    let parsed: unknown;
    try {
      parsed = yamlLoad(readFileSync(path, "utf8"));
    } catch (error) {
      errors.push(`CASCADE-006: ${relativePath} inválido: ${(error as Error).message}`);
      continue;
    }

    if (!Array.isArray(parsed)) {
      errors.push(`CASCADE-006: ${relativePath} deve conter lista YAML de propagacoes.`);
      continue;
    }

    const entries = parsed.filter(isRecord) as VerificationLogEntry[];
    if (entries.length !== parsed.length || entries.length === 0) {
      errors.push(`CASCADE-006: ${relativePath} deve conter pelo menos uma propagacao estruturada.`);
      continue;
    }

    const reqId = basename(relativePath, ".yaml");
    for (const [index, entry] of entries.entries()) {
      records.push({ reqId, logPath: relativePath, entry, index });
      if (!stringValue(entry.date)) {
        errors.push(`CASCADE-006: ${relativePath} entrada #${index + 1} sem date.`);
      }
      if (!stringValue(entry.trigger)) {
        errors.push(`CASCADE-006: ${relativePath} entrada #${index + 1} sem trigger.`);
      }
      if (!Array.isArray(entry.propagated_up)) {
        errors.push(`CASCADE-006: ${relativePath} entrada #${index + 1} sem propagated_up.`);
      }
      if (!Array.isArray(entry.propagated_down)) {
        errors.push(`CASCADE-006: ${relativePath} entrada #${index + 1} sem propagated_down.`);
      }
      if (!Array.isArray(entry.re_audits_completed)) {
        errors.push(`CASCADE-006: ${relativePath} entrada #${index + 1} sem re_audits_completed.`);
      }
    }

    const correctionStreak = trailingSpecCorrectionStreak(entries);
    const l1ReauditRecorded = correctionStreak.some((entry) =>
      arrayValue(entry.re_audits_completed).some((value) => value.startsWith("L1/") || value.startsWith("L1:")),
    );

    if (correctionStreak.length >= 3 && !l1ReauditRecorded) {
      const latestEntry = correctionStreak[correctionStreak.length - 1];
      const latestDate = stringValue(latestEntry.date) || "n/a";
      const message = `CASCADE-007: ${reqId} precisa re-auditoria L1; ${correctionStreak.length} correcoes consecutivas alteraram AC/REQ sem evidência de L1.`;
      errors.push(message);
      findings.push({
        code: "CASCADE-007",
        issueKind: "spec-review-flag",
        message,
        reqId,
        logPath: relativePath,
        correctionCount: correctionStreak.length,
        latestDate,
        propagatedUp: arrayValue(latestEntry.propagated_up),
        reAuditsCompleted: arrayValue(latestEntry.re_audits_completed),
      });
    }
  }

  const epicErrors = checkEpicReviewFlags(root, records);
  errors.push(...epicErrors.errors);
  findings.push(...epicErrors.findings);

  return { errors, findings };
}

function checkEpicReviewFlags(root: string, records: VerificationLogRecord[]) {
  const errors: string[] = [];
  const findings: VerificationCascadeFinding[] = [];
  const epicEvents = new Map<string, VerificationLogRecord[]>();
  const roadmapEpicMap = loadRoadmapEpicMap(root);

  for (const record of records) {
    const explicitEpicIds = extractLevelIds(record.entry, "L0");
    const epicIds = explicitEpicIds.length > 0 ? explicitEpicIds : fallbackEpicIdsForRequirement(roadmapEpicMap, record.reqId);
    for (const epicId of epicIds) {
      const existing = epicEvents.get(epicId);
      if (existing) existing.push(record);
      else epicEvents.set(epicId, [record]);
    }
  }

  for (const [epicId, events] of epicEvents.entries()) {
    const timeline = [...events].sort(compareVerificationRecords);
    const correctionStreak = trailingEpicCorrectionStreak(timeline);
    const reqIds = uniqueSorted(correctionStreak.map((record) => record.reqId));
    const l0ReauditRecorded = correctionStreak.some((record) =>
      arrayValue(record.entry.re_audits_completed).some((value) => referencesLevelId(value, "L0", epicId)),
    );

    if (correctionStreak.length >= 3 && reqIds.length >= 2 && !l0ReauditRecorded) {
      const latestRecord = correctionStreak[correctionStreak.length - 1];
      const latestDate = stringValue(latestRecord.entry.date) || "n/a";
      const message = `CASCADE-008: ${epicId} precisa re-auditoria L0; ${correctionStreak.length} correcoes consecutivas em ${reqIds.length} specs alteraram AC/REQ sem evidência de L0.`;
      errors.push(message);
      findings.push({
        code: "CASCADE-008",
        issueKind: "epic-review-flag",
        message,
        epicId,
        correctionCount: correctionStreak.length,
        latestDate,
        reqIds,
        logPaths: uniqueSorted(correctionStreak.map((record) => record.logPath)),
        reAuditsCompleted: arrayValue(latestRecord.entry.re_audits_completed),
      });
    }
  }

  return { errors, findings };
}

function readVerificationIssueTemplate(root: string) {
  const requiredPaths = [VERIFICATION_ISSUES_README, VERIFICATION_ISSUE_TEMPLATE, VERIFICATION_ISSUE_DRAFTS_DIR];
  for (const path of requiredPaths) {
    if (!existsSync(resolve(root, path))) {
      throw new Error(`CASCADE-004: artefato canônico ausente para issue draft: ${path}.`);
    }
  }
  return readFileSync(resolve(root, VERIFICATION_ISSUE_TEMPLATE), "utf8");
}

function verificationIssueContext() {
  const repository = process.env.GITHUB_REPOSITORY || "n/a";
  const branch = process.env.GITHUB_REF_NAME || "n/a";
  const commitSha = process.env.GITHUB_SHA || "n/a";
  const runId = process.env.GITHUB_RUN_ID;
  const serverUrl = process.env.GITHUB_SERVER_URL || "https://github.com";
  const workflowRun = runId && repository !== "n/a" ? `${serverUrl}/${repository}/actions/runs/${runId}` : "n/a";
  return { repository, branch, commitSha, workflowRun };
}

function renderTemplate(template: string, replacements: Record<string, string>) {
  return template.replace(/{{\s*([a-z_]+)\s*}}/g, (_match, key: string) => replacements[key] ?? "n/a");
}

function renderIssueDraft(
  template: string,
  options: {
    issueType: string;
    severity: string;
    labels: string[];
    title: string;
    context: string[];
    evidence: string[];
    reaudits: string[];
    closing: string[];
  },
) {
  return renderTemplate(template, {
    issue_type: options.issueType,
    severity: options.severity,
    labels_yaml: options.labels.map((label) => `  - ${label}`).join("\n"),
    issue_title: options.title,
    context_list: formatBullets(options.context),
    evidence_list: formatBullets(options.evidence),
    reaudit_list: formatBullets(options.reaudits),
    closing_list: formatBullets(options.closing),
  });
}

function formatBullets(values: string[]) {
  if (values.length === 0) return "- n/a";
  return values.map((value) => (value.startsWith("- ") ? value : `- ${value}`)).join("\n");
}

function listVerificationLogFiles(root: string) {
  const directory = resolve(root, "compliance", "verification-log");
  if (!existsSync(directory)) return [];
  return readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name)
    .filter((name) => name.endsWith(".yaml"))
    .filter((name) => name !== "_template.yaml")
    .sort()
    .map((name) => `compliance/verification-log/${name}`);
}

function loadRoadmapEpicMap(root: string) {
  const roadmapPath = resolve(root, ROADMAP_YAML);
  if (!existsSync(roadmapPath)) return new Map<string, string[]>();

  try {
    const parsed = yamlLoad(readFileSync(roadmapPath, "utf8")) as RoadmapEpicMapDocument;
    if (!isRecord(parsed) || !Array.isArray(parsed.slices)) {
      return new Map<string, string[]>();
    }

    const requirementToEpics = new Map<string, Set<string>>();
    for (const slice of parsed.slices) {
      if (!isRecord(slice)) continue;

      const epicId = asNonEmptyString((slice as RoadmapEpicMapSlice).epic_id);
      const linkedRequirements = Array.isArray((slice as RoadmapEpicMapSlice).linked_requirements)
        ? ((slice as RoadmapEpicMapSlice).linked_requirements as unknown[])
            .map(asNonEmptyString)
            .filter(Boolean) as string[]
        : [];

      if (!epicId || linkedRequirements.length === 0) continue;
      for (const requirementId of linkedRequirements) {
        const existing = requirementToEpics.get(requirementId);
        if (existing) existing.add(epicId);
        else requirementToEpics.set(requirementId, new Set([epicId]));
      }
    }

    return new Map(
      [...requirementToEpics.entries()].map(([requirementId, epicIds]) => [requirementId, [...epicIds].sort()]),
    );
  } catch {
    return new Map<string, string[]>();
  }
}

function fallbackEpicIdsForRequirement(roadmapEpicMap: Map<string, string[]>, reqId: string) {
  return roadmapEpicMap.get(reqId) ?? [];
}

function trailingSpecCorrectionStreak(entries: VerificationLogEntry[]) {
  const streak: VerificationLogEntry[] = [];
  for (const entry of [...entries].reverse()) {
    if (entry.ac_changed === true || entry.reqs_changed === true) streak.unshift(entry);
    else break;
  }
  return streak;
}

function trailingEpicCorrectionStreak(records: VerificationLogRecord[]) {
  const streak: VerificationLogRecord[] = [];
  for (const record of [...records].reverse()) {
    if (record.entry.ac_changed === true || record.entry.reqs_changed === true) streak.unshift(record);
    else break;
  }
  return streak;
}

function arrayValue(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value.map(yamlScalarValue).filter(Boolean);
}

function isSnapshotDiffFinding(finding: VerificationCascadeFinding): finding is SnapshotDiffFinding {
  return finding.issueKind === "snapshot-diff";
}

function isSpecReviewFlagFinding(finding: VerificationCascadeFinding): finding is SpecReviewFlagFinding {
  return finding.issueKind === "spec-review-flag";
}

function isEpicReviewFlagFinding(finding: VerificationCascadeFinding): finding is EpicReviewFlagFinding {
  return finding.issueKind === "epic-review-flag";
}

function isManagedVerificationIssue(issue: VerificationManagedIssue) {
  const labels = issue.labels.map((label) => label.trim());
  if (!labels.includes("verification-cascade")) return false;
  const body = issue.body ?? "";
  if (/^issue_type:\s*verification-cascade-/m.test(body)) return true;
  return (
    issue.title.startsWith("P0-10 snapshot-diff blocker:") ||
    issue.title.startsWith("P0-10 spec-review-flag:") ||
    issue.title.startsWith("P0-10 epic-review-flag:")
  );
}

function compareVerificationRecords(left: VerificationLogRecord, right: VerificationLogRecord) {
  return verificationRecordKey(left).localeCompare(verificationRecordKey(right));
}

function verificationRecordKey(record: VerificationLogRecord) {
  return `${stringValue(record.entry.date)}|${record.logPath}|${record.index.toString().padStart(6, "0")}`;
}

function extractLevelIds(entry: VerificationLogEntry, level: "L0" | "L1") {
  const values = [...arrayValue(entry.propagated_up), ...arrayValue(entry.re_audits_completed)];
  const ids = values
    .map((value) => parseLevelId(value, level))
    .filter(Boolean) as string[];
  return uniqueSorted(ids);
}

function parseLevelId(value: string, level: "L0" | "L1") {
  const slashMatch = value.match(new RegExp(`^${level}/([^:\\s]+)`));
  if (slashMatch) return slashMatch[1]?.trim();
  const colonMatch = value.match(new RegExp(`^${level}:\\s*([^:\\s]+)`));
  if (colonMatch) return colonMatch[1]?.trim();
  return undefined;
}

function referencesLevelId(value: string, level: "L0" | "L1", id: string) {
  return value.startsWith(`${level}/${id}`) || value.startsWith(`${level}:${id}`) || value.startsWith(`${level}: ${id}`);
}

function yamlScalarValue(value: unknown): string {
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "string") return value.trim();
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (isRecord(value)) {
    const pairs = Object.entries(value).map(([key, nestedValue]) => `${key}: ${yamlScalarValue(nestedValue)}`);
    return pairs.join("; ").trim();
  }
  return "";
}

function stringValue(value: unknown) {
  return yamlScalarValue(value);
}

function loadSnapshotManifest(path: string, errors: string[]) {
  try {
    const parsed = yamlLoad(readFileSync(path, "utf8"));
    if (!isRecord(parsed)) {
      errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve conter objeto YAML.`);
      return undefined;
    }
    return parsed as SnapshotManifest;
  } catch (error) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} inválido: ${(error as Error).message}`);
    return undefined;
  }
}

function validateSnapshotPolicy(manifest: SnapshotManifest, errors: string[]) {
  if (manifest.version !== 1) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar version: 1.`);
  }
  if (manifest.source !== REQUIRED_SNAPSHOT_SOURCE) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve apontar source: ${REQUIRED_SNAPSHOT_SOURCE}.`);
  }

  const policy = manifest.policy;
  if (!isRecord(policy)) {
    errors.push(`CASCADE-002: ${SNAPSHOT_MANIFEST} deve declarar policy.`);
    return;
  }

  const profiles = Array.isArray(policy.profiles_required) ? policy.profiles_required : [];
  for (const profile of REQUIRED_SNAPSHOT_PROFILES) {
    if (!profiles.includes(profile)) {
      errors.push(`CASCADE-002: policy.profiles_required deve incluir ${profile}.`);
    }
  }
  if (snapshotCountPolicy(manifest) < 1) {
    errors.push("CASCADE-002: policy.snapshots_per_profile deve ser >= 1.");
  }
  if (policy.fail_on_diff !== true) {
    errors.push("CASCADE-002: policy.fail_on_diff deve ser true.");
  }

  const approvers = Array.isArray(policy.approval_required_for_baseline_update)
    ? policy.approval_required_for_baseline_update
    : [];
  for (const approver of REQUIRED_BASELINE_APPROVERS) {
    if (!approvers.includes(approver)) {
      errors.push(`CASCADE-002: baseline update deve exigir aprovação de ${approver}.`);
    }
  }
}

function buildGates(requiresFullRegression: boolean): CascadeGate[] {
  const gates: CascadeGate[] = [
    {
      level: "L3",
      gate: "pre-commit-gates",
      required: true,
      reason: "Código sempre passa pelos gates duros de lint, ownership, dossiê e governança.",
    },
  ];

  if (requiresFullRegression) {
    gates.push(
      {
        level: "L4",
        gate: "full-regression",
        required: true,
        reason: "Mudança em área crítica exige 100% dos REQs blocker/high ligados à área.",
      },
      {
        level: "L4",
        gate: "snapshot-diff",
        required: true,
        reason: "Mudança em área crítica exige diff dos certificados canônicos antes do merge.",
      },
    );
  } else {
    gates.push({
      level: "L4",
      gate: "impact-analysis",
      required: true,
      reason: "Mudança fora da lista crítica usa análise de impacto e suite sentinela mínima.",
    });
  }

  return gates;
}

function selectAreaRegressionTests(requirements: Requirement[], criticalAreas: readonly string[]) {
  const selected = requirements
    .filter((requirement) => requirement.criticality === "blocker" || requirement.criticality === "high")
    .filter((requirement) =>
      (requirement.critical_paths ?? []).some((path) =>
        criticalAreas.some((area) => pathPatternsIntersect(path, area)),
      ),
    )
    .flatMap((requirement) => requirement.linked_tests ?? []);

  return uniqueSorted(selected);
}

function pathPatternsIntersect(left: string, right: string) {
  const normalizedLeft = normalizePath(left);
  const normalizedRight = normalizePath(right);
  if (normalizedLeft === normalizedRight) return true;
  const leftPrefix = patternPrefix(normalizedLeft);
  const rightPrefix = patternPrefix(normalizedRight);
  return leftPrefix.startsWith(rightPrefix) || rightPrefix.startsWith(leftPrefix);
}

function patternPrefix(pattern: string) {
  const wildcardIndex = pattern.indexOf("*");
  return wildcardIndex === -1 ? pattern : pattern.slice(0, wildcardIndex);
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

function snapshotCountPolicy(manifest: SnapshotManifest) {
  const value = manifest.policy?.snapshots_per_profile;
  return typeof value === "number" && Number.isInteger(value) ? value : 0;
}

function issueDraftDate() {
  return process.env.AFERE_CASCADE_TODAY || new Date().toISOString().slice(0, 10);
}

function sha256File(path: string) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function resolveSafePath(root: string, path: string) {
  const normalized = normalizePath(path);
  if (normalized.startsWith("/") || normalized.startsWith("../") || normalized.includes("/../")) return undefined;
  if (/^[a-zA-Z]:\//.test(normalized)) return undefined;

  const fullPath = resolve(root, normalized);
  const rootPath = resolve(root);
  return fullPath.startsWith(rootPath) ? fullPath : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asNonEmptyString(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}

function slugify(value: string) {
  return normalizePath(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function escapeRegex(value: string) {
  return value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
}

function parseCliArgs(argv: string[]) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "check";
  const changedFiles: string[] = [];
  let release = "";
  let json = false;
  let write = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--changed") {
      changedFiles.push(args[++index]);
    } else if (arg === "--release") {
      release = args[++index];
    } else if (arg === "--json") {
      json = true;
    } else if (arg === "--write") {
      write = true;
    } else {
      changedFiles.push(arg);
    }
  }

  return { command, changedFiles, release, json, write };
}

function runCli() {
  const { command, changedFiles, release, json, write } = parseCliArgs(process.argv.slice(2));
  if (command === "plan") {
    const plan = buildCascadePlan(process.cwd(), changedFiles);
    if (json) console.log(JSON.stringify(plan, null, 2));
    else {
      console.log(`verification-cascade: ${plan.criticalAreas.length} área(s) crítica(s).`);
      console.log(`full-regression: ${plan.requiresFullRegression ? "sim" : "não"}`);
      console.log(`snapshot-diff: ${plan.requiresSnapshotDiff ? "sim" : "não"}`);
      for (const test of plan.regressionTests) console.log(test);
    }
    return 0;
  }

  if (command === "release-audits") {
    if (!release) {
      console.error("Uso: verification-cascade release-audits --release <versao>");
      return 2;
    }
    const auditCheck = checkReleaseAudits(process.cwd(), release);
    if (json) console.log(JSON.stringify(auditCheck, null, 2));
    else {
      console.log(`verification-cascade: release ${release}, ${auditCheck.missing.length} parecer(es) ausente(s).`);
      for (const missing of auditCheck.missing) console.error(`ERROR CASCADE-005: parecer L5 ausente: ${missing}.`);
    }
    return auditCheck.missing.length > 0 ? 1 : 0;
  }

  if (command === "issue-drafts") {
    try {
      const result = checkVerificationCascade();
      const drafts = buildVerificationIssueDrafts(process.cwd(), result);
      const writtenPaths = write ? writeVerificationIssueDrafts(process.cwd(), drafts) : [];
      if (json) {
        console.log(JSON.stringify(drafts, null, 2));
      } else {
        console.log(`verification-cascade: ${drafts.length} issue draft(s) gerado(s).`);
        for (const draft of drafts) console.log(`${draft.title} -> ${draft.path}`);
        if (write) {
          for (const path of writtenPaths) console.log(`written: ${path}`);
        }
      }
      return 0;
    } catch (error) {
      console.error(`ERROR ${(error as Error).message}`);
      return 1;
    }
  }

  if (command !== "check") {
    console.error(
      "Uso: verification-cascade [check|plan|release-audits|issue-drafts] [--changed <arquivo>] [--release <versao>] [--json] [--write]",
    );
    return 2;
  }

  const result = checkVerificationCascade();
  console.log(`verification-cascade: check estrutural + snapshot-diff (${result.checkedSnapshots} snapshot(s)).`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
