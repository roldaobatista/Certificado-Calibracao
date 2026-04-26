# Finding — Tenant context transacional (`withTenant`) ainda não implementado

## Status

Parcialmente mitigado em 2026-04-26. `withTenant()` implementado e exportado; adoção nas persistências multitenant segue pendente.

## Contexto

As policies RLS em Postgres usam `current_setting('app.current_organization_id', true)`. O factory `createPrismaClient` cria um `PrismaClient` puro, sem configurar `SET LOCAL app.current_organization_id`. O `CorePersistence` filtra por `organizationId` na aplicação, mas isso não substitui a garantia do banco.

O finding `2026-04-24-rls-owner-bypass-risk.md` já documenta o risco de owner-bypass em dev. Este finding complementa: mesmo com role correta (`afere_app`), sem `SET LOCAL` transacional as policies RLS não serão exercitadas corretamente, resultando em falha ou retorno vazio.

## Impacto

- Isolamento multitenant depende exclusivamente de filtros aplicacionais.
- Risco de regressão para leitura/escrita cross-tenant se filtro for omitido em nova query.
- RLS vira gate estrutural (migrations) sem garantia runtime.

## Correção recomendada

1. Implementar `packages/db/src/tenant-context.ts` com `withTenant(organizationId, fn)`.
2. Dentro de `$transaction`, executar `SET LOCAL app.current_organization_id = ...`.
3. Proibir acesso direto ao PrismaClient nas camadas de persistência; exigir wrapper.
4. Adaptar login/bootstrap para descoberta controlada antes de contexto (e-mail/token).
5. Testes runtime que provem falha cross-tenant quando o contexto está ausente.
6. Somente então habilitar `FORCE ROW LEVEL SECURITY` e migrar para `DATABASE_APP_URL` com role não-owner.

## Rastreamento

- Spec: `specs/0099-rls-runtime-role-readiness.md`
- ADR: `adr/0065-rls-runtime-role-readiness.md`
- Gate: `tools/rls-runtime-readiness-check.ts`
- Finding relacionado: `2026-04-24-rls-owner-bypass-risk.md`
