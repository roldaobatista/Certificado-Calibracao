"""T-ORC-022 — RLS policies pattern v2 (ADR-0002 §6) nas 7 tabelas do modulo.

Cobertura (INV-TENANT-001/002/003 — identico a precificacao/PPS/clientes):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids`; INSERT por `app.active_tenant_id`.
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

NAO cobre nesta migration (fica em 0003_triggers_worm): imutabilidade WORM de
aprovacao/analise/versao (INV-ORC-APROVACAO-WORM / ANALISE-WORM).

# tests-coverage: tests/test_orcamentos_schema.py
# (RLS UNHAPPY cross-tenant nas 7 tabelas — drill PG-real)
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "orcamento",
    "versao_orcamento",
    "item_orcamento",
    "orcamento_link_publico",
    "orcamento_aprovacao",
    "analise_critica_orcamento",
    "template_orcamento",
)


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


SQL_FORWARD = "\n".join(_rls_forward(t) for t in TABELAS)
SQL_REVERSE = "\n".join(_rls_reverse(t) for t in TABELAS)


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
