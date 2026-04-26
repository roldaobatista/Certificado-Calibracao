# 05 — Guardrails de multitenancy e trilha imutável

> **P0-4**: promove exigências do PRD §6.6, §7.10, §11.3 de "eval genérica" para **hard gates de PR**.

## Gate 1 — Tenant-safe SQL linter

**Regra:** toda query ou policy que toca tabela multitenant precisa conter `organization_id` no WHERE/ON ou em política RLS.

- Owner: `db-schema`.
- Implementação: custom lint em `packages/db/tools/tenant-lint/` + CI step.
- Cobertura: `packages/db/**/*.sql`, `packages/db/prisma/**`, `apps/api/src/**/*.{ts,sql}`.
- Falha de build com mensagem específica: `TENANT-LINT: query em <arquivo:linha> não filtra por organization_id`.

## Gate 2 — RLS policy tests

**Regra:** toda tabela multitenant tem policy RLS; suite de testes valida isolamento com ≥ 2 tenants sintéticos.

- Localização: `evals/tenancy/`.
- Cenários obrigatórios:
  - `select` de tenant B retorna zero linhas quando sessão é tenant A.
  - `insert` com `organization_id` forjado via payload falha.
  - `join` cross-tenant é impossível.
  - Escalação de privilégio via `SET ROLE` falha *fail-closed*.
- CI: job `rls-tests` é **required check** para merge.

### Gate 2.1 — Prontidão de runtime RLS

**Regra:** `FORCE ROW LEVEL SECURITY` e `DATABASE_URL` com role de aplicação (`afere_app`) só podem entrar depois de existir contexto transacional por tenant (`app.current_organization_id`) no pacote DB.

- Owner: `db-schema` + `lgpd-security`.
- Implementação: `tools/rls-runtime-readiness-check.ts` + hook `.claude/hooks/rls-runtime-readiness-check.sh`.
- Cobertura: `docker-compose.yml`, `.env.example`, migrations, spec/ADR/finding de owner-bypass e futuro `packages/db/src/tenant-context.ts`.
- Falha de build com mensagem específica: `RUNTIME-RLS-*`.
- Limitação honesta: até a fatia de `afere_app`, compose dev segue com owner DB documentado em `compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk.md`.

## Gate 3 — Audit log hash-chain verifier

**Regra:** audit log é append-only com hash-chain; cada registro contém `hash(prev_hash || payload)`.

- Owner: `db-schema` + `lgpd-security`.
- Job diário recomputa a cadeia completa e compara com checkpoint assinado.
- Divergência → bloqueia release e abre incidente automático.
- Checkpoints periódicos são assinados com chave KMS e gravados em storage WORM.

## Gate 4 — WORM storage check

**Regra:** bucket de certificados emitidos e de audit checkpoints tem *object lock* / retenção imutável.

- Verificação em IaC review (Terraform plan) + smoke test pós-deploy.
- Falha de configuração = deploy bloqueado (*fail-closed*).
- Cobre: S3 Object Lock / GCS Bucket Lock / Azure Immutable Blob.

## Gate 5 — Fuzz semanal cross-tenant

**Regra:** pipeline agendada injeta payloads adversariais tentando quebrar isolamento.

- Cenários: IDs numéricos adjacentes, UUID v4 gerados aleatoriamente, SQL injection em filtros, tentativas de *parameter tampering* em JWT.
- Relatório em `compliance/validation-dossier/evidence/fuzz-<data>/`.
- Regressão de isolamento = release bloqueado até *root cause* documentado.

## Gate 6 — Lint de ownership de domínio

**Regra:** regra de emissão só existe em `apps/api/src/domain/emission/**`.

- Lint customizado detecta *imports* de `packages/normative-rules` feitos por `apps/web`, `apps/portal` ou `apps/android`.
- Também detecta lógica de cálculo de incerteza duplicada fora de `packages/engine-uncertainty`.
- Falha de build com mensagem de ownership violado.

## Gate 7 — Full regression obrigatória em área crítica

**Regra:** qualquer mudança em áreas críticas dispara execução de **100% dos REQs** da área, não apenas os afetados pelo diff. Ver `14-verification-cascade.md` (L4).

Áreas críticas (lista fechada, ampliação exige ADR):
- `apps/api/src/domain/emission/**`
- `apps/api/src/domain/audit/**`
- `packages/engine-uncertainty/**`
- `packages/normative-rules/**`
- `packages/audit-log/**`

Componentes obrigatórios:
- **Full regression suite**: todos os REQs em `requirements.yaml` marcados `criticality: blocker` ou `high` rodam.
- **Snapshot-diff de certificados**: 30 certificados canônicos (10 por perfil A/B/C) são regerados e comparados byte-a-byte; diff = bloqueio + investigação.
- **Property tests com N por criticidade**: ver `15-redundancy-and-loops.md` §1 (blocker=500 seeds).
- **Flake gate noturno**: testes rodam 10× à noite; flake > 0% em blocker = issue SLA 48h (ver `15-redundancy-and-loops.md` §2).

Mudança legítima de snapshot exige aprovação de `regulator` + `product-governance` e ADR explicando o que mudou regulatoriamente.

## Documentação

Cada gate tem página correspondente em `compliance/guardrails.md` com:
- Regra em uma linha.
- Implementação (arquivo + comando).
- Como rodar local (dev fix antes do CI).
- Exemplos de pass e fail.

## Prioridade de implementação

1. Gate 1 (SQL linter) — rápido, alto impacto.
2. Gate 6 (ownership lint) — rápido, previne deriva estrutural.
3. Gate 2 (RLS tests) — médio, alto valor.
4. Gate 3 (hash-chain) — médio, imprescindível para audit.
5. Gate 7 (full regression) — ativa junto com o 1º REQ blocker implementado.
6. Gate 4 (WORM) — depende de IaC em pé.
7. Gate 5 (fuzz) — último, ativa após baseline estável.
