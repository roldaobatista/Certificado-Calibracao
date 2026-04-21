import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type RequiredArtifact = {
  path: string;
  type: "dir" | "file";
};

const REQUIRED_ARTIFACTS: RequiredArtifact[] = [
  { path: "compliance/audits/code", type: "dir" },
  { path: "compliance/audits/legal", type: "dir" },
  { path: "compliance/audits/metrology", type: "dir" },
  { path: "compliance/budget-log", type: "dir" },
  { path: "compliance/cloud-agents/attestations", type: "dir" },
  { path: "compliance/escalations", type: "dir" },
  { path: "compliance/incidents", type: "dir" },
  { path: "compliance/legal-opinions", type: "dir" },
  { path: "compliance/normative-packages/approved", type: "dir" },
  { path: "compliance/normative-packages/releases", type: "dir" },
  { path: "compliance/regulator-decisions", type: "dir" },
  { path: "compliance/release-norm", type: "dir" },
  { path: "compliance/roadmap", type: "dir" },
  { path: "compliance/runbooks/executions", type: "dir" },
  { path: "compliance/sessions-log", type: "dir" },
  { path: "compliance/validation-dossier/evidence", type: "dir" },
  { path: "compliance/validation-dossier/findings", type: "dir" },
  { path: "compliance/validation-dossier/flake-log", type: "dir" },
  { path: "compliance/validation-dossier/releases", type: "dir" },
  { path: "compliance/validation-dossier/snapshots", type: "dir" },
  { path: "compliance/validation-dossier/snapshots/baseline", type: "dir" },
  { path: "compliance/validation-dossier/snapshots/current", type: "dir" },
  { path: "compliance/verification-log", type: "dir" },
  { path: "compliance/verification-log/issues", type: "dir" },
  { path: "compliance/verification-log/issues/drafts", type: "dir" },
  { path: "compliance/README.md", type: "file" },
  { path: "compliance/approved-claims.md", type: "file" },
  { path: "compliance/audits/README.md", type: "file" },
  { path: "compliance/budget-log/README.md", type: "file" },
  { path: "compliance/cloud-agents-log.md", type: "file" },
  { path: "compliance/cloud-agents-policy.md", type: "file" },
  { path: "compliance/cloud-agents/policy.yaml", type: "file" },
  { path: "compliance/escalations/README.md", type: "file" },
  { path: "compliance/guardrails.md", type: "file" },
  { path: "compliance/legal-opinions/README.md", type: "file" },
  { path: "compliance/normative-packages/README.md", type: "file" },
  { path: "compliance/normative-packages/releases/manifest.yaml", type: "file" },
  { path: "compliance/regulator-decisions/README.md", type: "file" },
  { path: "compliance/release-norm/README.md", type: "file" },
  { path: "compliance/roadmap/README.md", type: "file" },
  { path: "compliance/roadmap/transversal-tracks.yaml", type: "file" },
  { path: "compliance/roadmap/v1-v5.yaml", type: "file" },
  { path: "compliance/runbooks/README.md", type: "file" },
  { path: "compliance/runbooks/drill-schedule.yaml", type: "file" },
  { path: "compliance/sessions-log/README.md", type: "file" },
  { path: "compliance/validation-dossier/README.md", type: "file" },
  { path: "compliance/validation-dossier/coverage-report.md", type: "file" },
  { path: "compliance/validation-dossier/requirements.yaml", type: "file" },
  { path: "compliance/validation-dossier/snapshots/README.md", type: "file" },
  { path: "compliance/validation-dossier/snapshots/manifest.yaml", type: "file" },
  { path: "compliance/validation-dossier/traceability-matrix.yaml", type: "file" },
  { path: "compliance/verification-log/README.md", type: "file" },
  { path: "compliance/verification-log/_template.yaml", type: "file" },
  { path: "compliance/verification-log/issues/README.md", type: "file" },
  { path: "compliance/verification-log/issues/_template.md", type: "file" },
  { path: "compliance/verification-log/issues/drafts/.gitkeep", type: "file" },
];

const REQUIRED_README_REFERENCES = [
  "normative-packages/",
  "validation-dossier/",
  "release-norm/",
  "legal-opinions/",
  "audits/metrology|legal|code/",
  "approved-claims.md",
  "guardrails.md",
  "runbooks/",
  "verification-log/",
  "cloud-agents-policy.md",
  "budget-log/",
  "sessions-log/",
  "roadmap/",
] as const;

export type ComplianceStructureCheckResult = {
  errors: string[];
  checkedArtifacts: number;
  checkedReadmeReferences: number;
};

export function checkComplianceStructure(root = process.cwd()): ComplianceStructureCheckResult {
  const errors: string[] = [];

  for (const artifact of REQUIRED_ARTIFACTS) {
    const fullPath = resolve(root, artifact.path);
    if (!existsSync(fullPath)) {
      errors.push(`COMP-001: artefato obrigatório ausente: ${artifact.path}.`);
      continue;
    }

    const stats = statSync(fullPath);
    if (artifact.type === "dir" && !stats.isDirectory()) {
      errors.push(`COMP-001: ${artifact.path} deve ser diretório.`);
    }
    if (artifact.type === "file" && !stats.isFile()) {
      errors.push(`COMP-001: ${artifact.path} deve ser arquivo.`);
    }
  }

  const readmePath = resolve(root, "compliance/README.md");
  if (existsSync(readmePath)) {
    const readme = normalizeText(readFileSync(readmePath, "utf8"));
    for (const reference of REQUIRED_README_REFERENCES) {
      if (!readme.includes(normalizeText(reference))) {
        errors.push(`COMP-002: compliance/README.md deve referenciar ${reference}.`);
      }
    }
  }

  return {
    errors,
    checkedArtifacts: REQUIRED_ARTIFACTS.length,
    checkedReadmeReferences: REQUIRED_README_REFERENCES.length,
  };
}

function normalizeText(text: string) {
  return text.replace(/\r\n/g, "\n").toLowerCase();
}

function runCli() {
  const result = checkComplianceStructure();
  console.log(
    `compliance-structure-check: ${result.checkedArtifacts} artefato(s), ${result.checkedReadmeReferences} referência(s) no README.`,
  );
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
