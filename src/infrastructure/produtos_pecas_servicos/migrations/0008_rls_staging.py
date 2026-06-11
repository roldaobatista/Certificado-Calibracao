"""T-PPS-041 — RLS policies pattern v2 (ADR-0002 §6) nas 2 tabelas de staging.

Mesmo molde da 0002_rls_policies (INV-TENANT-001/002/003): SELECT/UPDATE/DELETE
scoped por `app.tenant_ids`; INSERT por `app.active_tenant_id`; ENABLE + FORCE.
Staging é mutável (sem trigger WORM) — o isolamento de tenant é integral.

# tests-coverage: tests/test_pps_importacao_fatia3.py (RLS UNHAPPY staging) +
# management/commands/validar_produtos_pecas_servicos.py
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "importacao_catalogo",
    "importacao_catalogo_linha",
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


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0007_importacao_staging"),
    ]

    operations = [
        migrations.RunSQL(sql=_rls_forward(t), reverse_sql=_rls_reverse(t)) for t in TABELAS
    ]
