"""UNIQUE INDEX parcial + CHECK constraints em cliente_bloqueios (US-CLI-004).

TL1 do tech-lead: 1 bloqueio ativo por cliente — UNIQUE parcial WHERE desbloqueado IS NULL.
TL4 do tech-lead: causation_type vale enum.
R2 advogado: motivo_categoria vale enum.
"""

# rls-policy: external -- esta migration adiciona INDEX + CHECK, sem CREATE POLICY novo
# tests-coverage: tests/test_clientes_us_cli_004_bloquear.py

from __future__ import annotations

from django.db import migrations


CREATE_SQL = """
-- TL1: 1 bloqueio ativo por cliente
CREATE UNIQUE INDEX uq_cliente_bloqueio_ativo
    ON cliente_bloqueios (cliente_id)
    WHERE desbloqueado_em IS NULL;

-- TL4 + R2: enum constraints
ALTER TABLE cliente_bloqueios
    ADD CONSTRAINT chk_cliente_bloqueio_motivo_enum
    CHECK (motivo_categoria IN (
        'manual_inadimplencia',
        'manual_quebra_confianca',
        'manual_solicitacao_juridico',
        'manual_outro',
        'automatico_inadimplencia_90d'
    ));

ALTER TABLE cliente_bloqueios
    ADD CONSTRAINT chk_cliente_bloqueio_causation_enum
    CHECK (
        causation_type = ''
        OR causation_type IN (
            'titulo_vencido',
            'importacao_batch',
            'politica_inadimplencia',
            'manual_decisao_admin'
        )
    );

-- RLS pra tabela nova
ALTER TABLE cliente_bloqueios ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente_bloqueios FORCE ROW LEVEL SECURITY;

CREATE POLICY cli_bloq_tenant_isolation_select ON cliente_bloqueios
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY cli_bloq_tenant_isolation_update ON cliente_bloqueios
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY cli_bloq_tenant_isolation_delete ON cliente_bloqueios
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY cli_bloq_tenant_isolation_insert ON cliente_bloqueios
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

DROP_SQL = """
DROP POLICY IF EXISTS cli_bloq_tenant_isolation_insert ON cliente_bloqueios;
DROP POLICY IF EXISTS cli_bloq_tenant_isolation_delete ON cliente_bloqueios;
DROP POLICY IF EXISTS cli_bloq_tenant_isolation_update ON cliente_bloqueios;
DROP POLICY IF EXISTS cli_bloq_tenant_isolation_select ON cliente_bloqueios;
ALTER TABLE cliente_bloqueios DISABLE ROW LEVEL SECURITY;
ALTER TABLE cliente_bloqueios DROP CONSTRAINT IF EXISTS chk_cliente_bloqueio_causation_enum;
ALTER TABLE cliente_bloqueios DROP CONSTRAINT IF EXISTS chk_cliente_bloqueio_motivo_enum;
DROP INDEX IF EXISTS uq_cliente_bloqueio_ativo;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0008_clientebloqueio"),
    ]
    operations = [
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL),
    ]
