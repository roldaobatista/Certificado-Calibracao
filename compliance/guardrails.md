# compliance/guardrails.md — 7 gates duros

> **Owner:** `product-governance` (coordenação); executores: `db-schema`, `backend-api`, `lgpd-security`, `regulator`.
> Espelha `harness/05-guardrails.md` — este arquivo é a referência **executável** (link para scripts e jobs), aquele é a **decisão arquitetural**.

## Status

- **Versão:** 0.2.0-bootstrap (2026-04-20)
- **P0-4:** `[~] Em implementação` — Gates 1, 2, 3, 4, 5, 6 funcionais em primeiras fatias; Gate 7 tem dossiê e seleção de regressão, mas snapshot-diff e flake gate ainda pendem.

## Gate 1 — Tenant-safe SQL linter

**Regra:** nenhum SQL cru em `packages/db` ou `apps/api` pode faltar filtro de tenant.

- **Implementação:** lint customizado em `packages/db/tools/tenant-lint/src/cli.ts` + hook PreCommit (`.claude/hooks/tenant-safe-sql.sh`) + CI job futuro.
- **Como rodar local:** `pnpm tenant-lint` ou `pnpm tenant-lint apps/api/src/foo.ts packages/db/prisma/migrations/001/migration.sql`.
- **Owner:** `db-schema`.
- **Falha:** commit bloqueado com `TENANT-LINT: query em <tabela> não filtra por organization_id`.

## Gate 2 — RLS policy tests

**Regra:** cada tabela multitenant tem policy RLS testada em `evals/tenancy/rls/`.

- **Implementação:** smoke executável em `evals/tenancy/rls/rls-smoke.sql` + `evals/tenancy/rls/rls-smoke.test.ts`.
- **Como rodar local:** `docker compose up -d postgres && pnpm test:rls`.
- **Owner:** `db-schema` + `qa-acceptance`.
- **Falha:** release bloqueado.

### Gate 2.1 — RLS runtime readiness

**Regra:** `FORCE ROW LEVEL SECURITY` e runtime com role de aplicação só entram depois de contexto transacional por tenant.

- **Implementação:** `tools/rls-runtime-readiness-check.ts` + hook PreCommit (`.claude/hooks/rls-runtime-readiness-check.sh`).
- **Como rodar local:** `pnpm rls-runtime-readiness-check`.
- **Owner:** `db-schema` + `lgpd-security`.
- **Falha:** commit bloqueado com `RUNTIME-RLS-*`.
- **Limitação honesta:** o compose dev ainda usa owner DB; o risco owner-bypass está registrado em `compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk.md` até a fatia de `afere_app` + `app.current_organization_id` transacional.

## Gate 3 — Audit log hash-chain verifier

**Regra:** `audit_log` é append-only com `hash = hash(prev_hash || payload)`.

- **Implementação:** verificador determinístico em `packages/audit-log/src/verify.ts` + CLI `pnpm audit-chain:verify <audit.jsonl>` + hook PreCommit (`.claude/hooks/audit-hash-chain.sh`) para artefatos JSONL.
- **Owner:** `db-schema` + `lgpd-security`.
- **Falha:** incidente automático + runbook `harness/13-runbooks-recovery.md`.

## Gate 4 — WORM storage check

**Regra:** bucket de certificados emitidos e de audit checkpoints tem *object lock* / retenção imutável.

- **Implementação:** scanner estático de Terraform em `tools/worm-check.ts` (`pnpm worm-check`) para S3 Object Lock, Backblaze B2 File Lock e GCS retention lock + smoke test pós-deploy futuro.
- **Owner:** `lgpd-security` + `product-governance`.
- **Falha:** deploy bloqueado (*fail-closed*).

## Gate 5 — Fuzz semanal cross-tenant

**Regra:** suíte de fuzz gera 500 payloads cross-tenant; 100% bloqueados por RLS + RBAC.

- **Implementação:** fuzz RLS determinístico em `evals/tenancy/fuzz/cross-tenant-fuzz.sql` + `pnpm test:fuzz`; RBAC aplicacional pendente até auth/RBAC existir em `apps/api`.
- **Owner:** `qa-acceptance`.
- **Frequência:** semanal + antes de release.

## Gate 6 — Lint de ownership de domínio

**Regra:**
- Regra de emissão só em `apps/api/src/domain/emission/**`.
- `apps/web`, `apps/portal`, `apps/android` não importam `packages/normative-rules` ou `packages/engine-uncertainty`.

- **Implementação:** lint customizado em `packages/ownership-lint/src/cli.ts` + hook PreCommit (`.claude/hooks/ownership-lint.sh`).
- **Owner:** `backend-api`.
- **Falha:** build bloqueado com mensagem de ownership violado.

## Gate 7 — Full regression obrigatória em área crítica

**Regra:** mudança em área blocker roda 100% dos REQs da área, não só os afetados pelo diff.

**Áreas blocker (lista fechada; ampliação exige ADR):**
- `apps/api/src/domain/emission/**`
- `apps/api/src/domain/audit/**`
- `packages/engine-uncertainty/**`
- `packages/normative-rules/**`
- `packages/audit-log/**`

**Componentes:**
- Full regression suite (REQs `blocker` + `high`) selecionada por `tools/validation-dossier.ts critical-tests`.
- Dossiê formal em `compliance/validation-dossier/requirements.yaml` + `traceability-matrix.yaml`.
- Snapshot-diff de 30 certificados canônicos (10 por perfil A/B/C) — pendente até renderer de certificado existir.
- Property tests com N por criticidade (`blocker=500 seeds`).
- Flake gate noturno (10× por noite; flake > 0% em blocker = issue SLA 48h) — pendente de CI agendado.

**Owner:** `qa-acceptance` + `product-governance`.
**Falha:** release bloqueado.

## Dependências entre gates

```
Gate 1 (SQL) ─┬─► Gate 2 (RLS)
              └─► Gate 5 (fuzz)

Gate 3 (hash-chain) ─► Gate 4 (WORM)

Gate 6 (ownership) — independente, hook PreToolUse

Gate 7 (full regression) — consome todos os anteriores como sinal
```

## Prioridade de implementação

1. **Gate 6** — imediato, lint estático, hook PreCommit.
2. **Gate 1** — imediato após Prisma scaffold (P0-1).
3. **Gates 2, 3** — com primeira migration de audit log.
4. **Gate 5** — com primeira área blocker implementada.
5. **Gate 4** — pré-deploy da V1 (fatia vertical).
6. **Gate 7** — ativado no dia que V1 entrar em área blocker.
