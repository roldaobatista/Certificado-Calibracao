# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** Foundation F-A (em curso)
**Semana da F-A:** 1 (de 4–6 esperadas)
**Modo:** AUTÔNOMO (autorizado por Roldão em 2026-05-17)
**Último Marco concluído:** **Marco 4 — Audit trail com hash chain** (canonicalização JSON determinística + sha256 + advisory lock + trigger PG anti-mutation + export stub).
**Próximo Marco (em curso):** Marco 5 — 2 hooks F-A faltantes (`migration-rls-check.sh` + `audit-immutability-check.sh`).

**Quadro de tarefas F-A (12 itens):**
- ✅ #11, #9, #10, #7 — gate administrativo
- ✅ #2 **Marco 1** — Esqueleto Django + Docker
- ✅ #1 **Marco 2** — 4 tabelas-núcleo
- ✅ #6 **Marco 3** — Multi-tenancy (middleware + roles + RLS)
- ✅ #12 **Marco 4** — Audit trail com hash chain
- 🔄 #3 **Marco 5** — Hooks migration-rls-check + audit-immutability-check
- ⏳ #8 **Marco 6** — Suite de testes + fuzzing cross-tenant
- ⏳ #5 **Marco 7** — `docs/arquitetura/django-convencoes.md`
- ⏳ #4 **Marco 8** — Drill final dos 7 critérios de saída F-A

**Arquivos do Marco 4 (entregues):**
- `src/infrastructure/audit/canonicalizar.py` — JSON canônico (sort_keys, sem espaço, ISO-8601 UTC obrigatório, Decimal preserva precisão, UUID stringifica, fail loud em datetime naive)
- `src/infrastructure/audit/hash_chain.py` — `calcular_hash(hash_anterior, payload_canon) = sha256(anterior || payload).hexdigest()`
- `src/infrastructure/audit/services.py` — `registrar_auditoria(...)` (advisory lock global serializa inserts) + `verificar_integridade_cadeia()` (drill Marco 8)
- `src/infrastructure/audit/migrations/0002_trigger_anti_mutation.py` — RunSQL cria função `auditoria_bloqueia_mutation()` + 2 triggers (BEFORE UPDATE + BEFORE DELETE) que RAISE EXCEPTION
- `src/infrastructure/audit/tasks.py` — stub `exportar_janela_horaria()` escreve JSONL em /tmp (destino B2 só com deploy autorizado)
- `tests/test_audit_canonicalizar.py` — 13 testes (ordem alfabética, sem espaço, tipos custom datetime/date/Decimal/UUID, acentos UTF-8, hash estável, hash muda com payload, hash muda com anterior)

**Decisões técnicas Marco 4:**
- Hash chain GLOBAL (não por tenant) — uma cadeia única amarra integridade da tabela inteira. Advisory lock por transação evita race condition de 2 inserts pegando mesmo `hash_anterior`.
- Datetime naive em payload é VALUEERROR — força chamador passar timezone. Sem isso, hash de máquina em UTC ≠ máquina em SP.
- Decimal → str() não float() (perda de precisão em valor financeiro).
- Defesa em 3 camadas: Python (`.save()`/`.delete()` raise) + Trigger PG (BEFORE UPDATE/DELETE) + Marco 5 hook pre-commit.

**Bloqueio:** nenhum.
**Risco aberto Marco 5:** hook `audit-immutability-check.sh` precisa detectar tentativas de mexer no trigger via migration nova OU via SQL bruto em management command. Lista de padrões a bloquear: `DROP TRIGGER auditoria_anti_*`, `DROP FUNCTION auditoria_bloqueia_mutation`, `ALTER TABLE auditoria DISABLE ROW LEVEL SECURITY`, etc.
