import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HARNESS_DESIGN_PATH = "HARNESS_DESIGN.md";

const REQUIRED_PATTERNS = [
  {
    id: "TIER3-002",
    pattern: /Tier 3\s+—\s+Cloud agents/i,
    message: "tabela de Tier 3 ausente em HARNESS_DESIGN.md.",
  },
  {
    id: "TIER3-003",
    pattern: /low-risk/i,
    message: "Tier 3 deve declarar que só aceita tarefas low-risk.",
  },
  {
    id: "TIER3-003",
    pattern: /P1-2/i,
    message: "Tier 3 deve referenciar a política P1-2.",
  },
  {
    id: "TIER3-004",
    pattern: /attestation/i,
    message: "Tier 3 deve exigir attestation verificável.",
  },
  {
    id: "TIER3-004",
    pattern: /product-governance/i,
    message: "Tier 3 deve exigir revisão de product-governance.",
  },
  {
    id: "TIER3-005",
    pattern: /harness\/09-cloud-agents-policy\.md/,
    message: "Tier 3 deve apontar para harness/09-cloud-agents-policy.md.",
  },
  {
    id: "TIER3-005",
    pattern: /compliance\/cloud-agents\/policy\.yaml/,
    message: "Tier 3 deve apontar para compliance/cloud-agents/policy.yaml.",
  },
];

const FORBIDDEN_PATTERNS = [
  {
    id: "TIER3-006",
    pattern: /drain de \*?backlog\*? overnight/i,
    message: "remova a formulação antiga de drain de backlog overnight sem qualificação.",
  },
];

export type HarnessDesignTier3Check = {
  errors: string[];
};

export function checkHarnessDesignTier3(root = process.cwd()): HarnessDesignTier3Check {
  const errors: string[] = [];
  const designPath = resolve(root, HARNESS_DESIGN_PATH);

  if (!existsSync(designPath)) {
    return { errors: [`TIER3-001: ${HARNESS_DESIGN_PATH} não encontrado.`] };
  }

  const content = readFileSync(designPath, "utf8");
  const tier3Section = extractTier3Context(content);

  for (const requirement of REQUIRED_PATTERNS) {
    if (!requirement.pattern.test(tier3Section)) {
      errors.push(`${requirement.id}: ${requirement.message}`);
    }
  }

  for (const forbidden of FORBIDDEN_PATTERNS) {
    if (forbidden.pattern.test(tier3Section)) {
      errors.push(`${forbidden.id}: ${forbidden.message}`);
    }
  }

  return { errors };
}

function extractTier3Context(content: string) {
  const normalized = content.replace(/\r\n/g, "\n");
  const section = normalized.match(/(?:^|\n)### 2\.1 Três camadas[\s\S]*?(?=\n### 2\.2|\n## 3\.|\n*$)/)?.[0];
  return section ?? normalized;
}

function runCli() {
  const result = checkHarnessDesignTier3();
  console.log("harness-design-tier3-check: HARNESS_DESIGN.md verificado.");
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
