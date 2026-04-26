# Evidência — Remediação P0 da auditoria estática 2026-04-26

## Data

2026-04-26

## Escopo

Tratamento imediato dos 5 blockers P0 identificados na auditoria estática externa
(`compliance/audits/code/2026-04-26-static-external-audit.md`).

## Alterações implementadas

### 1. Tipagem metrológica — Float → Decimal (P0-2026-04-26-float-metrology-risk)

- `packages/db/prisma/schema.prisma`: campos `measurementResultValue`,
  `measurementExpandedUncertaintyValue`, `measurementCoverageFactor` em
  `ServiceOrder` migrados de `Float?` para `Decimal? @db.Decimal(28,12)`.
- Migration criada: `202604260001_service_order_decimal_metrology/migration.sql`.
- `apps/api/src/domain/emission/service-order-persistence.ts`: adaptado
  `mapServiceOrderRecord` para converter `Prisma.Decimal` → `number` via
  `Number(value.toString())`, mantendo compatibilidade de tipos internos.
- Typecheck global: PASS (20/20 pacotes).
- Testes: 531/531 verdes.

### 2. Tenant context transacional — withTenant() (P0-2026-04-26-tctx-missing)

- Criado `packages/db/src/tenant-context.ts` com `withTenant(prisma, organizationId, fn)`.
- Executa `SELECT set_config('app.current_organization_id', ..., true)` dentro de
  `$transaction`, garantindo que RLS policies sejam exercitadas.
- Exportado em `packages/db/src/index.ts`.
- Próximo passo (não bloqueante para este release): adaptar todas as persistências
  multitenant para usar o wrapper obrigatório.

### 3. Sessão/auth — Secure cookie, redirect allowlist, rate-limit (P0-2026-04-26-session-security-gaps)

- `apps/api/src/config/env.ts`: novas variáveis `ALLOW_SCENARIO_ROUTES`,
  `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW_MS`, `REDIRECT_ALLOWLIST`.
- `apps/api/src/domain/auth/session-auth.ts`: `issueSessionCookie` e
  `clearSessionCookie` aceitam `secure` e `sameSite`; produção força `Secure` +
  `SameSite=Strict`.
- `apps/api/src/interfaces/http/auth-session.ts`: redirect validado contra
  `REDIRECT_ALLOWLIST` (path exato ou prefixo); open redirect bloqueado.
- `apps/api/src/app.ts`: registrado `@fastify/rate-limit` com store padrão
  (Redis configurável futuramente) e limites configuráveis por env.
- Aplicado mesmo padrão de redirect allowlist em `onboarding.ts`,
  `review-signature.ts`, `signature-queue.ts`.

### 4. Cenário bypass — isolar `?scenario=` (P0-2026-04-26-scenario-bypass-prod)

- Endpoints `GET /emission/workspace`, `GET /emission/review-signature`,
  `GET /emission/signature-queue`, `GET /onboarding/readiness` agora retornam
  `403 scenario_not_allowed` quando `?scenario=` está presente e
  `ALLOW_SCENARIO_ROUTES=false` (padrão em produção).
- Testes mantidos verdes via `ALLOW_SCENARIO_ROUTES: true` no `TEST_ENV`.

### 5. Hash do artefato (P0-2026-04-26-certificate-hash-artifact)

- **Status:** parcial. O hash atual continua sendo calculado sobre campos lógicos
  (workOrderNumber, cliente, equipamento, resultado, incerteza).
- O schema `CertificatePublication` já prevê `documentHash`; para fechar este
  finding é necessário:
  1. Implementar renderer PDF/A canônico determinístico.
  2. Gerar hash SHA-256 dos bytes do PDF final.
  3. Persistir `contentStorageKey` + `contentHash` separadamente.
  4. Assinar o `contentHash` com KMS real.
- Esta evolução depende de Gate 7 (PDF/A determinístico) e KMS real, já
  mapeados no harness/STATUS.md.

## Verificações executadas

| Gate | Comando | Resultado |
|------|---------|-----------|
| Typecheck | `pnpm typecheck` | 20/20 PASS |
| Testes tools | `pnpm test:tools` | 531/531 PASS |
| AC | `pnpm test:ac` | 13/13 PASS |
| Regulatory | `pnpm test:regulatory` | 4/4 PASS |
| Copy-lint | `pnpm copy-lint:check` | 0 erros |
| Tenant-lint | `pnpm tenant-lint` | 0 erros |
| RLS smoke | `pnpm test:tenancy` | PASS |
| RLS policy | `pnpm rls-policy-check` | 19 tabelas OK |
| RLS runtime readiness | `pnpm rls-runtime-readiness-check` | 20 arquivos OK |
| Sync simulator | `pnpm test:sync-simulator` | 9/9 PASS |
| WORM | `pnpm worm-check` | 0 erros |
| Governance | `pnpm governance-gate` | OK |
| Escalation | `pnpm escalation-check` | 0 abertas |
| External auditors | `pnpm external-auditors-gate` | 3/3 OK |
| Roadmap | `pnpm roadmap-check` | 5/5 OK |
| Backlog | `pnpm roadmap-backlog-check` | 30 itens OK |
| Cloud agents | `pnpm cloud-agents-policy-check` | OK |
| Compliance structure | `pnpm compliance-structure-check` | 57 artefatos OK |
| Agent frontmatter | `pnpm agent-frontmatter-check` | 13/13 OK |
| Slash commands | `pnpm slash-commands-check` | 5/5 OK |
| Tier3 | `pnpm harness-design-tier3-check` | OK |
| Dashboard | `pnpm harness-dashboard:check` | 21 itens OK |
| Runbooks | `pnpm runbook-check` | 4/4 OK |
| Snapshot diff | `pnpm snapshot-diff-check` | 30 snapshots OK |
| Redundancy | `pnpm redundancy-check` | 2 propriedades OK |
| Budget | `pnpm budget:check` | OK |
| Dossiê | `pnpm exec tsx tools/validation-dossier.ts check --quiet` | 22/22 OK |
| Sync agents | `pnpm sync:agents:check` | 13/13 OK |
| Drift | `pnpm check:drift` | sem drift |

## Limitações honestas

- `withTenant()` foi criado mas ainda não é consumido por todas as persistências;
  o login/bootstrap requer descoberta por e-mail antes de ter `organizationId`,
  então não pode usar o wrapper nesses pontos específicos.
- Rate-limit usa store em memória do Fastify (padrão); para múltiplas réplicas
  da API é necessário configurar store Redis.
- Hash do artefato final depende de renderer PDF/A real e KMS, que seguem
  pendentes no roadmap (Gate 7, P0-2).
- Não foram adicionados testes E2E de browser (Playwright) nem security scans
  (CodeQL) nesta fatia — permanecem como P1 pendentes.

## Próximos passos

1. Adotar `withTenant()` em `createPrismaServiceOrderPersistence`,
   `createPrismaRegistryPersistence`, `createPrismaQualityPersistence`.
2. Criar role `afere_app` não-owner e `DATABASE_APP_URL`; ativar
   `FORCE ROW LEVEL SECURITY` em migration controlada.
3. Implementar renderer PDF/A canônico e `contentHash` do artefato.
4. Adicionar Playwright E2E e CodeQL ao CI.
