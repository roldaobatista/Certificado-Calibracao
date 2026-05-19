"""RLS + trigger anti-mutation pra acessos_dados_cliente (US-CLI-002 — TL6).

INV-013: log de visualizacao imutavel. Trigger bloqueia UPDATE/DELETE.
RLS pattern v2 — usuario so ve acessos do tenant.

Index expressional em `auditoria` pra timeline performante (TL1).
"""

# tests-coverage: tests/test_clientes_us_cli_002_visao360.py

from __future__ import annotations

from django.db import migrations

CREATE_SQL = """
-- RLS pattern v2
ALTER TABLE acessos_dados_cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE acessos_dados_cliente FORCE ROW LEVEL SECURITY;

CREATE POLICY acessos_tenant_isolation_select ON acessos_dados_cliente
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY acessos_tenant_isolation_insert ON acessos_dados_cliente
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- Trigger anti-mutation (INV-013 estendida)
CREATE OR REPLACE FUNCTION acessos_bloqueia_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'acessos_dados_cliente eh INSERT-only (INV-013). % bloqueado em trigger PG.',
        TG_OP
    USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER acessos_anti_update
    BEFORE UPDATE ON acessos_dados_cliente
    FOR EACH ROW EXECUTE FUNCTION acessos_bloqueia_mutation();

CREATE TRIGGER acessos_anti_delete
    BEFORE DELETE ON acessos_dados_cliente
    FOR EACH ROW EXECUTE FUNCTION acessos_bloqueia_mutation();

-- CHECK constraints enum (R1 + R2 advogado)
ALTER TABLE acessos_dados_cliente
    ADD CONSTRAINT chk_acesso_finalidade_enum
    CHECK (finalidade IN (
        'atendimento_pos_venda',
        'preparar_orcamento',
        'executar_os',
        'emitir_documento_fiscal',
        'cobranca_inadimplencia',
        'auditoria_interna',
        'atendimento_lgpd_titular',
        'investigacao_incidente'
    ));

ALTER TABLE acessos_dados_cliente
    ADD CONSTRAINT chk_acesso_categoria_enum
    CHECK (categoria_dado_acessado IN (
        'pii_identificadora',
        'pii_sensivel',
        'dado_fiscal',
        'dado_regulatorio',
        'metadado'
    ));

-- Indice expressional em auditoria pra timeline (TL1)
CREATE INDEX ix_audit_payload_cliente_id
    ON auditoria (tenant_id, (payload_jsonb->>'cliente_id'), timestamp DESC)
    WHERE payload_jsonb ? 'cliente_id';
"""

DROP_SQL = """
DROP INDEX IF EXISTS ix_audit_payload_cliente_id;
ALTER TABLE acessos_dados_cliente DROP CONSTRAINT IF EXISTS chk_acesso_categoria_enum;
ALTER TABLE acessos_dados_cliente DROP CONSTRAINT IF EXISTS chk_acesso_finalidade_enum;
DROP TRIGGER IF EXISTS acessos_anti_delete ON acessos_dados_cliente;
DROP TRIGGER IF EXISTS acessos_anti_update ON acessos_dados_cliente;
DROP FUNCTION IF EXISTS acessos_bloqueia_mutation();
DROP POLICY IF EXISTS acessos_tenant_isolation_insert ON acessos_dados_cliente;
DROP POLICY IF EXISTS acessos_tenant_isolation_select ON acessos_dados_cliente;
ALTER TABLE acessos_dados_cliente DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0004_acessos_dados_cliente")]
    operations = [migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL)]
