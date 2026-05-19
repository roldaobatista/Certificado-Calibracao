"""Fonte ÚNICA do SQL de policies RLS de isolamento por tenant (FA-A2).

Por que existe: `clientes/0002` nasceu com `current_setting('app.tenant_ids')`
CRU, divergente do fail-loud que `multitenant/0002` instituiu para
`auditoria`/`feature_flags`. Em contexto vazio o cru devolve `''` →
`string_to_array('',',')` não casa UUID → policy "vê 0 linhas" SILENCIOSA em
vez de RAISE (furo de robustez de isolamento — ADR-0002 §6 exige fail-loud).

Toda migration futura que crie tabela com `tenant_id` deve gerar policies por
estas funções — nunca colar SQL cru de novo (dedup formal: FA-M3).

EXCEÇÃO CONSCIENTE (FB-C3, review tech-lead Q3): `authz_decisions` admite
`tenant_id NULL` legítimo (decisão pré-tenant: login, "listar meus tenants").
O template genérico acima é fail-loud ESTRITO (`require_tenant_ctx()` RAISE
42501 + `WITH CHECK tenant_id = ...::uuid` aborta em `''::uuid`) e quebraria
todo login pré-tenant. Por isso authz_decisions usa o builder DEDICADO
`policies_authz_decisions()` abaixo — MESMA fonte única, molde próprio. NÃO
"consertar" authz_decisions pro template genérico (reintroduz FB-C1⇄FB-C3).

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


# --- Builder DEDICADO: authz_decisions (FB-C3 — exceção consciente) ----------
#
# Cadeia hash com 3 caminhos legítimos de leitura/escrita:
#  1. modo_sistema='1' (run_as_system): trilha COMPLETA — drill/CGCRE.
#     Sinal canônico FA-C1 (substitui o proxy frágil `usuario_id=''` que era
#     a regressão FB-C3 — worker tenant sem usuário via pré-tenant alheio).
#  2. Cadeia pré-tenant POR-USUÁRIO (tenant_id NULL): o usuário só lê/encadeia
#     as PRÓPRIAS decisões pré-tenant. Resolve FB-C1⇄FB-C3 (a decisão authz
#     pré-tenant TEM dono — o usuário; ≠ cadeia "sistema" do audit, sem dono).
#  3. Cadeia do tenant: tenant na lista de tenants do contexto.
#
# INSERT NÃO tem branch `modo_sistema` PROPOSITALMENTE (review tech-lead Q4):
# `can()` sempre tem usuario_id (é o sujeito da decisão); nenhum fluxo grava
# authz_decisions sob run_as_system. Adicionar permissivo morto = furo. Há
# teste que prova INSERT sob run_as_system → NEGADO (trava regressão).
#
# `current_setting(..., true)` (2º arg) em TODAS as GUCs — robusto se a GUC
# nunca foi setada na sessão (não levanta "unrecognized configuration").

_AUTHZ_DECISIONS_SELECT = """
CREATE POLICY authz_decisions_select ON authz_decisions
    FOR SELECT
    USING (
        current_setting('app.modo_sistema', true) = '1'
        OR (
            tenant_id IS NULL
            AND usuario_id = NULLIF(current_setting('app.usuario_id', true), '')::uuid
        )
        OR tenant_id::text = ANY(
            string_to_array(current_setting('app.tenant_ids', true), ',')
        )
    );
"""

_AUTHZ_DECISIONS_INSERT = """
CREATE POLICY authz_decisions_insert ON authz_decisions
    FOR INSERT
    WITH CHECK (
        (
            tenant_id IS NULL
            AND usuario_id = NULLIF(current_setting('app.usuario_id', true), '')::uuid
        )
        OR tenant_id = NULLIF(current_setting('app.active_tenant_id', true), '')::uuid
    );
"""

# UPDATE/DELETE: policy permissiva — quem fala é o TRIGGER PG anti-mutation
# (mensagem melhor, INV-AUTHZ-002). NÃO tocar o trigger (já existe em 0002).
_AUTHZ_DECISIONS_NO_MUT = """
CREATE POLICY authz_decisions_no_update ON authz_decisions
    FOR UPDATE USING (true) WITH CHECK (true);

CREATE POLICY authz_decisions_no_delete ON authz_decisions
    FOR DELETE USING (true);
"""

_AUTHZ_DECISIONS_DROP = """
DROP POLICY IF EXISTS authz_decisions_no_delete ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_no_update ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_insert ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_select ON authz_decisions;
"""


def policies_authz_decisions() -> str:
    """SQL forward das 4 policies de authz_decisions (DROP idempotente + CREATE).

    DROP-then-CREATE permite regenerar sobre as policies pré-FB-C3 sem erro
    de "policy already exists". Garante `ENABLE/FORCE ROW LEVEL SECURITY`.
    """
    return (
        "ALTER TABLE authz_decisions ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE authz_decisions FORCE ROW LEVEL SECURITY;\n"
        + _AUTHZ_DECISIONS_DROP
        + _AUTHZ_DECISIONS_SELECT
        + _AUTHZ_DECISIONS_INSERT
        + _AUTHZ_DECISIONS_NO_MUT
    )


def reverse_policies_authz_decisions() -> str:
    """Reverse: recria as MESMAS policies (não regride robustez — padrão FA-A2).

    Rollback de emergência não pode reintroduzir a regressão FB-C3 (proxy
    `usuario_id=''`) num caminho não exercitado por teste forward-only.
    """
    return policies_authz_decisions()
