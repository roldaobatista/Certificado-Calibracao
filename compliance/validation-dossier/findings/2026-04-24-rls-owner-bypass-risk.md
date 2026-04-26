# Finding - RLS owner-bypass em runtime de desenvolvimento

## Status

Aberto, mitigado por gate de prontidao.

## Contexto

O compose de desenvolvimento ainda usa `DATABASE_URL=postgresql://afere:afere@postgres:5432/afere?schema=public` para `apps/api`. A role `afere` e tambem `POSTGRES_USER`, portanto atua como dona/superuser do banco local.

Em PostgreSQL, o dono da tabela pode contornar RLS quando a tabela nao esta com `FORCE ROW LEVEL SECURITY`. Isso cria risco owner-bypass: as policies versionadas existem, mas uma conexao privilegiada pode nao exercitar a mesma barreira que a role de aplicacao futura (`afere_app`).

## Impacto

- Risco de falsa confianca em testes que filtram por `organization_id` na aplicacao, mas nao executam como role sem bypass.
- Risco de ativar `FORCE ROW LEVEL SECURITY` de forma abrupta e quebrar login, sessao e bootstrap, porque esses fluxos precisam descobrir ou criar o tenant antes de configurar `app.current_organization_id`.

## Mitigacao nesta fatia

- `specs/0099-rls-runtime-role-readiness.md` define o plano incremental.
- `adr/0065-rls-runtime-role-readiness.md` registra a decisao.
- `.env.example` documenta `DATABASE_OWNER_URL`, `DATABASE_APP_URL`, `afere_app` e `app.current_organization_id`.
- `tools/rls-runtime-readiness-check.ts` impede `FORCE ROW LEVEL SECURITY` ou runtime com `afere_app` antes de `packages/db/src/tenant-context.ts`.
- `pnpm rls-runtime-readiness-check` entra em `pnpm check:all` e no pre-commit.

## Proximos passos

1. Criar `packages/db/src/tenant-context.ts` com transacao que define `app.current_organization_id` via `set_config(..., true)`.
2. Adaptar login e sessao para descoberta controlada por e-mail/token sem abrir leitura cross-tenant.
3. Adaptar bootstrap para gerar `organization.id` antes do insert e configurar contexto.
4. Executar testes reais com role `afere_app` sem bypass.
5. Introduzir `FORCE ROW LEVEL SECURITY` em migration somente depois das verificacoes acima.
