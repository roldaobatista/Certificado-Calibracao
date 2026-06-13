"""T-COL-022 — RLS policies pattern v2 (ADR-0002 §6) nas 4 tabelas-tenant do módulo.

Cobertura (INV-TENANT-001/002/003):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids`.
- INSERT scoped por `app.active_tenant_id`.
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

ISENÇÃO DOCUMENTADA — catalogo_habilidade:
  Tabela global (sem tenant_id) — sem RLS por design (TL-COL-10 / D-COL-5).
  Acesso controlado por GRANT: app_user tem SELECT apenas (0004_grants_app_user).
  INSERT exclusivo via migration de seed (0006_seed_catalogo_habilidade).
  Não entra nesta migration.

# tests-coverage: tests/test_colaboradores_schema_fatia1b.py
# (RLS UNHAPPY cross-tenant nas 4 tabelas + drill validar_colaboradores.py)
"""

from __future__ import annotations

from django.db import migrations

# Apenas as tabelas com tenant_id — catalogo_habilidade é global (sem RLS).
TABELAS = (
    "colaborador",
    "colaborador_papel",
    "colaborador_habilidade",
    "colaborador_documento",
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
        ("colaboradores", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
