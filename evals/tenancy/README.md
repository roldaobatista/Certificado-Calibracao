# evals/tenancy — RLS + anti-vazamento

## Gate 2 — RLS smoke

Comando local:

```bash
docker compose up -d postgres
pnpm test:rls
```

O teste `rls/rls-smoke.sql` cria um cenário transacional com dois tenants sintéticos e valida:

- `select` de tenant B retorna zero linhas quando a sessão é tenant A.
- `insert` com `organization_id` forjado falha por RLS.
- `join` cross-tenant não vaza linhas.
- tentativa de `SET ROLE` para outro papel falha quando a sessão está como papel de aplicação.

## Gate 5 — fuzz determinístico

Comando local:

```bash
docker compose up -d postgres
pnpm test:fuzz
```

O teste `fuzz/cross-tenant-fuzz.sql` executa 500 seeds determinísticos contra RLS:

- tenta ler linhas de tenant B a partir de uma sessão de tenant A;
- tenta inserir payloads forjados com `organization_id` de tenant B;
- falha se qualquer seed vazar ou se qualquer insert forjado passar.

Cobertura de RBAC aplicacional entra quando `apps/api` tiver auth/RBAC real.
