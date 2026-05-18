"""FA-C1 — policies RLS da auditoria: cadeia por-tenant + cadeia sistema.

Auditoria F-A rodada 1 (design FA-C1-design-hash-chain.md, aprovado pelo
tech-lead com correcoes). Schema (coluna `sequencia` + sequence + indice)
fica em audit/0009; aqui só as policies.

- SELECT: `app.modo_sistema='1'` (setado SO por run_as_system) → vê só a
  cadeia sistema (tenant_id IS NULL); senao isolamento por tenant com
  fail-loud (require_tenant_ctx() RAISE se contexto vazio). NAO usar
  `CASE WHEN app.tenant_ids=''` — regrediria o fail-loud da migration 0002.
- INSERT: cadeia sistema só sob modo_sistema; senao amarrado ao
  active_tenant_id SEM `::uuid` (que estoura com vazio). Espelha
  feature_flags.ff_insert_validated (0002).
- UPDATE/DELETE → USING(false): o trigger auditoria_anti_* ja e a barreira
  real; require_tenant_ctx() so mascarava "imutavel" com "tenant nao setado".

# rls-policy: auditoria SELECT/INSERT/UPDATE/DELETE recriadas (FA-C1)
# tests-coverage: tests/test_audit_cadeia_por_tenant.py
"""

from __future__ import annotations

from django.db import migrations


FORWARD = """
DROP POLICY IF EXISTS auditoria_tenant_isolation_select ON auditoria;
CREATE POLICY auditoria_chain_select ON auditoria
    FOR SELECT
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN tenant_id IS NULL
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    );

DROP POLICY IF EXISTS auditoria_tenant_isolation_insert ON auditoria;
CREATE POLICY auditoria_chain_insert ON auditoria
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1' AND tenant_id IS NULL)
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );

DROP POLICY IF EXISTS auditoria_tenant_isolation_update ON auditoria;
CREATE POLICY auditoria_chain_no_update ON auditoria
    FOR UPDATE USING (false);

DROP POLICY IF EXISTS auditoria_tenant_isolation_delete ON auditoria;
CREATE POLICY auditoria_chain_no_delete ON auditoria
    FOR DELETE USING (false);
"""

REVERSE = """
DROP POLICY IF EXISTS auditoria_chain_no_delete ON auditoria;
DROP POLICY IF EXISTS auditoria_chain_no_update ON auditoria;
DROP POLICY IF EXISTS auditoria_chain_insert ON auditoria;
DROP POLICY IF EXISTS auditoria_chain_select ON auditoria;

CREATE POLICY auditoria_tenant_isolation_select ON auditoria
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));
CREATE POLICY auditoria_tenant_isolation_insert ON auditoria
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
CREATE POLICY auditoria_tenant_isolation_update ON auditoria
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));
CREATE POLICY auditoria_tenant_isolation_delete ON auditoria
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(require_tenant_ctx(), ',')));
"""


class Migration(migrations.Migration):

    dependencies = [
        ("multitenant", "0003_upt_permite_insert_system"),
        ("audit", "0009_auditoria_sequencia"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
