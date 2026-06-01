"""T-CER-022 — RLS pattern v2 (ADR-0002 §6) nas 2 tabelas novas da reconciliação.

A tabela `certificados` JÁ tem RLS (migration 0001). Aqui só `ponto_reconciliado` e
`analise_reconciliacao_cert` (INV-TENANT-001/002/003 — idêntico a M4/M6/M7).

# tests-coverage: tests/regressao/test_inv_cer_p2_schema_triggers.py (RLS) + management/commands/validar_certificados.py (GATE-CER-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

TABELAS = ("ponto_reconciliado", "analise_reconciliacao_cert")


def _rls_forward(tabela: str) -> str:
    p = tabela
    return f"""
-- =============================================================
-- {tabela} - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;

CREATE POLICY {p}_tenant_isolation_select ON {tabela}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {p}_tenant_isolation_update ON {tabela}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {p}_tenant_isolation_delete ON {tabela}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {p}_tenant_isolation_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""


def _rls_reverse(tabela: str) -> str:
    p = tabela
    return f"""
DROP POLICY IF EXISTS {p}_tenant_isolation_insert ON {tabela};
DROP POLICY IF EXISTS {p}_tenant_isolation_delete ON {tabela};
DROP POLICY IF EXISTS {p}_tenant_isolation_update ON {tabela};
DROP POLICY IF EXISTS {p}_tenant_isolation_select ON {tabela};
ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;
"""


FORWARD = "\n".join(_rls_forward(t) for t in TABELAS)
REVERSE = "\n".join(_rls_reverse(t) for t in reversed(TABELAS))


class Migration(migrations.Migration):
    dependencies = [
        ("certificados", "0002_emissao_metrologica"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
