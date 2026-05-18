# .agent/CURRENT.md

> ≤30 linhas. Atualizado a cada conclusão de tarefa F-A (manual por agora; hook session-start fica pra Wave A quando codegen estiver pronto).
>
> Hierarquia: CURRENT (agora) > SESSION (histórico curto) > auto-memory (preferências).

**Fase:** Foundation F-A (INICIADA em 2026-05-17 com autorização do Roldão)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Último entregável concluído:** ADR-0002 e ADR-0007 promovidas pra "aceito"; AGENTS.md atualizado refletindo início da F-A.
**Próximo entregável (em curso):** este arquivo `.agent/CURRENT.md` sendo atualizado pra refletir a fase nova.
**Entregável seguinte na fila:** esqueleto Django 5.0 + DRF + PostgreSQL 16 via Docker Compose local (task #2 do quadro).

**Quadro de tarefas F-A (12 itens):**
- ✅ #11 ADR-0002 → aceito
- ✅ #9 ADR-0007 → aceito
- 🔄 #10 AGENTS.md → marca F-A iniciada
- 🔄 #7 .agent/CURRENT.md → este arquivo
- ⏳ #2 Esqueleto Django + Docker
- ⏳ #1 4 tabelas-núcleo (Tenant, Usuario, Auditoria, FeatureFlag)
- ⏳ #6 Multi-tenancy (middleware + roles + RLS)
- ⏳ #12 Audit trail com hash chain
- ⏳ #3 Hooks migration-rls-check + audit-immutability-check
- ⏳ #8 Suite de testes + fuzzing cross-tenant
- ⏳ #5 docs/arquitetura/django-convencoes.md
- ⏳ #4 Drill de validação dos 7 critérios de saída F-A

**US em foco:** ainda nenhuma — F-A é infraestrutura, sem US de produto. Stories de produto começam na Wave A.
**AC ativos:** os 7 critérios de saída da F-A (ver `docs/faseamento-foundation-waves.md` §2)
**Branch:** main
**Bloqueio:** nenhum (todos os gates doc/governança fechados; Roldão autorizou)
**Risco aberto:** F-A é primeiro código real do projeto — agente IA pode introduzir vazamento cross-tenant. Mitigação: defesa em 4 camadas da ADR-0002 + 2 hooks adicionais (#3 do quadro) antes do código tocar o banco.

**Atualizar este arquivo a cada:** tarefa F-A concluída + novo bloqueio + decisão Roldão.
