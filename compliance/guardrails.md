# compliance/guardrails.md — 7 gates duros

> **Owner:** `product-governance` (coordenação); executores: `db-schema`, `backend-api`, `lgpd-security`, `regulator`.
> Espelha `harness/05-guardrails.md` — este arquivo é a referência **executável** (link para scripts e jobs), aquele é a **decisão arquitetural**.

## Status

- **Versão:** 0.1.0-bootstrap (2026-04-19)
- **P0-4:** `[ ] Proposto` — implementação dos 7 gates pendente.

## Gate 1 — Tenant-safe SQL linter

**Regra:** nenhum SQL cru em `packages/db` ou `apps/api` pode faltar filtro de tenant.

- **Implementação:** lint customizado em `packages/db/lint/tenant-safe-sql.ts` + hook PreCommit (`.claude/hooks/tenant-safe-sql.sh`) + CI job.
- **Owner:** `db-schema`.
- **Falha:** commit bloqueado.

## Gate 2 — RLS policy tests

**Regra:** cada tabela multitenant tem policy RLS testada em `evals/tenancy/rls/`.

- **Implementação:** vitest roda queries com sessão de tenant A tentando ler dados do tenant B.
- **Owner:** `db-schema` + `qa-acceptance`.
- **Falha:** release bloqueado.

## Gate 3 — Audit log hash-chain verifier

**Regra:** `audit_log` é append-only com `hash = hash(prev_hash || payload)`.

- **Implementação:** job diário recomputa a cadeia + compara com checkpoint assinado em KMS.
- **Owner:** `db-schema` + `lgpd-security`.
- **Falha:** incidente automático + runbook `harness/13-runbooks-recovery.md`.

## Gate 4 — WORM storage check

**Regra:** bucket de certificados emitidos e de audit checkpoints tem *object lock* / retenção imutável.

- **Implementação:** validação em `terraform plan` + smoke test pós-deploy.
- **Owner:** `lgpd-security` + `product-governance`.
- **Falha:** deploy bloqueado (*fail-closed*).

## Gate 5 — Fuzz semanal cross-tenant

**Regra:** suíte de fuzz gera 500 payloads cross-tenant; 100% bloqueados por RLS + RBAC.

- **Implementação:** `evals/tenancy/fuzz/` + slash-command `/tenant-fuzz`.
- **Owner:** `qa-acceptance`.
- **Frequência:** semanal + antes de release.

## Gate 6 — Lint de ownership de domínio

**Regra:**
- Regra de emissão só em `apps/api/src/domain/emission/**`.
- `apps/web`, `apps/portal`, `apps/android` não importam `packages/normative-rules` ou `packages/engine-uncertainty`.

- **Implementação:** lint customizado em `packages/db/lint/ownership.ts`.
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
- Full regression suite (REQs `blocker` + `high`).
- Snapshot-diff de 30 certificados canônicos (10 por perfil A/B/C).
- Property tests com N por criticidade (`blocker=500 seeds`).
- Flake gate noturno (10× por noite; flake > 0% em blocker = issue SLA 48h).

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

1. **Gate 6** — imediato, lint estático, hook PreToolUse.
2. **Gate 1** — imediato após Prisma scaffold (P0-1).
3. **Gates 2, 3** — com primeira migration de audit log.
4. **Gate 5** — com primeira área blocker implementada.
5. **Gate 4** — pré-deploy da V1 (fatia vertical).
6. **Gate 7** — ativado no dia que V1 entrar em área blocker.
