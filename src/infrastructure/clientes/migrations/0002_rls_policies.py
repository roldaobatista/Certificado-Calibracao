"""RLS pra tabela clientes — pattern v2 (ADR-0002 §6).

INV-TENANT-001/002/003: isolamento cross-tenant em todas as tabelas com tenant_id.
Policy SELECT/UPDATE/DELETE usa lista de tenants; INSERT exige active_tenant.
"""

# tests-coverage: tests/test_clientes_isolamento.py tests/test_clientes_modelo.py

from __future__ import annotations

from django.db import migrations


RLS_POLICY = """
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes FORCE ROW LEVEL SECURITY;

CREATE POLICY clientes_tenant_isolation_select ON clientes
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY clientes_tenant_isolation_update ON clientes
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY clientes_tenant_isolation_delete ON clientes
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY clientes_tenant_isolation_insert ON clientes
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

RLS_POLICY_REVERSE = """
DROP POLICY IF EXISTS clientes_tenant_isolation_insert ON clientes;
DROP POLICY IF EXISTS clientes_tenant_isolation_delete ON clientes;
DROP POLICY IF EXISTS clientes_tenant_isolation_update ON clientes;
DROP POLICY IF EXISTS clientes_tenant_isolation_select ON clientes;
ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=RLS_POLICY,
            reverse_sql=RLS_POLICY_REVERSE,
        ),
    ]
