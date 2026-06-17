"""T-AGE-023 — RLS policies pattern v2 (ADR-0002 §6) nas tabelas agenda.

Cobertura (INV-TENANT-001/002/003 — idêntico a contas_receber / ordens_servico):
- SELECT/UPDATE/DELETE scoped por ``app.tenant_ids`` (multi-tenant role).
- INSERT scoped por ``app.active_tenant_id`` (tenant único na sessão).
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

Tabelas cobertas: as 7 tabelas da Fatia 1b.

Nota: ``feriado`` tem tenant_id nullable (nacionais têm tenant=NULL). A policy de
SELECT inclui ``OR tenant_id IS NULL`` para que todos os tenants leiam os feriados
nacionais do seed (comportamento esperado — D-AGE-10). INSERT de feriado nacional
é feito só via migration (seed), nunca via app_user.

# tests-coverage: tests/test_agenda_schema_fatia1b.py
"""

from __future__ import annotations

from django.db import migrations

_TABELAS_COMUNS = [
    "evento_agenda",
    "recorrencia_agenda",
    "registro_no_show",
    "capacidade_tecnico",
    "evento_auditoria_agenda",
    "regime_jornada_colaborador",
]


def _rls_forward(tabela: str) -> str:
    return f"""
-- =============================================================
-- {tabela} - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;

CREATE POLICY {tabela}_tenant_isolation_select ON {tabela}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_update ON {tabela}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_delete ON {tabela}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""


def _rls_reverse(tabela: str) -> str:
    return f"""
DROP POLICY IF EXISTS {tabela}_tenant_isolation_insert ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_delete ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_update ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_select ON {tabela};
ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;
"""


# feriado tem RLS especial: SELECT inclui feriados nacionais (tenant IS NULL).
_FERIADO_FORWARD = """
-- =============================================================
-- feriado - RLS pattern v2 com suporte a feriados nacionais (tenant IS NULL)
-- =============================================================
ALTER TABLE feriado ENABLE ROW LEVEL SECURITY;
ALTER TABLE feriado FORCE ROW LEVEL SECURITY;

CREATE POLICY feriado_tenant_isolation_select ON feriado
    FOR SELECT
    USING (
        tenant_id IS NULL
        OR tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))
    );

CREATE POLICY feriado_tenant_isolation_update ON feriado
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY feriado_tenant_isolation_delete ON feriado
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY feriado_tenant_isolation_insert ON feriado
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

_FERIADO_REVERSE = """
DROP POLICY IF EXISTS feriado_tenant_isolation_insert ON feriado;
DROP POLICY IF EXISTS feriado_tenant_isolation_delete ON feriado;
DROP POLICY IF EXISTS feriado_tenant_isolation_update ON feriado;
DROP POLICY IF EXISTS feriado_tenant_isolation_select ON feriado;
ALTER TABLE feriado DISABLE ROW LEVEL SECURITY;
"""

FORWARD = "\n".join(_rls_forward(t) for t in _TABELAS_COMUNS) + _FERIADO_FORWARD
REVERSE = "\n".join(_rls_reverse(t) for t in _TABELAS_COMUNS) + _FERIADO_REVERSE


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
