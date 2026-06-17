"""T-AGE-025 — Triggers PG WORM INSERT-only nas tabelas imutáveis da agenda.

INV-AG-AUDIT-WORM-001 / ADR-0031 Padrão B INSERT-only.

Tabelas INSERT-only (block-update + block-delete):
1. ``evento_auditoria_agenda`` — trilha de auditoria da agenda (retenção ≥5a).
2. ``registro_no_show``        — registro de no-show (prova de fato).
3. ``regime_jornada_colaborador`` — override de regime de jornada (ato de RH).

Semântica: cada linha é imutável assim que inserida. Para "atualizar" um regime
de jornada, insere-se nova linha com nova ``vigencia_inicio`` (INSERT-com-vigência
— D-AGE-15). A consulta "regime vigente em data D" pega o maior ``vigencia_inicio``
≤ D (padrão temporal canônico ADR-0030).

Molde: ``contas_receber/migrations/0003_triggers_worm.py``
(pagamento_titulo_block_update / pagamento_titulo_block_delete).

# audit-immutability: triggers WORM agenda (não tocam cadeia auditoria)
# tests-coverage: tests/test_agenda_schema_fatia1b.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. evento_auditoria_agenda — INSERT-only (INV-AG-AUDIT-WORM-001)
-- =============================================================
CREATE OR REPLACE FUNCTION evento_auditoria_agenda_block_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-AUDIT-WORM-001: evento_auditoria_agenda e INSERT-only. '
        'Nao e permitido UPDATE (ADR-0031 Padrao B / D-AGE-3).';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER evento_auditoria_agenda_block_update_trg
    BEFORE UPDATE ON evento_auditoria_agenda
    FOR EACH ROW
    EXECUTE FUNCTION evento_auditoria_agenda_block_update();

CREATE OR REPLACE FUNCTION evento_auditoria_agenda_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-AUDIT-WORM-001: evento_auditoria_agenda e INSERT-only. '
        'Nao e permitido DELETE (ADR-0031 Padrao B / D-AGE-3).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER evento_auditoria_agenda_block_delete_trg
    BEFORE DELETE ON evento_auditoria_agenda
    FOR EACH ROW
    EXECUTE FUNCTION evento_auditoria_agenda_block_delete();

-- =============================================================
-- 2. registro_no_show — INSERT-only (INV-AG-AUDIT-WORM-001 / D-AGE-9)
-- =============================================================
CREATE OR REPLACE FUNCTION registro_no_show_block_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-AUDIT-WORM-001: registro_no_show e INSERT-only. '
        'Nao e permitido UPDATE (ADR-0031 Padrao B / D-AGE-9).';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER registro_no_show_block_update_trg
    BEFORE UPDATE ON registro_no_show
    FOR EACH ROW
    EXECUTE FUNCTION registro_no_show_block_update();

CREATE OR REPLACE FUNCTION registro_no_show_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-AUDIT-WORM-001: registro_no_show e INSERT-only. '
        'Nao e permitido DELETE (ADR-0031 Padrao B / D-AGE-9).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER registro_no_show_block_delete_trg
    BEFORE DELETE ON registro_no_show
    FOR EACH ROW
    EXECUTE FUNCTION registro_no_show_block_delete();

-- =============================================================
-- 3. regime_jornada_colaborador — INSERT-only (INV-AG-REGIME-001 / D-AGE-15)
-- =============================================================
CREATE OR REPLACE FUNCTION regime_jornada_colaborador_block_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-REGIME-001: regime_jornada_colaborador e INSERT-only. '
        'Nao e permitido UPDATE (ADR-0031 Padrao B / D-AGE-15). '
        'Para alterar o regime, inserir nova linha com nova vigencia_inicio.';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER regime_jornada_colaborador_block_update_trg
    BEFORE UPDATE ON regime_jornada_colaborador
    FOR EACH ROW
    EXECUTE FUNCTION regime_jornada_colaborador_block_update();

CREATE OR REPLACE FUNCTION regime_jornada_colaborador_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-AG-REGIME-001: regime_jornada_colaborador e INSERT-only. '
        'Nao e permitido DELETE (ADR-0031 Padrao B / D-AGE-15). '
        'Para encerrar vigencia, inserir nova linha com vigencia_fim preenchido.';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER regime_jornada_colaborador_block_delete_trg
    BEFORE DELETE ON regime_jornada_colaborador
    FOR EACH ROW
    EXECUTE FUNCTION regime_jornada_colaborador_block_delete();
"""

REVERSE = """
DROP TRIGGER IF EXISTS regime_jornada_colaborador_block_delete_trg ON regime_jornada_colaborador;
DROP FUNCTION IF EXISTS regime_jornada_colaborador_block_delete();
DROP TRIGGER IF EXISTS regime_jornada_colaborador_block_update_trg ON regime_jornada_colaborador;
DROP FUNCTION IF EXISTS regime_jornada_colaborador_block_update();

DROP TRIGGER IF EXISTS registro_no_show_block_delete_trg ON registro_no_show;
DROP FUNCTION IF EXISTS registro_no_show_block_delete();
DROP TRIGGER IF EXISTS registro_no_show_block_update_trg ON registro_no_show;
DROP FUNCTION IF EXISTS registro_no_show_block_update();

DROP TRIGGER IF EXISTS evento_auditoria_agenda_block_delete_trg ON evento_auditoria_agenda;
DROP FUNCTION IF EXISTS evento_auditoria_agenda_block_delete();
DROP TRIGGER IF EXISTS evento_auditoria_agenda_block_update_trg ON evento_auditoria_agenda;
DROP FUNCTION IF EXISTS evento_auditoria_agenda_block_update();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0003_exclusion_overlap"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
