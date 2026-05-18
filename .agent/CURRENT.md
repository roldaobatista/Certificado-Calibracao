# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** Foundation F-A (em curso)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17 — "pode fazer fa completo em modo autônomo")
**Último Marco concluído:** **Marco 3 — Trava de isolamento entre clientes** (ContextVars + connection patcher + TenantMiddleware + Router 2-alias + Migration RLS).
**Próximo Marco (em curso):** Marco 4 — Trilha de auditoria com hash em cadeia (helper de canonicalização JSON + cálculo sha256 + trigger PG anti-UPDATE/DELETE + export stub).

**Quadro de tarefas F-A (12 itens):**
- ✅ #11 ADR-0002 → aceito
- ✅ #9 ADR-0007 → aceito
- ✅ #10 AGENTS.md → marca F-A iniciada
- ✅ #7 .agent/CURRENT.md
- ✅ #2 **Marco 1** — Esqueleto Django + Docker
- ✅ #1 **Marco 2** — 4 tabelas-núcleo
- ✅ #6 **Marco 3** — Multi-tenancy (middleware + roles + RLS)
- 🔄 #12 **Marco 4** — Audit trail com hash chain
- ⏳ #3 **Marco 5** — Hooks migration-rls-check + audit-immutability-check
- ⏳ #8 **Marco 6** — Suite de testes + fuzzing cross-tenant
- ⏳ #5 **Marco 7** — `docs/arquitetura/django-convencoes.md`
- ⏳ #4 **Marco 8** — Drill final dos 7 critérios de saída F-A

**Arquivos do Marco 3 (entregues):**
- `src/infrastructure/multitenant/__init__.py`, `apps.py` (registra signal connection_created)
- `src/infrastructure/multitenant/context.py` — 3 ContextVars (tenant_ids, active_tenant, usuario_id)
- `src/infrastructure/multitenant/connection.py` — connection patcher (reset no checkout do pool) + `setar_contexto_pg_na_conexao()` + `run_in_tenant_context()` + `run_as_system()`
- `src/infrastructure/multitenant/middleware.py` — TenantMiddleware (extrai user, resolve tenant_ids via UsuarioPerfilTenant, valida header `X-Afere-Active-Tenant`, seta GUCs PG)
- `src/infrastructure/multitenant/router.py` — TenantMultiRoleRouter (migrations → alias `migrator`)
- `src/infrastructure/multitenant/migrations/0001_rls_setup.py` — RLS v2 padrão pra `auditoria`; policy especial bootstrap pra `usuario_perfil_tenant` (usa `app.usuario_id`); policy híbrida pra `feature_flags` (NULL = global)
- `config/settings/base.py` — DATABASES com 2 alias (default + migrator); DATABASE_ROUTERS; TenantMiddleware na MIDDLEWARE list após Auth
- `docker-compose.yml` — migrate agora usa `--database=migrator`
- `tests/test_multitenant_{context,router,middleware_basico}.py` — 11 testes puros (sem banco)

**Decisões técnicas Marco 3:**
- ContextVar (PEP 567) > thread-local (funciona em ASGI também)
- `set_config(name, value, true)` = `SET LOCAL` (vive até COMMIT). Sem `ON ERROR_STOP` fallback — ADR-0002 §6 sem fallback permissivo.
- `usuario_perfil_tenant` tem policy bootstrap (`usuario_id = current_setting('app.usuario_id')`) — middleware lê ANTES de saber tenant_ids
- `feature_flags` aceita NULL = global; policy híbrida (`tenant_id IS NULL OR tenant_id IN lista`)
- DB Router: migrations só rodam no alias `migrator` (`allow_migrate(db) == "migrator"`). Comando: `manage.py migrate --database=migrator`.

**Bloqueio:** nenhum.
**Risco aberto Marco 4:** ordem de canonicalização JSON precisa ser determinística — sorted keys, separators=(",",":"), ensure_ascii=False, datetime ISO-8601 UTC com Z. Forçar via teste, não por convenção.
