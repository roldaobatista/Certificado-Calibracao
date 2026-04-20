# STATUS — Checklist de correções P0/P1/P2

> Cada item aponta para o arquivo do `harness/` que contém a decisão detalhada. Marque `[x]` ao aprovar.

## P0 — Hard blockers

| ID | Correção | Arquivo | Status |
|----|----------|---------|--------|
| P0-1 | Backend `apps/api` como peça de 1ª classe + agente `backend-api` | [02-arquitetura.md](./02-arquitetura.md), [03-agentes.md](./03-agentes.md) | [~] Em implementação (scaffold Fastify + tRPC + Prisma + Docker Compose; /healthz + /trpc/health.ping verdes; lógica de domínio pendente para fatias V1+) |
| P0-2 | Pipeline de normative package assinado e versionado | [04-compliance-pipeline.md](./04-compliance-pipeline.md) | [~] Em implementação (`@afere/normative-rules` valida pacote normativo com hash canônico SHA-256 e assinatura Ed25519; KMS real e pacote aprovado baseline ainda pendentes) |
| P0-3 | Dossiê formal de validação contínua | [04-compliance-pipeline.md](./04-compliance-pipeline.md) | [~] Em implementação (`requirements.yaml`, `traceability-matrix.yaml`, `coverage-report.md` e `tools/validation-dossier.ts`; cobertura atual 3/22 critérios do PRD §13, demais pendentes explícitos) |
| P0-4 | Hard gates de multitenancy e trilha imutável | [05-guardrails.md](./05-guardrails.md) | [~] Em implementação (Gates 1, 2, 3, 4, 5 e 6 funcionais em primeiras fatias; Gate 7 tem seleção de regressão por dossiê, snapshot-diff/flake gate pendentes; Gate 5 cobre RLS, RBAC depende de auth real em `apps/api`) |
| P0-5 | Copy-lint regulatório | [06-copy-lint.md](./06-copy-lint.md) | [~] Em implementação (packages/copy-lint funcional com 8 regras, CLI, hook PreCommit fail-closed, slash /claim-check; teste-de-fogo detectou 4 claims proibidos em PRD.md — finding aberto em compliance/validation-dossier/findings/) |
| P0-6 | Agente `product-governance` + CODEOWNERS | [07-governance-gate.md](./07-governance-gate.md) | [ ] Proposto |
| P0-7 | Budgets mensuráveis (tokens, custo, paralelismo, retries) | [11-budgets.md](./11-budgets.md) | [ ] Proposto |
| P0-8 | Matriz de escalonamento e rito de desempate | [12-escalation-matrix.md](./12-escalation-matrix.md) | [ ] Proposto (revisado, +D8) |
| P0-9 | Runbooks de recuperação (KMS, hash-chain, WORM, normative package) | [13-runbooks-recovery.md](./13-runbooks-recovery.md) | [ ] Proposto |
| P0-10 | Cascata de verificação L0→L5 + propagação bidirecional | [14-verification-cascade.md](./14-verification-cascade.md) | [ ] Proposto (revisado, L5 inclui 3 auditores) |
| P0-11 | Redundância, loops e auto-consistência (property tests, flake gate, dupla checagem) | [15-redundancy-and-loops.md](./15-redundancy-and-loops.md) | [ ] Proposto |
| P0-12 | 3 agentes auditores externos substituem humanos contratados (metrology-auditor, legal-counsel, senior-reviewer) | [16-agentes-auditores-externos.md](./16-agentes-auditores-externos.md) | [ ] Proposto |
| P0-13 | Operação dual Claude Code + Codex CLI com `AGENTS.md` canônico | [17-multi-tooling.md](./17-multi-tooling.md) | [~] Em implementação (`.claude/` + `.codex/` espelhados; git hooks canônicos via `.githooks/` + `tools/install-hooks.sh`; `tools/install-mcp.sh`; `tools/sync-agents.ts` gera `.codex/agents/*.toml` a partir de `.claude/agents/*.md`; `pnpm check:all` valida sync + drift) |

## P1 — Estrutural

| ID | Correção | Arquivo | Status |
|----|----------|---------|--------|
| P1-1 | Simulador determinístico de sync/conflito + fila de revisão humana | [08-sync-simulator.md](./08-sync-simulator.md) | [ ] Proposto (revisado) |
| P1-2 | Política de Tier 3 com provenance/attestation (SLSA/sigstore) | [09-cloud-agents-policy.md](./09-cloud-agents-policy.md) | [ ] Proposto (revisado) |
| P1-3 | Diretório `/compliance/` canônico | [02-arquitetura.md](./02-arquitetura.md) | [~] Em implementação (árvore canônica criada no bootstrap; scaffolds de `approved-claims.md`, `guardrails.md`, `cloud-agents-policy.md` em v0.1.0-draft) |
| P1-4 | Roadmap em fatias verticais V1–V5 | [10-roadmap.md](./10-roadmap.md) | [ ] Proposto |

## P2 — Refinamento

| ID | Correção | Onde | Status |
|----|----------|------|--------|
| P2-1 | Nomenclatura de agentes (frontmatter padrão) | [03-agentes.md](./03-agentes.md) | [ ] Proposto |
| P2-2 | Slash-commands regulatórios (`/spec-norm-diff`, `/ac-evidence`, `/claim-check`, `/tenant-fuzz`, `/emit-cert-dry`) | pendente | [ ] Não iniciado |
| P2-3 | Dashboard de observabilidade do harness | pendente | [ ] Não iniciado |
| P2-4 | Reescrever texto do Tier 3 no `HARNESS_DESIGN.md` raiz | — | [ ] Não iniciado |

## Legenda de status

- `[ ] Proposto` — decisão escrita neste diretório, aguarda revisão humana.
- `[x] Aprovado` — revisado e aceito; pode ser implementado.
- `[~] Em implementação` — aprovado, código sendo criado.
- `[✓] Implementado` — código em produção + dossiê arquivado.
- `[!] Rejeitado` — revisor vetou; motivo em comentário.

## Fluxo de aprovação

1. Revisor lê o arquivo apontado.
2. Se ok → troca `[ ] Proposto` por `[x] Aprovado` + assinatura (`— nome/data`).
3. Se pedir ajuste → comenta no arquivo, mantém status em `Proposto`.
4. Quando **todos os P0** estiverem `Aprovado`, `HARNESS_DESIGN.md` raiz é reescrito a partir deste diretório.
5. P1 segue mesmo fluxo; P2 pode ser deferido para pós-V1.

## Dependências de implementação

```
P0-1 (backend) ─┬─► P0-2 (normative package) ─► P0-3 (dossiê) ─► P0-9 (runbooks)
                ├─► P0-4 (guardrails) ─► P0-9 (runbooks)
                └─► P0-6 (governance gate) ─► P0-8 (escalation matrix)

P0-3 (dossiê) ─► P0-10 (cascata L0→L5) ─► P0-11 (redundância/loops)

P0-5 (copy-lint) — independente, pode rodar em paralelo
P0-7 (budgets) — transversal, ativado já no bootstrap do harness

P1-1, P1-2 — dependem de P0-1 estar em pé
P1-3 — ativado junto com P0-3
P1-4 — deve ser aprovado antes de qualquer V1 começar
```

## Última atualização

- `2026-04-19` — proposta inicial criada em `harness/`.
- `2026-04-19` — emendas P0-7, P0-8, P0-9 adicionadas após 2ª rodada de revisão; P1-1 e P1-2 revisados.
- `2026-04-19` — emendas P0-10 (cascata L0→L5) e P0-11 (redundância/loops) adicionadas após 3ª rodada; D8 adicionado a P0-8; Gate 7 adicionado a P0-4.
- `2026-04-19` — emenda P0-12 adicionada após decisão de operar sem especialistas humanos contratados: 3 agentes auditores (metrology-auditor, legal-counsel, senior-reviewer) substituem humanos em 1ª linha; D9 adicionado a P0-8; L5 em P0-10 atualizado; checklist de P0-6 inclui 3 pareceres.
- `2026-04-19` — emenda P0-13 adicionada: operação dual Claude Code + Codex CLI com `AGENTS.md` canônico na raiz; `.claude/` e `.codex/` são espelhos gerados; roteamento por tipo de tarefa documentado.
- `2026-04-19` — **P0-13 gaps fechados**: `.githooks/pre-commit` canônico (via `core.hooksPath`) roda copy-lint + ownership-lint independente da CLI; `tools/install-hooks.sh` idempotente; `tools/install-mcp.sh` registra MCPs em Claude e Codex; `tools/check-agents-drift.ts` detectou e corrigiu 11 divergências entre `.claude/agents` e `.codex/agents`; `pnpm check:drift` e `pnpm check:all` no root; onboarding em AGENTS.md §9 e CLAUDE.md.
- `2026-04-20` — **P0-13 sync automático implementado**: `tools/sync-agents.ts` gera os 13 `.codex/agents/*.toml` a partir de `.claude/agents/*.md` usando apenas campos aceitos pelo Codex CLI 0.121+; `pnpm sync:agents:check` entra em `pnpm check:all`; teste `tools/sync-agents.test.ts` cobre modo check e regeneração.
- `2026-04-19` — **P0-4 Gate 6 funcional**: `packages/ownership-lint` com 4 regras OWN-001..OWN-004 detectando imports cruzando boundaries; esqueletos de `@afere/engine-uncertainty` e `@afere/normative-rules` criados; hook `.claude/hooks/ownership-lint.sh` real adicionado ao PreCommit; slash-command `/ownership-check`. Teste-de-fogo: 3 arquivos temporários com imports proibidos geraram 4 errors (OWN-001 x2, OWN-002 x1, OWN-004 x1); pós-cleanup retorna 0.
- `2026-04-20` — **P0-4 Gate 1 primeira fatia funcional**: `packages/db/tools/tenant-lint` detecta SQL cru e `CREATE POLICY` em tabelas multitenant sem `organization_id`; hook `.claude/hooks/tenant-safe-sql.sh` deixou de ser stub e chama `pnpm tenant-lint` no delta; `pnpm check:all` roda testes do tenant-lint via `pnpm test:tools`.
- `2026-04-20` — **P0-4 Gate 2 smoke funcional**: `evals/tenancy/rls/rls-smoke.sql` executa em Postgres real via `pnpm test:rls` e valida select cross-tenant, insert com `organization_id` forjado, join cross-tenant e tentativa de `SET ROLE` para outro papel.
- `2026-04-20` — **P0-4 Gate 3 primeira fatia funcional**: `@afere/audit-log` implementa `computeAuditHash` + `verifyAuditHashChain` com canonicalização de payload; CLI `pnpm audit-chain:verify <audit.jsonl>` valida artefatos JSONL; hook `.claude/hooks/audit-hash-chain.sh` deixou de ser stub e chama o verificador para arquivos auditáveis no delta.
- `2026-04-20` — **P0-4 Gate 4 primeira fatia funcional**: `tools/worm-check.ts` varre Terraform e bloqueia buckets regulatórios S3/B2/GCS sem Object Lock/File Lock/retention lock; `pnpm worm-check` entrou em `pnpm check:all`.
- `2026-04-20` — **P0-4 Gate 5 primeira fatia funcional**: `evals/tenancy/fuzz/cross-tenant-fuzz.sql` executa 500 seeds determinísticos contra RLS via `pnpm test:fuzz`; valida leitura cross-tenant e inserts com `organization_id` forjado. RBAC aplicacional fica pendente até auth/RBAC real no backend.
- `2026-04-20` — **P0-3 primeira fatia funcional + Gate 7 base**: `compliance/validation-dossier/requirements.yaml` vira fonte de requisitos ativados; `tools/validation-dossier.ts` valida schema/links, gera `traceability-matrix.yaml` e `coverage-report.md`, e seleciona testes de regressão para requisitos `blocker`/`high` por `critical_paths`; `pnpm check:all` passa a validar matriz atualizada. Cobertura honesta atual: 3/22 critérios do PRD §13.
- `2026-04-20` — **P0-2 primeira fatia funcional**: `packages/normative-rules/src/package.ts` implementa hash canônico SHA-256, assinatura/verificação Ed25519, loader de diretório `package.yaml` + `package.sha256` + `package.sig` e falha fechada para pacote sem assinatura; testes usam chave efêmera, sem chave privada versionada. KMS real e pacote aprovado baseline ficam pendentes.
- `2026-04-19` — **P0-5 implementação inicial**: `packages/copy-lint` com 8 regras regex (CL-001..CL-008), CLI com resolução de workspace root, hook PreCommit fail-closed real, slash-command `/claim-check`. Teste-de-fogo detectou os claims proibidos no wireframe do `PRD.md`; finding rastreado em `compliance/validation-dossier/findings/2026-04-19-prd-claims-proibidos.md`.
- `2026-04-19` — **P0-1 scaffold implementado e validado**: pnpm workspace + turbo; `packages/db` Prisma 5 scaffold; `packages/contracts` tRPC 11 + zod; `apps/api` Fastify 5 + dotenv + CORS + pino; `docker-compose.yml` (postgres 16-alpine :5433, redis 7-alpine :6380); Dockerfile multi-stage. Typecheck global e E2E (`/healthz`, `/readyz`, `/trpc/health.ping`) verdes.
- `2026-04-19` — **ADRs 0001, 0002, 0003 aprovados** pelo usuário: Fastify + TS; sync event-log + idempotency + fila humana; Hostinger VPS KVM 4 + Backblaze B2 Object Lock + AWS KMS sa-east-1 + Grafana/Axiom. Camada 2 (scaffold `apps/api`) destravada.
- `2026-04-19` — produto renomeado **Kalibrium → Aferê** (placeholder virou nome oficial; slug técnico `afere`).
- `2026-04-19` — **bootstrap Camada 1 executado**: `CLAUDE.md` raiz; árvore do monorepo (`apps/`, `packages/`, `evals/`, `compliance/`, `specs/`, `adr/`, `infra/`) com 34 READMEs; 13 subagentes em `.claude/agents/*.md` + espelho em `.codex/agents/*.toml`; `.claude/settings.json` + `.codex/config.toml` com hooks, allowlist, MCPs e budgets; 6 slash-commands (`spec-new`, `ac-check`, `claim-check`, `emit-cert-dry`, `release-norm`, `tenant-fuzz`); 9 hooks Claude + 4 hooks Codex (stubs); scaffolds `compliance/approved-claims.md`, `compliance/guardrails.md`, `compliance/cloud-agents-policy.md`. P0-13 e P1-3 marcados `[~] Em implementação`; demais P0 continuam `[ ] Proposto` (exigem código de aplicação — Camadas seguintes).
