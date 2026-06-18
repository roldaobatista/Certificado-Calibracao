"""T-CT-023 — RLS pattern v2 (ADR-0002 §6) em TODAS as 6 tabelas do caixa_tecnico.

4 policies por tabela:
  SELECT/UPDATE/DELETE → app.tenant_ids (multi-tenant)
  INSERT              → app.active_tenant_id (único tenant por sessão)

Molde idêntico a contas_receber/0002_rls_policies e agenda/0002_rls_policies.

# tests-coverage: tests/test_caixa_tecnico_schema_fatia1b.py
# (cobertura RLS happy + UNHAPPY cross-tenant: test_rls_isolamento_cross_tenant,
#  test_rls_enabled_forced_em_todas_as_tabelas, test_policies_minimas_em_todas_as_tabelas)
#  + management/commands/validar_caixa_tecnico.py
"""

from django.db import migrations

_TABELAS = [
    "caixa_tecnico",
    "adiantamento_caixa",
    "despesa_caixa",
    "prestacao_contas_caixa",
    "politica_caixa",
    "consentimento_gps_colaborador",
]


def _sql_rls(tabela: str) -> str:
    """Gera SQL RLS para uma tabela (4 policies — ADR-0002 §6 pattern v2)."""
    return f"""
-- RLS {tabela}
ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;

CREATE POLICY {tabela}_select ON {tabela}
    FOR SELECT
    USING (tenant_id = ANY(
        string_to_array(current_setting('app.tenant_ids', TRUE), ',')::uuid[]
    ));

CREATE POLICY {tabela}_update ON {tabela}
    FOR UPDATE
    USING (tenant_id = ANY(
        string_to_array(current_setting('app.tenant_ids', TRUE), ',')::uuid[]
    ));

CREATE POLICY {tabela}_delete ON {tabela}
    FOR DELETE
    USING (tenant_id = ANY(
        string_to_array(current_setting('app.tenant_ids', TRUE), ',')::uuid[]
    ));

CREATE POLICY {tabela}_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id', TRUE)::uuid);
"""


def _sql_rls_reverso(tabela: str) -> str:
    return f"""
DROP POLICY IF EXISTS {tabela}_select ON {tabela};
DROP POLICY IF EXISTS {tabela}_update ON {tabela};
DROP POLICY IF EXISTS {tabela}_delete ON {tabela};
DROP POLICY IF EXISTS {tabela}_insert ON {tabela};
ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("caixa_tecnico", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="\n".join(_sql_rls(t) for t in _TABELAS),
            reverse_sql="\n".join(_sql_rls_reverso(t) for t in _TABELAS),
        ),
    ]
