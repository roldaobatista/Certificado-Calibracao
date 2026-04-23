# Spec 0079 — V5 completa de Qualidade e governança regulatória avançada

## Contexto

A V4 fechou o acesso externo persistido ao certificado, com portal autenticado, QR público e reemissão controlada. A V5 precisa deixar de tratar Qualidade e governança regulatória como leituras demonstrativas isoladas, abrindo operação real sobre OS, certificados, trilha crítica e estado regulatório persistido do tenant.

## Objetivo

Fechar a V5 sobre registros persistidos do tenant autenticado com:

- não conformidades e trabalho não conforme ligados a OS, certificados e evidências reais;
- programa de auditoria interna com ciclos e follow-up sobre evidências persistidas;
- indicadores e hub gerencial derivados do núcleo operacional e da Qualidade ativa;
- análise crítica com reuniões, entradas automáticas e deliberações sobre dados reais;
- governança regulatória avançada materializada nas configurações da organização, com perfil regulatório, escopo/CMC, parecer jurídico e rito de release-norm coerentes com a operação.

## Escopo

- `packages/db/prisma/**`
- `apps/api/src/domain/quality/**`
- `apps/api/src/domain/settings/**`
- `apps/api/src/interfaces/http/{auth-session,nonconformities,nonconforming-work,internal-audit,quality-indicators,management-review,quality-hub,organization-settings}.ts`
- `apps/api/src/app.ts`
- `apps/api/src/app.test.ts`
- `apps/web/app/quality/**`
- `apps/web/app/settings/organization/page.tsx`
- `apps/web/src/quality/**`
- `apps/web/src/settings/**`
- `compliance/release-norm/v5.md`
- `compliance/validation-dossier/releases/v5.md`
- `harness/STATUS.md`

## Regras

- `?scenario=` continua existindo como fallback canônico; sem `scenario`, os módulos V5 preferem leitura persistida protegida por sessão.
- Somente `admin` e `quality_manager` podem alterar dados de Qualidade e governança regulatória; leitura persistida pode ser aberta também por `signatory` e `technical_reviewer`.
- Não conformidade e trabalho não conforme devem referenciar OS reais, ou falhar fechado quando a referência informada não pertencer ao tenant autenticado.
- Auditoria interna deve apontar para evidências persistidas do tenant, mesmo quando o ciclo ainda estiver em preparação.
- Indicadores V5 devem ser derivados do estado persistido do fluxo central, da Qualidade e das reemissões, sem depender apenas de snapshots demonstrativos.
- A análise crítica deve agregar automaticamente entradas mínimas de NCs, auditoria, indicadores, emissão/reemissão e perfil regulatório real.
- Perfil regulatório, escopo/CMC, parecer jurídico e governança normativa não podem viver apenas em texto estático: precisam aparecer em payload persistido do backend e sustentar a leitura real de `/settings/organization` e do hub da Qualidade.

## Aceite

- `GET /quality/nonconformities`, `GET /quality/nonconforming-work`, `GET /quality/internal-audit`, `GET /quality/indicators`, `GET /quality/management-review`, `GET /quality` e `GET /settings/organization` respondem com catálogos persistidos do tenant quando chamados sem `scenario` e com cookie válido.
- `POST /quality/nonconformities/manage`, `POST /quality/nonconforming-work/manage`, `POST /quality/internal-audit/manage`, `POST /quality/management-review/manage` e `POST /settings/organization/manage` persistem ações mínimas reais da V5 e preservam isolamento por tenant.
- O hub da Qualidade deixa de reportar apenas leituras demonstrativas e passa a refletir contagens reais de NCs, follow-up, reuniões e indicadores do tenant autenticado.
- A tela de configurações da organização expõe estado real do perfil regulatório, escopo/CMC, parecer jurídico e governança normativa sem regressão involuntária para `?scenario=`.
- O seed local demonstra V5 com pelo menos uma NC, um caso de trabalho não conforme, um ciclo de auditoria, uma reunião de análise crítica e um perfil regulatório persistidos.
- A suíte automatizada verifica leitura persistida dos módulos V5, alteração autenticada em `manage` e coerência do hub/indicadores com a base real.

## Verificação

- `pnpm --filter @afere/db exec prisma generate --no-engine`
- `pnpm --filter @afere/api typecheck`
- `pnpm --filter @afere/web typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
