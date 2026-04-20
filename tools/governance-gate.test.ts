import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const repoRoot = process.cwd();
const scriptPath = join(repoRoot, "tools", "governance-gate.ts");
const tsxLoaderUrl = pathToFileURL(join(repoRoot, "node_modules", "tsx", "dist", "loader.mjs")).href;

const validCodeowners = `# Areas que exigem aprovacao do product-governance
apps/api/src/domain/emission/**       @product-governance
apps/api/src/domain/audit/**          @product-governance @lgpd-security
packages/engine-uncertainty/**        @product-governance @metrology-calc
packages/normative-rules/**           @product-governance @regulator
packages/audit-log/**                 @product-governance @db-schema @lgpd-security
compliance/**                         @product-governance
PRD.md                                @product-governance
`;

const validPullRequestTemplate = `## Governance checklist (product-governance only)

- [ ] Matriz requisito->spec->teste->evidencia atualizada
- [ ] Pacote normativo impactado? Se sim, PR de draft criado em compliance/normative-packages/drafts/
- [ ] Copy-lint verde (sem claims proibidos)
- [ ] Guardrails de multitenancy verdes (gates 1-7)
- [ ] RLS tests passam em >=2 tenants sinteticos
- [ ] Audit hash-chain integra
- [ ] Release notes regulatorias preenchidas se o PR afeta emissao, audit ou pacote normativo
- [ ] Cloud agents: se PR veio de cloud agent, tocou apenas paths da allowlist?

## Pareceres dos 3 auditores externos

- [ ] metrology-auditor: parecer PASS em compliance/audits/metrology/<release>.md
- [ ] legal-counsel: parecer PASS em compliance/audits/legal/<release>.md
- [ ] senior-reviewer: parecer PASS em compliance/audits/code/<release>.md
- [ ] Nenhum dos 3 auditores emitiu BLOQUEIO nao resolvido

## Risco regulatorio (self-assessment)

- [ ] Este PR pode alterar comportamento de emissao? Se sim, descreva.
- [ ] Este PR pode alterar o que e gravado no audit log?
- [ ] Este PR introduz ou altera claim comercial?
- [ ] Algum dos 5 casos-limite aplicavel? Se sim, escalar ao usuario
`;

function productGovernanceAgent(allowedPaths: string[]): string {
  return `---
name: product-governance
description: Gate de merge regulatorio
---

## Paths permitidos (escrita)

${allowedPaths.map((path) => `- ${path}`).join("\n")}

## Paths bloqueados

- apps/**
- packages/**
`;
}

function makeWorkspace(options: {
  codeowners?: string;
  pullRequestTemplate?: string;
  productGovernanceAllowedPaths?: string[];
} = {}): string {
  const root = mkdtempSync(join(tmpdir(), "afere-governance-gate-"));
  mkdirSync(join(root, ".github"), { recursive: true });
  mkdirSync(join(root, ".claude", "agents"), { recursive: true });
  writeFileSync(join(root, ".github", "CODEOWNERS"), options.codeowners ?? validCodeowners);
  writeFileSync(
    join(root, ".github", "pull_request_template.md"),
    options.pullRequestTemplate ?? validPullRequestTemplate,
  );
  writeFileSync(
    join(root, ".claude", "agents", "product-governance.md"),
    productGovernanceAgent(options.productGovernanceAllowedPaths ?? ["adr/**", "compliance/release-norm/**", "Comentarios e approvals de PR"]),
  );
  return root;
}

function runGovernanceGate(root: string) {
  return spawnSync(process.execPath, ["--import", tsxLoaderUrl, scriptPath, "--workspace", root], {
    cwd: repoRoot,
    encoding: "utf8",
  });
}

test("passes when CODEOWNERS, PR checklist and product-governance paths match policy", () => {
  const root = makeWorkspace();
  try {
    const result = runGovernanceGate(root);

    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.match(result.stdout, /governance-gate: ok/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("fails when a critical CODEOWNERS rule is missing a required owner", () => {
  const root = makeWorkspace({
    codeowners: validCodeowners.replace(
      "packages/audit-log/**                 @product-governance @db-schema @lgpd-security",
      "packages/audit-log/**                 @db-schema @lgpd-security",
    ),
  });
  try {
    const result = runGovernanceGate(root);

    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout + result.stderr, /GOV-001/);
    assert.match(result.stdout + result.stderr, /packages\/audit-log\/\*\*/);
    assert.match(result.stdout + result.stderr, /@product-governance/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("fails when product-governance can write application code", () => {
  const root = makeWorkspace({ productGovernanceAllowedPaths: ["adr/**", "apps/api/**", "compliance/release-norm/**"] });
  try {
    const result = runGovernanceGate(root);

    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout + result.stderr, /GOV-003/);
    assert.match(result.stdout + result.stderr, /apps\/api\/\*\*/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
