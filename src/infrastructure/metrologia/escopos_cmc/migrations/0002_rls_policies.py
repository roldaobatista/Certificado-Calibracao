"""T-ECMC-012 — RLS policies pattern v2 (ADR-0002 §6) nas 2 tabelas M6.

Cobertura (INV-TENANT-001/002/003 — idêntico a M3/M4/M5):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids` (multi-tenant role).
- INSERT scoped por `app.active_tenant_id` (tenant único na sessão).
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

NÃO cobre nesta migration (fica em 0003_triggers_worm):
- INV-ECMC-003 (campo metrológico de CONFIRMADO imutável — WORM Padrão B).
- INV-SOFT-002 (block hard DELETE em escopo_cmc).

# tests-coverage: tests/regressao/test_inv_ecmc_p2_schema_triggers.py (RLS) + management/commands/validar_escopos_cmc.py (GATE-ECMC-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

TABELAS_M6 = (
    "escopo_cmc",
    "escopo_extraido",
)


def _rls_forward(tabela: str) -> str:
    p = tabela  # prefixo das policies = nome da tabela (único por tabela)
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


FORWARD = "\n".join(_rls_forward(t) for t in TABELAS_M6)
REVERSE = "\n".join(_rls_reverse(t) for t in reversed(TABELAS_M6))


class Migration(migrations.Migration):
    dependencies = [
        ("escopos_cmc", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
