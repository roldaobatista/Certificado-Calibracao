# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.
>
> Hierarquia: CURRENT (agora) > SESSION (histórico curto) > auto-memory (preferências).

**Fase:** Foundation F-A (em curso)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17 — "pode fazer fa completo em modo autônomo")
**Último Marco concluído:** **Marco 1 — Esqueleto técnico** (Django 5.0 + DRF + PG16 + Docker Compose + estrutura de pastas conforme ADR-0007).
**Próximo Marco (em curso):** Marco 2 — 4 tabelas-núcleo (Tenant, Usuario, Auditoria, FeatureFlag) + migrations + admin.

**Quadro de tarefas F-A (12 itens):**
- ✅ #11 ADR-0002 → aceito
- ✅ #9 ADR-0007 → aceito
- ✅ #10 AGENTS.md → marca F-A iniciada + §6 atualizado com comandos reais
- ✅ #7 .agent/CURRENT.md (este arquivo)
- ✅ #2 **Marco 1** — Esqueleto Django + Docker (entregue 2026-05-17)
- 🔄 #1 **Marco 2** — 4 tabelas-núcleo
- ⏳ #6 **Marco 3** — Multi-tenancy (middleware + roles + RLS)
- ⏳ #12 **Marco 4** — Audit trail com hash chain
- ⏳ #3 **Marco 5** — Hooks migration-rls-check + audit-immutability-check
- ⏳ #8 **Marco 6** — Suite de testes + fuzzing cross-tenant
- ⏳ #5 **Marco 7** — `docs/arquitetura/django-convencoes.md`
- ⏳ #4 **Marco 8** — Drill final dos 7 critérios de saída F-A

**Arquivos do Marco 1 (entregues):**
- `pyproject.toml`, `manage.py`, `docker-compose.yml`, `Dockerfile`
- `docker/postgres/init/01-roles.sh`, `02-extensions.sh`
- `config/{__init__,urls,wsgi,asgi}.py` + `config/settings/{base,dev,prod}.py`
- `src/{domain,infrastructure,application}/__init__.py` + `domain/shared/{events,value_objects,invariantes}.py`
- `tests/{__init__,conftest,test_smoke_esqueleto}.py`
- `docs/operacao/setup-local.md` (tutorial mastigado pro Roldão)
- `.devcontainer/devcontainer.json` (pacote `afere.*` → `config.*` por causa de memória `project_product_name`)

**US em foco:** ainda nenhuma — F-A é infraestrutura, sem US de produto. Stories começam Wave A.
**AC ativos:** os 7 critérios de saída da F-A (ver `docs/faseamento-foundation-waves.md` §2)
**Branch:** main (commits direto na main por política do projeto + autonomia do agente)
**Bloqueio:** nenhum
**Risco aberto Marco 2:** definir hash da Auditoria (sha256 do payload JSON canonicalizado) sem ambiguidade — chaves ordenadas, sem espaço, ISO-8601 UTC. Forçar via teste no Marco 2 (não esperar Marco 6).
