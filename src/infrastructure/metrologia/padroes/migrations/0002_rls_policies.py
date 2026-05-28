"""T-PAD-010..014 — RLS policies pattern v2 (ADR-0002 §6) nas 6 tabelas M5.

Cobertura (INV-TENANT-001/002/003 — identico a M3/M4):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids` (multi-tenant role).
- INSERT scoped por `app.active_tenant_id` (tenant unico na sessao).
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

NAO cobre nesta migration (ficam em 0003_triggers_worm):
- INV-PAD-006 (incertezas/validade/proximo_recal so via recal — GUC).
- INV-SOFT-002 (block hard DELETE em padrao_metrologico).
- WORM em recal_externo_padrao / verificacao_intermediaria /
  intercomparacao_pt / analise_carta_controle.

# tests-coverage: tests/regressao/test_inv_pad_rls.py (T-PAD-072 GATE-PAD-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

# 6 tabelas M5 (db_table das classes em models.py). Lista canonica; sem wildcard.
TABELAS_M5 = (
    "padrao_metrologico",
    "recal_externo_padrao",
    "verificacao_intermediaria",
    "intercomparacao_pt",
    "analise_carta_controle",
    "vinculo_auxiliar",
)


def _rls_forward(tabela: str) -> str:
    p = tabela  # prefixo das policies = nome da tabela (unico por tabela)
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


FORWARD = "\n".join(_rls_forward(t) for t in TABELAS_M5)
REVERSE = "\n".join(_rls_reverse(t) for t in reversed(TABELAS_M5))


class Migration(migrations.Migration):
    dependencies = [
        ("padroes", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
