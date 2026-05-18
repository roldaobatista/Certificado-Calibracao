"""Refinamento das policies RLS — Marco 8 (drill F-A descobriu 2 gaps):

1. fail-loud: current_setting('app.tenant_ids') retornando '' (string vazia) faz
   policy não bloquear nada (string_to_array('', ',') = {""} que não casa UUIDs,
   mas tambem nao levanta erro). Substitui chamadas por require_tenant_ctx()
   que RAISE EXCEPTION se vazio. ADR-0002 §6 exige fail-loud.

2. ff_block_mutation muito restritivo: bloqueava INSERT legitimo de flag global
   (tenant_id NULL) em run_as_system(). Substituido por policies cirurgicas:
   - INSERT permitido se (tenant_id IS NULL E tenant_ids vazio) OU
                       (tenant_id = active_tenant_id)
   - UPDATE/DELETE continuam bloqueados (USING false) — flag flag flag
     muda via management command, nunca em runtime.
"""

# tests-coverage: tests/test_isolamento_cross_tenant.py

from __future__ import annotations

from django.db import migrations


REQUIRE_TENANT_CTX_FN = """
CREATE OR REPLACE FUNCTION require_tenant_ctx() RETURNS text
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v text;
BEGIN
    v := current_setting('app.tenant_ids');
    IF v IS NULL OR v = '' THEN
        RAISE EXCEPTION 'app.tenant_ids nao setado — query sem contexto tenant (INV-TENANT-001)'
            USING ERRCODE = '42501'; -- insufficient_privilege
    END IF;
    RETURN v;
END;
$$;
"""

DROP_REQUIRE_FN = """
DROP FUNCTION IF EXISTS require_tenant_ctx();
"""


REFINA_AUDITORIA = """
DROP POLICY IF EXISTS auditoria_tenant_isolation_select ON auditoria;
DROP POLICY IF EXISTS auditoria_tenant_isolation_update ON auditoria;
DROP POLICY IF EXISTS auditoria_tenant_isolation_delete ON auditoria;

CREATE POLICY auditoria_tenant_isolation_select ON auditoria
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));

CREATE POLICY auditoria_tenant_isolation_update ON auditoria
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));

CREATE POLICY auditoria_tenant_isolation_delete ON auditoria
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));
"""

REVERSE_AUDITORIA = """
DROP POLICY IF EXISTS auditoria_tenant_isolation_select ON auditoria;
DROP POLICY IF EXISTS auditoria_tenant_isolation_update ON auditoria;
DROP POLICY IF EXISTS auditoria_tenant_isolation_delete ON auditoria;

CREATE POLICY auditoria_tenant_isolation_select ON auditoria
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY auditoria_tenant_isolation_update ON auditoria
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY auditoria_tenant_isolation_delete ON auditoria
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));
"""


REFINA_FEATURE_FLAGS = """
DROP POLICY IF EXISTS ff_block_mutation ON feature_flags;

-- INSERT permitido em 2 cenarios:
-- (1) flag global criada via run_as_system (tenant_ids vazio E tenant_id NULL)
-- (2) flag tenant-specific via run_in_tenant_context (tenant_id = active_tenant_id)
CREATE POLICY ff_insert_validated ON feature_flags
    FOR INSERT
    WITH CHECK (
        (current_setting('app.tenant_ids') = '' AND tenant_id IS NULL)
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );

-- UPDATE bloqueado (flag muda via management command, nunca runtime)
CREATE POLICY ff_block_update ON feature_flags FOR UPDATE USING (false);

-- DELETE bloqueado idem
CREATE POLICY ff_block_delete ON feature_flags FOR DELETE USING (false);
"""

REVERSE_FEATURE_FLAGS = """
DROP POLICY IF EXISTS ff_block_delete ON feature_flags;
DROP POLICY IF EXISTS ff_block_update ON feature_flags;
DROP POLICY IF EXISTS ff_insert_validated ON feature_flags;

CREATE POLICY ff_block_mutation ON feature_flags
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("multitenant", "0001_rls_setup"),
    ]

    operations = [
        migrations.RunSQL(sql=REQUIRE_TENANT_CTX_FN, reverse_sql=DROP_REQUIRE_FN),
        migrations.RunSQL(sql=REFINA_AUDITORIA, reverse_sql=REVERSE_AUDITORIA),
        migrations.RunSQL(sql=REFINA_FEATURE_FLAGS, reverse_sql=REVERSE_FEATURE_FLAGS),
    ]
