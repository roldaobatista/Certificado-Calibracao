# ADR-0002 — Modelo de multi-tenancy

> **Status:** rascunho (17/05/2026) — bloqueante do Portão 2 da ADR-0001
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditor 2 da 1ª auditoria de 10 agentes + Parecer 1 + Parecer 8 da 2ª — vetores de vazamento cross-tenant que ADR-0001 promete cobrir mas não fecha.
> **Depende de:** ADR-0001 v2 (stack Django + PostgreSQL)

---

## Contexto

ADR-0001 v2 recomenda **schema-shared + RLS PostgreSQL** pra 100-5000 tenants no VPS KVM 4. Auditor 2 levantou 3 vetores críticos + 5 altos de fuga que precisam ser cobertos antes de F-A:

- **C1:** Prisma/ORM em pool de conexões não preserva `SET LOCAL app.tenant_id` entre requests — vazamento determinístico.
- **C2:** Celery workers rodam fora do request HTTP — `tenant_id` não é restaurado.
- **C3:** Role do app não pode ser `BYPASSRLS` nem superuser — Docker Compose mal configurado anula RLS.

---

## Decisão (rascunho — a fechar)

**Schema-shared + middleware tenant_id thread-local + RLS PostgreSQL + 2 roles distintas:**

1. **Role `app_user`** (acesso normal): `NOBYPASSRLS`, `NOSUPERUSER`. Usada pelo Django.
2. **Role `app_migrator`** (migrations only): pode rodar DDL, ainda NOBYPASSRLS.
3. **Middleware Django** seta `tenant_id` thread-local no início do request.
4. **Connection patcher Django ORM** abre transação e executa `SET LOCAL app.tenant_id = $1` antes da 1ª query.
5. **Wrapper `run_in_tenant(tenant_id, fn)`** obrigatório pra Celery tasks; teste prova que job sem tenant_id **falha**, não vaza.
6. **Lint custom** proíbe `connection.cursor().execute()` (raw queries) fora do `with_tenant()` wrapper.
7. **INV-TENANT-004 nova:** role `app_user` criada com NOBYPASSRLS; hook valida.
8. **Migration linter:** nova tabela com PK exige coluna `tenant_id NOT NULL` + FK pra `tenants`.
9. **Export por tenant** (LGPD art. 18 portabilidade): pipeline `export_tenant(uuid)` via `COPY ... WHERE tenant_id=$1` por tabela.

---

## Itens a fazer
- [ ] Spike 2 dias validando empiricamente C1 (Prisma/Django ORM + `SET LOCAL` em pool concorrente)
- [ ] Spike 1 dia validando prepared statements + RLS (Auditor 2 M1)
- [ ] Cross-tenant canary tenant sintético rodando query e alertando (Parecer 8)
- [ ] INV-TENANT-004 escrita em REGRAS-INEGOCIAVEIS.md + hook validador
- [ ] Decisão schema-shared vs schema-per-tenant final (gatilho de reversão: TAM > 1.000 tenants)

---

## Aprovação
- [ ] Roldão — pendente
- [ ] Auditor 2 (revisitar achados C1/C2/C3 + 5 altos) — pendente
