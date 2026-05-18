"""Fonte ÚNICA do SQL de policies RLS de isolamento por tenant (FA-A2).

Por que existe: `clientes/0002` nasceu com `current_setting('app.tenant_ids')`
CRU, divergente do fail-loud que `multitenant/0002` instituiu para
`auditoria`/`feature_flags`. Em contexto vazio o cru devolve `''` →
`string_to_array('',',')` não casa UUID → policy "vê 0 linhas" SILENCIOSA em
vez de RAISE (furo de robustez de isolamento — ADR-0002 §6 exige fail-loud).

Toda migration futura que crie tabela com `tenant_id` deve gerar policies por
estas funções — nunca colar SQL cru de novo (dedup formal: FA-M3).

Contrato das 4 policies geradas (`<tabela>_tenant_isolation_*`):
- SELECT/UPDATE/DELETE: `require_tenant_ctx()` — RAISE 42501 se contexto vazio
  (criada em `multitenant/0002_fail_loud_e_flag_global`).
- INSERT: `WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid)`
  — fail-loud via 22P02 (`''::uuid` aborta). Idêntico ao precedente
  auditoria/feature_flags; NÃO usar `require_active_tenant()` aqui (escopo
  FA-A2 é só `require_tenant_ctx()`; higiene de mensagem fica em FA-M3).
"""

from __future__ import annotations

import re

# Nome de tabela é input de migration (dev/agente), não de usuário — mas
# f-string crua em DDL é má higiene e o template pode ser estendido a tabelas
# vindas de config. Validação mata a classe inteira de injeção em DDL (R3).
_NOME_TABELA_VALIDO = re.compile(r"[a-z_][a-z0-9_]*")


def _validar_tabela(tabela: str) -> str:
    if not _NOME_TABELA_VALIDO.fullmatch(tabela):
        raise ValueError(
            f"Nome de tabela invalido para template RLS: {tabela!r}. "
            r"Esperado /[a-z_][a-z0-9_]*/ (anti-injecao DDL, FA-A2 R3)."
        )
    return tabela


def _select_update_delete(tabela: str) -> str:
    return f"""
CREATE POLICY {tabela}_tenant_isolation_select ON {tabela}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));

CREATE POLICY {tabela}_tenant_isolation_update ON {tabela}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));

CREATE POLICY {tabela}_tenant_isolation_delete ON {tabela}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));
"""


def _insert(tabela: str) -> str:
    return f"""
CREATE POLICY {tabela}_tenant_isolation_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""


def drop_policies_isolamento_tenant(tabela: str) -> str:
    """Só DROP das 4 policies (idempotente). Uso interno do forward/reverse."""
    t = _validar_tabela(tabela)
    return f"""
DROP POLICY IF EXISTS {t}_tenant_isolation_insert ON {t};
DROP POLICY IF EXISTS {t}_tenant_isolation_delete ON {t};
DROP POLICY IF EXISTS {t}_tenant_isolation_update ON {t};
DROP POLICY IF EXISTS {t}_tenant_isolation_select ON {t};
"""


def policies_isolamento_tenant(tabela: str) -> str:
    """SQL forward: DROP idempotente + 4 policies fail-loud.

    DROP-then-CREATE permite regenerar policies cruas pré-existentes sem erro
    de "policy already exists".
    """
    t = _validar_tabela(tabela)
    return drop_policies_isolamento_tenant(t) + _select_update_delete(t) + _insert(t)


def reverse_policies_isolamento_tenant(tabela: str) -> str:
    """SQL reverse: recria as policies AINDA fail-loud (NÃO volta ao cru).

    R2 (review tech-lead FA-A2): reverse cru reintroduziria a vuln FA-A2 num
    caminho que testes/hook (forward-only) não exercitam — rollback de
    emergência vazaria-para-zero sem alarme. Schema continua reversível
    (policies existem, RLS ativa); só não regride a robustez fail-loud.
    """
    return policies_isolamento_tenant(tabela)
