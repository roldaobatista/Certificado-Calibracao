"""RLS + triggers Marco 2 - tabela `equipamentos` (T-EQP-001/008/010/049).

Coverage:
- INV-TENANT-001/002/003: RLS policies SELECT/UPDATE/DELETE/INSERT (mesmo
  pattern v2 do Marco 1, ADR-0002 §6).
- INV-EQP-001 (P-EQP-R1): trigger PG `equipamento_perfil_tenant_imutavel`
  BEFORE UPDATE bloqueia mutacao de `perfil_tenant_snapshot` +
  `snapshot_schema_version` (excecao unica via funcao SECURITY DEFINER
  `promover_perfil_equipamento_snapshot` - T-EQP-009).
- AC-EQP-001-8 (P-EQP-T9): trigger `equipamento_anti_orfao_imediato`
  BEFORE UPDATE detecta `cliente_atual_id` virou NULL via LGPD eliminacao
  e marca status=orfao_pendente_decisao.
- AC-EQP-006-3a (P-EQP-T2): trigger `bloquear_transicao_status_equipamento_invalida`
  BEFORE UPDATE consulta funcao `transicao_status_permitida(de, para)`
  com matriz declarativa.

# tests-coverage: tests/regressao/inv_eqp_001.py tests/regressao/inv_049_tag_unica.py tests/test_equipamentos_modelo.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- RLS pattern v2 (ADR-0002 §6) - igual clientes
-- =============================================================
ALTER TABLE equipamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_tenant_isolation_select ON equipamentos
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_tenant_isolation_update ON equipamentos
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_tenant_isolation_delete ON equipamentos
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_tenant_isolation_insert ON equipamentos
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- INV-EQP-001 (P-EQP-R1) - trigger imutabilidade perfil_tenant_snapshot
-- =============================================================
CREATE OR REPLACE FUNCTION equipamento_perfil_tenant_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Default: bloqueia mutacao do snapshot + schema_version pos-criacao.
    -- Excecao unica: funcao SECURITY DEFINER seta GUC
    -- `app.perfil_promocao_permitida='1'` (T-EQP-009 - promocao D->A).
    IF (OLD.perfil_tenant_snapshot IS DISTINCT FROM NEW.perfil_tenant_snapshot
        OR OLD.snapshot_schema_version IS DISTINCT FROM NEW.snapshot_schema_version)
       AND COALESCE(current_setting('app.perfil_promocao_permitida', true), '') != '1' THEN
        RAISE EXCEPTION
            'INV-EQP-001: perfil_tenant_snapshot imutavel pos-criacao. '
            'Promocao D->A unica via funcao promover_perfil_equipamento_snapshot.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER equipamento_perfil_tenant_imutavel_trg
    BEFORE UPDATE ON equipamentos
    FOR EACH ROW
    EXECUTE FUNCTION equipamento_perfil_tenant_imutavel_check();

-- =============================================================
-- AC-EQP-001-8 (P-EQP-T9) - trigger anti-orfao via LGPD eliminacao
-- =============================================================
CREATE OR REPLACE FUNCTION equipamento_anti_orfao_imediato_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Quando cliente_atual_id vira NULL (via signal Django ou ON DELETE),
    -- marca status=orfao_pendente_decisao automaticamente.
    IF OLD.cliente_atual_id IS NOT NULL
       AND NEW.cliente_atual_id IS NULL
       AND NEW.status NOT IN ('orfao_pendente_decisao', 'sucata', 'extraviado') THEN
        NEW.status := 'orfao_pendente_decisao';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER equipamento_anti_orfao_imediato_trg
    BEFORE UPDATE ON equipamentos
    FOR EACH ROW
    EXECUTE FUNCTION equipamento_anti_orfao_imediato_check();

-- =============================================================
-- AC-EQP-006-3a (P-EQP-T2) - maquina de estados Equipamento.status
-- =============================================================
CREATE OR REPLACE FUNCTION transicao_status_permitida(p_de text, p_para text)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $body$
BEGIN
    -- Matriz declarativa. NULL inicial -> ativo. Mesmo estado sempre OK.
    IF p_de IS NULL OR p_de = '' THEN RETURN p_para = 'ativo'; END IF;
    IF p_de = p_para THEN RETURN TRUE; END IF;
    IF (p_de, p_para) IN (
        ('ativo', 'inativo_temporario'), ('inativo_temporario', 'ativo'),
        ('ativo', 'aposentado'), ('aposentado', 'ativo'),
        ('ativo', 'em_calibracao_lab'), ('em_calibracao_lab', 'ativo'),
        ('ativo', 'sucata'), ('aposentado', 'sucata'),
        ('inativo_temporario', 'aposentado'), ('inativo_temporario', 'sucata'),
        ('em_calibracao_lab', 'aposentado'), ('em_calibracao_lab', 'sucata'),
        ('orfao_pendente_decisao', 'ativo'),
        ('orfao_pendente_decisao', 'aposentado'),
        ('orfao_pendente_decisao', 'sucata'),
        ('extraviado', 'ativo'),
        ('ativo', 'extraviado'), ('inativo_temporario', 'extraviado'),
        ('aposentado', 'extraviado'), ('em_calibracao_lab', 'extraviado'),
        ('sucata', 'extraviado'),
        -- Detecao automatica de orfao (trigger antes desta validacao):
        ('ativo', 'orfao_pendente_decisao'),
        ('inativo_temporario', 'orfao_pendente_decisao'),
        ('aposentado', 'orfao_pendente_decisao'),
        ('em_calibracao_lab', 'orfao_pendente_decisao')
    ) THEN RETURN TRUE; END IF;
    RETURN FALSE;
END;
$body$;

CREATE OR REPLACE FUNCTION bloquear_transicao_status_equipamento_invalida_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status
       AND NOT transicao_status_permitida(OLD.status, NEW.status) THEN
        RAISE EXCEPTION
            'AC-EQP-006-3a: transicao de status invalida (% -> %)',
            OLD.status, NEW.status;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER bloquear_transicao_status_equipamento_invalida_trg
    BEFORE UPDATE ON equipamentos
    FOR EACH ROW
    EXECUTE FUNCTION bloquear_transicao_status_equipamento_invalida_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS bloquear_transicao_status_equipamento_invalida_trg ON equipamentos;
DROP FUNCTION IF EXISTS bloquear_transicao_status_equipamento_invalida_check();
DROP FUNCTION IF EXISTS transicao_status_permitida(text, text);
DROP TRIGGER IF EXISTS equipamento_anti_orfao_imediato_trg ON equipamentos;
DROP FUNCTION IF EXISTS equipamento_anti_orfao_imediato_check();
DROP TRIGGER IF EXISTS equipamento_perfil_tenant_imutavel_trg ON equipamentos;
DROP FUNCTION IF EXISTS equipamento_perfil_tenant_imutavel_check();
DROP POLICY IF EXISTS equipamentos_tenant_isolation_insert ON equipamentos;
DROP POLICY IF EXISTS equipamentos_tenant_isolation_delete ON equipamentos;
DROP POLICY IF EXISTS equipamentos_tenant_isolation_update ON equipamentos;
DROP POLICY IF EXISTS equipamentos_tenant_isolation_select ON equipamentos;
ALTER TABLE equipamentos DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("equipamentos", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
