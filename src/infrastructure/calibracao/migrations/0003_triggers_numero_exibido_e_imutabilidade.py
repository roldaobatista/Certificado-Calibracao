"""T-CAL-003 - Triggers PG: numero_exibido populador + imutabilidade pos-`aprovada`.

Cobertura:
- numero_exibido populado em BEFORE INSERT (PG nao aceita GENERATED
  STORED com EXTRACT — STABLE not IMMUTABLE). Garante consistencia
  mesmo em insert via raw SQL.
- INV-CAL-WORM-001 (Calibracao imutavel pos-aprovada): trigger BEFORE
  UPDATE/DELETE bloqueia mutacao quando OLD.status IN ('aprovada',
  'rejeitada', 'cancelada'). Estado terminal = forensico.

NAO cobre nesta migration (ficam em T-CAL-004+):
- Triggers WORM em entidades Leitura, LeituraCorrecao, OrcamentoIncerteza,
  ComponenteIncerteza, OrcamentoPorPonto, PadraoUsado, EventoDeCalibracao
  (uma trigger por tabela quando a entidade for criada).
- Trigger lock pos em_revisao_1 em PadraoUsado.snapshot_lock — T-CAL-008.

# audit-immutability: Calibracao em estados terminais
# tests-coverage: tests/regressao/test_inv_cal_worm_001_estado_terminal.py (T-CAL-145)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- numero_exibido populador (BEFORE INSERT)
-- =============================================================
-- 'CAL-' || EXTRACT(YEAR FROM criada_em) || '-' || LPAD(numero_interno, 6, '0')
-- Django seta criada_em via auto_now_add antes de chegar aqui;
-- numero_interno vem do DEFAULT sequence (migration 0001).
CREATE OR REPLACE FUNCTION calibracao_numero_exibido_populator()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.numero_exibido IS NULL OR NEW.numero_exibido = '' THEN
        NEW.numero_exibido := 'CAL-' ||
            EXTRACT(YEAR FROM NEW.criada_em)::text || '-' ||
            LPAD(NEW.numero_interno::text, 6, '0');
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER calibracao_numero_exibido_trg
    BEFORE INSERT ON calibracao
    FOR EACH ROW
    EXECUTE FUNCTION calibracao_numero_exibido_populator();

-- =============================================================
-- INV-CAL-WORM-001 — Calibracao imutavel em estados terminais
-- =============================================================
-- Estados terminais: aprovada, rejeitada, cancelada. UPDATE/DELETE
-- nesses estados bloqueia (INV-CAL-WORM-001 spec §4.1). Reprocessar
-- exige nova Calibracao com causation_id apontando a esta.
CREATE OR REPLACE FUNCTION calibracao_anti_mutation_terminal_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('aprovada', 'rejeitada', 'cancelada') THEN
            -- Permite apenas ajuste de causation_id (referenciar nova
            -- calibracao que substituiu esta — uso defensivo); demais
            -- campos sao bloqueados.
            IF NEW.status IS DISTINCT FROM OLD.status
               OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
               OR NEW.numero_interno IS DISTINCT FROM OLD.numero_interno
               OR NEW.cliente_referencia_hash IS DISTINCT FROM OLD.cliente_referencia_hash
               OR NEW.snapshot_equipamento_json IS DISTINCT FROM OLD.snapshot_equipamento_json
               OR NEW.procedimento_versao_snapshot IS DISTINCT FROM OLD.procedimento_versao_snapshot
               OR NEW.regra_decisao IS DISTINCT FROM OLD.regra_decisao
               OR NEW.regra_decisao_acordada_hash IS DISTINCT FROM OLD.regra_decisao_acordada_hash
               OR NEW.zona_ilac_g8 IS DISTINCT FROM OLD.zona_ilac_g8
               OR NEW.decisao IS DISTINCT FROM OLD.decisao
               OR NEW.pfa_calculada IS DISTINCT FROM OLD.pfa_calculada
               OR NEW.pra_calculada IS DISTINCT FROM OLD.pra_calculada
               OR NEW.executor_id IS DISTINCT FROM OLD.executor_id
               OR NEW.revisor_id IS DISTINCT FROM OLD.revisor_id
               OR NEW.conferente_id IS DISTINCT FROM OLD.conferente_id
               OR NEW.recebedor_user_id IS DISTINCT FROM OLD.recebedor_user_id
               OR NEW.snapshot_competencia_revisor_json
                  IS DISTINCT FROM OLD.snapshot_competencia_revisor_json
               OR NEW.snapshot_competencia_conferente_json
                  IS DISTINCT FROM OLD.snapshot_competencia_conferente_json
               OR NEW.versao_motor_calculo IS DISTINCT FROM OLD.versao_motor_calculo
            THEN
                RAISE EXCEPTION
                    'INV-CAL-WORM-001: Calibracao em estado terminal (%) e imutavel — reprocessar exige nova calibracao com causation_id (spec §4.1)',
                    OLD.status;
            END IF;
        END IF;
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.status IN ('aprovada', 'rejeitada', 'cancelada') THEN
            RAISE EXCEPTION
                'INV-CAL-WORM-001: Calibracao em estado terminal (%) nao pode ser deletada (audit imutavel — ISO 17025 cl. 7.5 + cl. 8.4 retencao 25a)',
                OLD.status;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER calibracao_anti_mutation_terminal_trg
    BEFORE UPDATE OR DELETE ON calibracao
    FOR EACH ROW
    EXECUTE FUNCTION calibracao_anti_mutation_terminal_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS calibracao_anti_mutation_terminal_trg ON calibracao;
DROP FUNCTION IF EXISTS calibracao_anti_mutation_terminal_check();
DROP TRIGGER IF EXISTS calibracao_numero_exibido_trg ON calibracao;
DROP FUNCTION IF EXISTS calibracao_numero_exibido_populator();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("calibracao", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
