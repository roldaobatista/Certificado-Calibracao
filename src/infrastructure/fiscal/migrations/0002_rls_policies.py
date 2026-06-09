"""T-FIS-020 — RLS policies pattern v2 (ADR-0002 §6) na tabela fiscal.

Cobertura (INV-TENANT-001/002/003 — idêntico a M3..M9):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids` (multi-tenant role).
- INSERT scoped por `app.active_tenant_id` (tenant único na sessão).
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

NÃO cobre nesta migration (fica em 0003_triggers_worm):
- INV-FIS-004 (campos probatórios imutáveis + block-delete — WORM Padrão B).

# tests-coverage: tests/test_fiscal_schema_fatia1b.py (RLS) + management/commands/validar_fiscal_nfse.py
"""

from __future__ import annotations

from django.db import migrations

TABELA = "nota_fiscal_servico"


FORWARD = f"""
-- =============================================================
-- {TABELA} - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE {TABELA} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {TABELA} FORCE ROW LEVEL SECURITY;

CREATE POLICY {TABELA}_tenant_isolation_select ON {TABELA}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {TABELA}_tenant_isolation_update ON {TABELA}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {TABELA}_tenant_isolation_delete ON {TABELA}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {TABELA}_tenant_isolation_insert ON {TABELA}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""


REVERSE = f"""
DROP POLICY IF EXISTS {TABELA}_tenant_isolation_insert ON {TABELA};
DROP POLICY IF EXISTS {TABELA}_tenant_isolation_delete ON {TABELA};
DROP POLICY IF EXISTS {TABELA}_tenant_isolation_update ON {TABELA};
DROP POLICY IF EXISTS {TABELA}_tenant_isolation_select ON {TABELA};
ALTER TABLE {TABELA} DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
