# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** Foundation F-A — **DRILL 5/5 VERDE** (2026-05-18)
**Modo:** AUTÔNOMO (Roldão "pode continuar")
**Marcos:** 8/8 + drill executado no Docker do PC
**Próximo passo:** critérios 6+7 (drill restore PG manual + 4-6 semanas operação)

**Resultado do drill (2026-05-18):**
- ✅ Hooks 90/90 verdes
- ✅ Roles app_user/app_migrator NOBYPASSRLS + NOSUPERUSER
- ✅ Trigger auditoria_anti_* (update + delete) existe
- ✅ Hash chain íntegro (5 linhas verificadas, 0 quebras)
- ✅ p99 query operacional = 6.1ms (limite 200ms — folga 33x)
- ✅ Fuzzing 50 threads × 100 queries → ZERO vazamento
- ✅ Suite pytest: 58 passed, 1 skipped (justificado Wave A)

**Bugs descobertos PELO drill e corrigidos (justifica o drill):**
1. PEP 440 inválido em version do pyproject (`0.1.0-foundation-f-a` → `0.1.0`)
2. Syntax errado pra extras Poetry (`"psycopg[binary,pool]"` → inline table)
3. Dockerfile faltava deps dev (django-extensions)
4. Ordem de migrations circular (audit.0002 dep audit.0001) → renomeado 0003
5. **fail-soft em RLS:** `current_setting('app.tenant_ids')` vazio retornava `''` em vez de erro → migration 0002 adiciona função `require_tenant_ctx()` que RAISE EXCEPTION
6. **Policy `ff_block_mutation` muito restritiva:** bloqueava INSERT de flag global em system → migration 0002 substitui por policies cirúrgicas (INSERT permitido em system OR contexto tenant)
7. **Policy `upt_block_mutation` idem:** factory de teste / provisioning admin não conseguia INSERT → migration 0003 permite INSERT em system
8. Test DB `test_afere` precisa permissões manuais (`GRANT ALL ON SCHEMA public` + DEFAULT PRIVILEGES) porque app_user é NOCREATEDB

**Migrations novas durante drill:**
- `multitenant.0002_fail_loud_e_flag_global` (require_tenant_ctx + ff policies cirúrgicas)
- `multitenant.0003_upt_permite_insert_system`
- `audit.0003_trigger_anti_mutation` (renomeado de 0002)

**Pendências Roldão (não-código):**
- Drill manual restore PG < 30min com pgBackRest (uma vez no período)
- Acompanhar 4-6 semanas: ≤ 2 intervenções/sem, ≤ 3 SEV-1, ≤ R$1.500 LLM, auditor sem veto

**Quando 7/7 verde → F-A FECHA → autorizar F-B (autenticação + RBAC + MFA).**

**Bloqueio:** nenhum.
