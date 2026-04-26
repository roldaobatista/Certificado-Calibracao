# 0099 - Prontidao de runtime RLS e papel de aplicacao

## Contexto

A cobertura estrutural de RLS das migrations foi fechada em `0098`, mas a analise seguinte identificou uma lacuna diferente: o compose de desenvolvimento ainda conecta `apps/api` com o dono do banco (`afere`). Em PostgreSQL, o dono da tabela pode contornar RLS quando a tabela nao esta com `FORCE ROW LEVEL SECURITY`.

Aplicar `FORCE ROW LEVEL SECURITY` sem preparar o backend tambem seria inseguro: login por e-mail, leitura de sessao por hash e bootstrap de tenant ainda sao fluxos globais que precisam configurar `app.current_organization_id` de forma transacional antes de consultar tabelas protegidas.

## Objetivo

Transformar o risco de owner-bypass em um risco explicito, rastreado e bloqueado contra adoção parcial:

1. documentar a separacao entre `DATABASE_OWNER_URL` e `DATABASE_APP_URL`;
2. registrar que `afere_app` sera a role de runtime sem bypass RLS;
3. impedir que `FORCE ROW LEVEL SECURITY` entre em migration antes de existir contexto transacional de tenant no pacote DB;
4. impedir que `DATABASE_URL` seja trocada para `afere_app` antes da mesma preparacao.

## Escopo

- Criar `tools/rls-runtime-readiness-check.ts`.
- Expor `pnpm rls-runtime-readiness-check`.
- Rodar o gate em `pnpm check:all` e no pre-commit quando arquivos de runtime RLS mudarem.
- Arquivar finding formal em `compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk.md`.
- Documentar em `.env.example` a separacao owner/app e o uso futuro de `app.current_organization_id`.

## Fora de escopo

- Ativar `FORCE ROW LEVEL SECURITY` nas tabelas existentes.
- Trocar `docker-compose.yml` para `DATABASE_URL=afere_app`.
- Implementar `packages/db/src/tenant-context.ts` nesta fatia.
- Reescrever persistencias Prisma para transacoes tenant-bound.

## Regras

1. Runtime com o dono do banco so pode existir se o risco owner-bypass estiver registrado em spec, ADR e finding.
2. `FORCE ROW LEVEL SECURITY` so pode aparecer em migration depois de existir helper transacional em `packages/db/src/tenant-context.ts`.
3. `DATABASE_URL` com role diferente de `POSTGRES_USER` no compose so pode aparecer depois do mesmo helper transacional.
4. `.env.example` deve declarar `DATABASE_OWNER_URL`, `DATABASE_APP_URL` e `app.current_organization_id`.

## Criterios de aceite

- O teste novo falha antes da implementacao do checker.
- `pnpm exec tsx --test tools/rls-runtime-readiness-check.test.ts` passa.
- `pnpm rls-runtime-readiness-check` passa no estado atual, mantendo o risco owner-bypass explicito.
- `pnpm check:all` inclui o novo gate.
- `.githooks/pre-commit` aciona o hook quando runtime RLS, docs ou migrations mudarem.
