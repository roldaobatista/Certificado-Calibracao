"""T-PPS-021 — RLS policies pattern v2 (ADR-0002 §6) nas 5 tabelas do módulo.

Cobertura (INV-TENANT-001/002/003 — idêntico a configuracoes_sistema/fiscal/M3..M9):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids`; INSERT por `app.active_tenant_id`.
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

NÃO cobre nesta migration (fica em 0003_triggers_worm): imutabilidade de
versão/linha (INV-PPS-VERSAO-IMUTAVEL / INV-PPS-LINHA-IMUTAVEL).

# tests-coverage: tests/test_pps_schema_fatia1b.py (RLS UNHAPPY 5 tabelas) +
# management/commands/validar_produtos_pecas_servicos.py
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "item_catalogo",
    "item_catalogo_versao",
    "kit_composicao",
    "tabela_preco",
    "linha_tabela_preco",
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


FORWARD = "".join(_rls_forward(t) for t in TABELAS)
REVERSE = "".join(_rls_reverse(t) for t in reversed(TABELAS))


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
