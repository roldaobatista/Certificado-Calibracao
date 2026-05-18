# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** Foundation F-A — **CODE-COMPLETE** (aguardando drill no ambiente Roldão)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17 — "pode fazer fa completo em modo autônomo")
**Marcos concluídos:** 8/8 (gate administrativo + 8 entregáveis técnicos).
**Próximo passo:** Roldão sobe Docker no PC, roda `validar_f_a`, confere 5/7 critérios automáveis verde; 2/7 critérios operacionais ficam abertos pelas 4–6 semanas seguintes.

**Quadro F-A (12 tarefas — todas concluídas):**
- ✅ #11 ADR-0002 aceito | ✅ #9 ADR-0007 aceito | ✅ #10 AGENTS.md atualizado | ✅ #7 CURRENT.md atualizado
- ✅ #2 **Marco 1** Esqueleto Django + Docker (commit 20e79c7)
- ✅ #1 **Marco 2** 4 tabelas-núcleo (commit 60263ac)
- ✅ #6 **Marco 3** Multi-tenancy operacional (commit 8b286cd)
- ✅ #12 **Marco 4** Audit trail com hash chain (commit 97ef55b)
- ✅ #3 **Marco 5** 2 hooks faltantes (commit d2f5edc)
- ✅ #8 **Marco 6** Suite de testes + fuzzing (commit b22afae)
- ✅ #5 **Marco 7** Convenções Django (commit f323379)
- ✅ #4 **Marco 8** Drill + management command (este commit)

**Estatísticas da F-A:**
- Commits: 9 (incluindo gate + 8 marcos)
- Arquivos novos: ~50 (config, src/{domain,infrastructure,application}, tests, docker, docs)
- Linhas adicionadas: ~3000 (estimativa pré-último commit)
- Hooks ativos: 13 (88→90 testes verdes após adicionar 2 hooks F-A + 2 novos casos)
- Testes: 6 arquivos puros (sem PG) + 3 arquivos E2E (`@pytest.mark.tenant_isolation`)

**Falta no ambiente Roldão (não-código):**
1. Subir Docker: `docker compose up` (instruções `docs/operacao/setup-local.md`)
2. Rodar drill: `docker compose exec app poetry run python manage.py validar_f_a`
3. Rodar fuzzing: `docker compose exec app poetry run pytest -m "tenant_isolation and slow"`
4. Drill manual restore PG < 30min (uma vez no período F-A)
5. Acompanhar métricas operacionais nas 4–6 semanas (intervenções, SEV-1, tokens, vetos auditor)

**Quando 7/7 critérios verde → autorizar Foundation F-B.**

**Bloqueio:** nenhum no código; só falta gate operacional (Roldão).
