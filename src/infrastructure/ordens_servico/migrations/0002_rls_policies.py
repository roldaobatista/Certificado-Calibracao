"""T-OS-002 - RLS policies pattern v2 (ADR-0002 §6).

Cobertura:
- INV-TENANT-001/002/003: SELECT/UPDATE/DELETE/INSERT scoped por tenant
  via `app.tenant_ids` (multi-tenant role) + `app.active_tenant_id`
  (INSERT — tenant unico na sessao).
- INV-OS-ATIV-002 (cross-tenant proibido via OS pai): garantido pelo
  pattern v2 — UPDATE/DELETE em AtividadeDaOS so afeta linhas do tenant
  da sessao; INSERT exige `tenant_id = app.active_tenant_id` que vai
  ser populado pelo handler com o tenant da OS pai.

NAO cobre nesta migration (ficam em T-OS-003+):
- Trigger anti cross-tenant entre OS<->AtividadeDaOS (T-OS-003)
- Trigger estado computado INV-OS-ATIV-001 (T-OS-004 stub)
- Trigger executor designado INV-OS-ATIV-005 (T-OS-005)
- Unique partial index INV-OS-CONC-001 (T-OS-006)

# tests-coverage: tests/regressao/test_inv_os_ativ_002_cross_tenant.py (T-OS-109)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- ordens_servico - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE ordens_servico ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordens_servico FORCE ROW LEVEL SECURITY;

CREATE POLICY ordens_servico_tenant_isolation_select ON ordens_servico
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY ordens_servico_tenant_isolation_update ON ordens_servico
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY ordens_servico_tenant_isolation_delete ON ordens_servico
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY ordens_servico_tenant_isolation_insert ON ordens_servico
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- atividade_da_os - RLS pattern v2 (ADR-0002 §6 + INV-OS-ATIV-002)
-- =============================================================
ALTER TABLE atividade_da_os ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividade_da_os FORCE ROW LEVEL SECURITY;

CREATE POLICY atividade_da_os_tenant_isolation_select ON atividade_da_os
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY atividade_da_os_tenant_isolation_update ON atividade_da_os
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY atividade_da_os_tenant_isolation_delete ON atividade_da_os
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY atividade_da_os_tenant_isolation_insert ON atividade_da_os
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

REVERSE = """
DROP POLICY IF EXISTS atividade_da_os_tenant_isolation_insert ON atividade_da_os;
DROP POLICY IF EXISTS atividade_da_os_tenant_isolation_delete ON atividade_da_os;
DROP POLICY IF EXISTS atividade_da_os_tenant_isolation_update ON atividade_da_os;
DROP POLICY IF EXISTS atividade_da_os_tenant_isolation_select ON atividade_da_os;
ALTER TABLE atividade_da_os DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ordens_servico_tenant_isolation_insert ON ordens_servico;
DROP POLICY IF EXISTS ordens_servico_tenant_isolation_delete ON ordens_servico;
DROP POLICY IF EXISTS ordens_servico_tenant_isolation_update ON ordens_servico;
DROP POLICY IF EXISTS ordens_servico_tenant_isolation_select ON ordens_servico;
ALTER TABLE ordens_servico DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ordens_servico", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
