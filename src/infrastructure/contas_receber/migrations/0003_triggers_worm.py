"""T-CR-024 — Triggers PG WORM (ADR-0031 / D-CR-6/17 / INV-CR-PAGAMENTO-WORM).

Espelha o molde fiscal (0003) e calibração (0015_perfil_no_evento_san_perfil).

1. `titulo_receber_block_delete` — BEFORE DELETE: bloqueia DELETE físico.
   Título é documento probatório (retenção 25a perfil A — ADR-0021 / INV-TENANT-001).
   Cancelamento usa `estado=cancelado` + `cancelado_em`, nunca DELETE físico.

2. `titulo_receber_worm_check` — BEFORE UPDATE: campos PROBATÓRIOS congelados
   pós-INSERT (D-CR-6/17):
     Imutáveis: valor_original, tenant_id, cliente_referencia_hash, os_id_origem,
                nfse_id_origem, perfil_no_evento, data_emissao, categoria_receita,
                origem, cliente_key_id, criado_em.
     Mutáveis: estado, data_baixa (one-shot), cancelado_em (one-shot),
               gateway_externo_id, linha_digitavel, qr_code, tx_id,
               convenio_pix_id, revision, atualizado_em.
   `data_baixa` e `cancelado_em` ONE-SHOT (NULL→valor; nunca muda depois).

3. `pagamento_titulo_block_update` + `pagamento_titulo_block_delete`
   — INSERT-only puro (INV-CR-PAGAMENTO-WORM / D-CR-8).

4. `override_bloqueio_block_update` + `override_bloqueio_block_delete`
   — INSERT-only puro (INV-CR-OVERRIDE-WORM / D-CR-10).

5. `titulo_receber_perfil_fallback` — BEFORE INSERT em titulo_receber:
   `NEW.perfil_no_evento := COALESCE(NEW.perfil_no_evento,
     NULLIF(current_setting('app.perfil_tenant', true), ''))`.
   SÓ preenche se chegou NULL; NUNCA sobrescreve (R4 / INV-FIN-SNAPSHOT-PERFIL-001).

# audit-immutability: triggers WORM contas-receber (nao tocam cadeia auditoria)
# tests-coverage: tests/test_contas_receber_schema_fatia1b.py
# (cobertura WORM block-delete/imutavel/one-shot/INSERT-only) + management/commands/validar_contas_receber.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. titulo_receber — block-delete (retencao 25a / ADR-0021)
-- =============================================================
CREATE OR REPLACE FUNCTION titulo_receber_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CR: titulo_receber nao pode ser deletado fisicamente '
        '(retencao 25a perfil A — ADR-0021 / D-CR-17). '
        'Use estado=cancelado + cancelado_em.';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER titulo_receber_block_delete_trg
    BEFORE DELETE ON titulo_receber
    FOR EACH ROW
    EXECUTE FUNCTION titulo_receber_block_delete();

-- =============================================================
-- 2. titulo_receber — WORM check (campos probatorios imutaveis)
-- =============================================================
CREATE OR REPLACE FUNCTION titulo_receber_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos probatorios congelados pos-INSERT (D-CR-6/17).
    IF NEW.valor_original IS DISTINCT FROM OLD.valor_original
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.cliente_referencia_hash IS DISTINCT FROM OLD.cliente_referencia_hash
       OR NEW.cliente_key_id IS DISTINCT FROM OLD.cliente_key_id
       OR NEW.os_id_origem IS DISTINCT FROM OLD.os_id_origem
       OR NEW.nfse_id_origem IS DISTINCT FROM OLD.nfse_id_origem
       OR NEW.perfil_no_evento IS DISTINCT FROM OLD.perfil_no_evento
       OR NEW.data_emissao IS DISTINCT FROM OLD.data_emissao
       OR NEW.categoria_receita IS DISTINCT FROM OLD.categoria_receita
       OR NEW.origem IS DISTINCT FROM OLD.origem
       OR NEW.criado_em IS DISTINCT FROM OLD.criado_em
    THEN
        RAISE EXCEPTION
            'INV-CR/WORM: campos probatorios de titulo_receber sao imutaveis '
            'pos-INSERT (ADR-0031 Padrao B / D-CR-17). '
            'So estado/data_baixa/cancelado_em/dados-gateway transitam.';
    END IF;

    -- data_baixa one-shot (NULL -> valor; nunca volta nem muda)
    IF OLD.data_baixa IS NOT NULL
       AND NEW.data_baixa IS DISTINCT FROM OLD.data_baixa THEN
        RAISE EXCEPTION
            'INV-CR: data_baixa e one-shot (imutavel apos preenchida).';
    END IF;

    -- cancelado_em one-shot
    IF OLD.cancelado_em IS NOT NULL
       AND NEW.cancelado_em IS DISTINCT FROM OLD.cancelado_em THEN
        RAISE EXCEPTION
            'INV-CR: cancelado_em e one-shot (imutavel apos preenchida).';
    END IF;

    RETURN NEW;
END;
$body$;

CREATE TRIGGER titulo_receber_worm_check_trg
    BEFORE UPDATE ON titulo_receber
    FOR EACH ROW
    EXECUTE FUNCTION titulo_receber_worm_check();

-- =============================================================
-- 3. pagamento_titulo — INSERT-only puro (INV-CR-PAGAMENTO-WORM)
-- =============================================================
CREATE OR REPLACE FUNCTION pagamento_titulo_block_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CR-PAGAMENTO-WORM: pagamento_titulo e INSERT-only. '
        'Nao e permitido UPDATE (D-CR-8 / ADR-0031 Padrao B).';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER pagamento_titulo_block_update_trg
    BEFORE UPDATE ON pagamento_titulo
    FOR EACH ROW
    EXECUTE FUNCTION pagamento_titulo_block_update();

CREATE OR REPLACE FUNCTION pagamento_titulo_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CR-PAGAMENTO-WORM: pagamento_titulo e INSERT-only. '
        'Nao e permitido DELETE (D-CR-8 / ADR-0031 Padrao B).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER pagamento_titulo_block_delete_trg
    BEFORE DELETE ON pagamento_titulo
    FOR EACH ROW
    EXECUTE FUNCTION pagamento_titulo_block_delete();

-- =============================================================
-- 4. override_bloqueio — INSERT-only puro (INV-CR-OVERRIDE-WORM)
-- =============================================================
CREATE OR REPLACE FUNCTION override_bloqueio_block_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CR-OVERRIDE-WORM: override_bloqueio e INSERT-only. '
        'Nao e permitido UPDATE (D-CR-10 / ADR-0031 Padrao B).';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER override_bloqueio_block_update_trg
    BEFORE UPDATE ON override_bloqueio
    FOR EACH ROW
    EXECUTE FUNCTION override_bloqueio_block_update();

CREATE OR REPLACE FUNCTION override_bloqueio_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CR-OVERRIDE-WORM: override_bloqueio e INSERT-only. '
        'Nao e permitido DELETE (D-CR-10 / ADR-0031 Padrao B).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER override_bloqueio_block_delete_trg
    BEFORE DELETE ON override_bloqueio
    FOR EACH ROW
    EXECUTE FUNCTION override_bloqueio_block_delete();

-- =============================================================
-- 5. titulo_receber — perfil_no_evento fallback COALESCE (R4)
--    SÓ preenche se chegou NULL; NUNCA sobrescreve (INV-FIN-SNAPSHOT-PERFIL-001).
-- =============================================================
CREATE OR REPLACE FUNCTION titulo_receber_perfil_fallback()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.perfil_no_evento IS NULL THEN
        NEW.perfil_no_evento := NULLIF(current_setting('app.perfil_tenant', true), '');
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER titulo_receber_perfil_fallback_trg
    BEFORE INSERT ON titulo_receber
    FOR EACH ROW
    EXECUTE FUNCTION titulo_receber_perfil_fallback();
"""

REVERSE = """
DROP TRIGGER IF EXISTS titulo_receber_perfil_fallback_trg ON titulo_receber;
DROP FUNCTION IF EXISTS titulo_receber_perfil_fallback();

DROP TRIGGER IF EXISTS override_bloqueio_block_delete_trg ON override_bloqueio;
DROP FUNCTION IF EXISTS override_bloqueio_block_delete();
DROP TRIGGER IF EXISTS override_bloqueio_block_update_trg ON override_bloqueio;
DROP FUNCTION IF EXISTS override_bloqueio_block_update();

DROP TRIGGER IF EXISTS pagamento_titulo_block_delete_trg ON pagamento_titulo;
DROP FUNCTION IF EXISTS pagamento_titulo_block_delete();
DROP TRIGGER IF EXISTS pagamento_titulo_block_update_trg ON pagamento_titulo;
DROP FUNCTION IF EXISTS pagamento_titulo_block_update();

DROP TRIGGER IF EXISTS titulo_receber_worm_check_trg ON titulo_receber;
DROP FUNCTION IF EXISTS titulo_receber_worm_check();
DROP TRIGGER IF EXISTS titulo_receber_block_delete_trg ON titulo_receber;
DROP FUNCTION IF EXISTS titulo_receber_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("contas_receber", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
