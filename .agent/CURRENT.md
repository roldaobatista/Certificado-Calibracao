# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** Foundation F-A (em curso)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17)
**Último Marco concluído:** **Marco 5 — 2 hooks F-A faltantes** (`migration-rls-check.sh` + `audit-immutability-check.sh`). Total agora 13 hooks ativos, 88/88 testes verdes.
**Próximo Marco (em curso):** Marco 6 — Suite de testes + fuzzing cross-tenant.

**Quadro F-A (12 itens):**
- ✅ #11, #9, #10, #7 — gate administrativo
- ✅ #2 **Marco 1** — Esqueleto Django + Docker
- ✅ #1 **Marco 2** — 4 tabelas-núcleo
- ✅ #6 **Marco 3** — Multi-tenancy (middleware + RLS)
- ✅ #12 **Marco 4** — Audit trail com hash chain
- ✅ #3 **Marco 5** — 2 hooks faltantes
- 🔄 #8 **Marco 6** — Suite de testes + fuzzing cross-tenant
- ⏳ #5 **Marco 7** — `docs/arquitetura/django-convencoes.md`
- ⏳ #4 **Marco 8** — Drill final dos 7 critérios de saída F-A

**Arquivos do Marco 5 (entregues):**
- `.claude/hooks/migration-rls-check.sh` — detecta `CreateModel + tenant_id` em migration; exige `CREATE POLICY`/`ENABLE ROW LEVEL SECURITY` na mesma; permite override por comentário `# rls-policy: external NNNN`.
- `.claude/hooks/audit-immutability-check.sh` — bloqueia 7 padrões de degradação da trilha; override exige justificativa ≥10 chars; auto-allow para migrations que TAMBÉM criam `CREATE TRIGGER auditoria_anti_*` ou `CREATE FUNCTION auditoria_bloqueia_mutation` (reverse_sql tem DROP mas é legítimo).
- `.claude/settings.json` — registra os 2 hooks no `PreToolUse Write|Edit`.
- `.claude/hooks/_test-runner.sh` — +17 casos novos (6 RLS + 11 audit-immutability). Resumo 71 → 88.
- `AGENTS.md` §3 (hooks atualizada) e §12 (subseção "Hooks 13 ativos").

**Decisões técnicas Marco 5:**
- `migration-rls-check` é fail-open por design (só bloqueia se DETECTA tenant_id E NÃO acha policy). Sem detecção de schema completo — confia em pattern grep.
- `audit-immutability-check` valida em `.py` e `.sql` (ambos podem ter raw SQL); ignora `*/tests/*` e `*.md`.
- Auto-allow da migration de criação: presença de `CREATE TRIGGER auditoria_anti_*` no MESMO conteúdo libera o `DROP TRIGGER` que vive no reverse_sql. Heurística robusta (não depende de nome de arquivo).

**Bloqueio:** nenhum.
**Risco aberto Marco 6:** fuzzing cross-tenant real exige PG vivo com RLS aplicada — testes não rodam no harness atual (sem Docker). Vou escrever os testes + marcar como `@pytest.mark.tenant_isolation` + documentar que Marco 8 drill executa quando Roldão subir o ambiente.
