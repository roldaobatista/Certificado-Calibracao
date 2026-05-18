# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.
>
> Hierarquia: CURRENT (agora) > SESSION (histórico curto) > auto-memory (preferências).

**Fase:** Foundation F-A (em curso)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17 — "pode fazer fa completo em modo autônomo")
**Último Marco concluído:** **Marco 2 — 4 tabelas-núcleo** (Tenant, Usuario+UsuarioPerfilTenant, Auditoria, FeatureFlag) + admin + testes + AUTH_USER_MODEL custom.
**Próximo Marco (em curso):** Marco 3 — Trava de isolamento (TenantMiddleware + connection patcher + roles PG aplicadas via DATABASE_MIGRATOR_URL + policies RLS v2 com lista de tenants).

**Quadro de tarefas F-A (12 itens):**
- ✅ #11 ADR-0002 → aceito
- ✅ #9 ADR-0007 → aceito
- ✅ #10 AGENTS.md → marca F-A iniciada
- ✅ #7 .agent/CURRENT.md
- ✅ #2 **Marco 1** — Esqueleto Django + Docker
- ✅ #1 **Marco 2** — 4 tabelas-núcleo + admin
- 🔄 #6 **Marco 3** — Multi-tenancy (middleware + roles + RLS)
- ⏳ #12 **Marco 4** — Audit trail com hash chain
- ⏳ #3 **Marco 5** — Hooks migration-rls-check + audit-immutability-check
- ⏳ #8 **Marco 6** — Suite de testes + fuzzing cross-tenant
- ⏳ #5 **Marco 7** — `docs/arquitetura/django-convencoes.md`
- ⏳ #4 **Marco 8** — Drill final dos 7 critérios de saída F-A

**Arquivos do Marco 2 (entregues):**
- `src/infrastructure/tenant/{__init__,apps,models,admin}.py` + `migrations/__init__.py`
- `src/infrastructure/usuario/{__init__,apps,models,admin}.py` + `migrations/__init__.py` — `Usuario` custom (USERNAME_FIELD=email, Argon2) + `UsuarioPerfilTenant` (M:N com valido_de/ate)
- `src/infrastructure/audit/{__init__,apps,models,admin}.py` + `migrations/__init__.py` — `Auditoria` INSERT-only com hash_anterior/hash_atual (cálculo Marco 4); admin readonly; .save()/.delete() bloqueados em código
- `src/infrastructure/feature_flag/{__init__,apps,models,admin}.py` + `migrations/__init__.py`
- `config/settings/base.py` atualizado (INSTALLED_APPS + AUTH_USER_MODEL='usuario.Usuario')
- `docker-compose.yml` atualizado (roda `makemigrations` antes de `migrate` no boot dev)
- `tests/test_models_nucleo.py` — 11 testes (Tenant, Usuario, UsuarioPerfilTenant, Auditoria, FeatureFlag)
- `.claude/hooks/authz-check.sh` — fix de path Windows (normalização backslash→forward) + allowlist `*/models.py *.py /apps.py`

**US em foco:** ainda nenhuma — F-A é infraestrutura.
**AC ativos:** 7 critérios de saída F-A.
**Branch:** main.
**Bloqueio:** nenhum.
**Risco aberto Marco 3:** middleware tem que setar `app.tenant_ids` ANTES de qualquer query do request (incluindo middleware seguintes que possam consultar User). Ordem em MIDDLEWARE list crítica. Testar com fuzzing concorrente pool de conexões.
