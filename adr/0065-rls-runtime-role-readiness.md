# ADR 0065 - Prontidao de runtime RLS e papel de aplicacao

## Status

Aceito

## Contexto

O gate `rls-policy-check` garante que tabelas multitenant tenham RLS e policy no historico SQL. Essa cobertura nao fecha o risco operacional de owner-bypass: enquanto `apps/api` conecta como dono das tabelas, PostgreSQL pode ignorar RLS em tabelas sem `FORCE ROW LEVEL SECURITY`.

A ativacao imediata de `FORCE ROW LEVEL SECURITY` tambem nao e segura. O backend ainda possui fluxos globais de login, sessao e bootstrap que nao sabem o tenant antes da primeira consulta. Esses fluxos precisam de uma camada transacional que configure `app.current_organization_id` sem vazar contexto entre conexoes.

## Decisao

Adicionar um gate de prontidao de runtime RLS antes da mudanca disruptiva:

1. `DATABASE_OWNER_URL` fica documentada como credencial de migrations/seed.
2. `DATABASE_APP_URL` fica documentada como destino futuro da role `afere_app`, sem bypass RLS.
3. O risco owner-bypass atual fica registrado em spec, ADR e finding do dossie.
4. `tools/rls-runtime-readiness-check.ts` falha se `FORCE ROW LEVEL SECURITY` for introduzido antes de `packages/db/src/tenant-context.ts`.
5. O mesmo gate falha se `docker-compose.yml` passar a usar role de aplicacao em `DATABASE_URL` antes do tenant context.
6. O gate entra em `check:all` e no pre-commit.

## Consequencias

### Positivas

- A lacuna de owner-bypass deixa de ser silenciosa.
- Evita uma migracao de `FORCE ROW LEVEL SECURITY` que quebraria login, sessao ou bootstrap sem teste dedicado.
- Cria trilha clara para a proxima fatia: helper transacional, refactor das persistencias e depois ativacao de `afere_app`/FORCE RLS.

### Limitacoes honestas

- Esta decisao ainda nao ativa `FORCE ROW LEVEL SECURITY`.
- Esta decisao ainda nao troca o runtime do compose para `afere_app`.
- A protecao efetiva contra owner-bypass em runtime depende da proxima fatia implementar `app.current_organization_id` transacional e executar testes reais com role sem bypass.
