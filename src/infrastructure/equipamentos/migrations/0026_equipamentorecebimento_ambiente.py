"""T-EQP-055 (US-EQP-006 AC-EQP-006-7b / P-EQP-R3) — condicoes ambientais
no `EquipamentoRecebimento` + trigger PG imutabilidade pos-INSERT.

Adiciona 4 campos:
- `temp_ambiente_c` DECIMAL(5,2) NULL  — temperatura em C (faixa -50..80).
- `ur_percentual` DECIMAL(5,2) NULL    — umidade relativa em % (0..100).
- `pressao_kpa` DECIMAL(6,2) NULL      — pressao em kPa (50..120).
- `justificativa_condicoes_ambientais_ausentes` TEXT default ''
  — justificativa obrigatoria quando NENHUM dos 3 acima preenchido
  (validacao em service + clean(); anti-PII via validator dedicado).

NULL permitido com justificativa quando a grandeza nao exige medicao
ambiental (RBC cl. 6.3 + ISO/IEC 17025 cl. 6.4.10). Wave A vai trocar
para enum por-grandeza (matriz exigencia ambiental).

Trigger PG `recebimento_ambiente_imutavel_check` (BEFORE UPDATE):
bloqueia mutacao em qualquer dos 4 campos pos-INSERT — registro do
estado ambiental no momento da recepcao e WORM (ISO 17025 cl. 7.4
+ RBC NIT-DICLA-021).

CHECK PG `ck_recebimento_ambiente_faixa_razoavel`: rejeita valores
absurdos no INSERT (defesa contra digitacao errada — operador atrapalha
fluxo se grava 1000°C ou -300%).

# tests-coverage: tests/test_equipamentos_recebimento_ambiente_t_eqp_055.py
"""

from __future__ import annotations

from django.db import migrations, models

SQL_FORWARD = """
-- =============================================================
-- T-EQP-055 (P-EQP-R3) — trigger imutabilidade pos-INSERT em
-- temp_ambiente_c, ur_percentual, pressao_kpa,
-- justificativa_condicoes_ambientais_ausentes.
-- ISO/IEC 17025 cl. 7.4 + RBC NIT-DICLA-021 — WORM 25 anos.
-- =============================================================
CREATE OR REPLACE FUNCTION recebimento_ambiente_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.temp_ambiente_c IS DISTINCT FROM OLD.temp_ambiente_c THEN
        RAISE EXCEPTION
            'T-EQP-055 (P-EQP-R3): temp_ambiente_c imutavel pos-INSERT (ISO 17025 cl. 7.4).';
    END IF;
    IF NEW.ur_percentual IS DISTINCT FROM OLD.ur_percentual THEN
        RAISE EXCEPTION
            'T-EQP-055 (P-EQP-R3): ur_percentual imutavel pos-INSERT (ISO 17025 cl. 7.4).';
    END IF;
    IF NEW.pressao_kpa IS DISTINCT FROM OLD.pressao_kpa THEN
        RAISE EXCEPTION
            'T-EQP-055 (P-EQP-R3): pressao_kpa imutavel pos-INSERT (ISO 17025 cl. 7.4).';
    END IF;
    IF NEW.justificativa_condicoes_ambientais_ausentes IS DISTINCT FROM OLD.justificativa_condicoes_ambientais_ausentes THEN
        RAISE EXCEPTION
            'T-EQP-055 (P-EQP-R3): justificativa_condicoes_ambientais_ausentes imutavel pos-INSERT (ISO 17025 cl. 7.4).';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER recebimento_ambiente_imutavel_trg
    BEFORE UPDATE ON equipamentos_recebimento
    FOR EACH ROW
    EXECUTE FUNCTION recebimento_ambiente_imutavel_check();

-- =============================================================
-- T-EQP-055 — CHECK constraint faixa razoavel.
-- Permite NULL; quando preenchido, bloqueia valores absurdos.
-- =============================================================
ALTER TABLE equipamentos_recebimento
    ADD CONSTRAINT ck_recebimento_ambiente_faixa_razoavel
    CHECK (
        (temp_ambiente_c IS NULL OR (temp_ambiente_c >= -50 AND temp_ambiente_c <= 80))
        AND (ur_percentual IS NULL OR (ur_percentual >= 0 AND ur_percentual <= 100))
        AND (pressao_kpa IS NULL OR (pressao_kpa >= 50 AND pressao_kpa <= 120))
    );
"""

SQL_BACKWARD = """
ALTER TABLE equipamentos_recebimento
    DROP CONSTRAINT IF EXISTS ck_recebimento_ambiente_faixa_razoavel;

DROP TRIGGER IF EXISTS recebimento_ambiente_imutavel_trg ON equipamentos_recebimento;
DROP FUNCTION IF EXISTS recebimento_ambiente_imutavel_check();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("equipamentos", "0025_seed_authz_provisorio"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipamentorecebimento",
            name="temp_ambiente_c",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Temperatura ambiente em °C no momento da recepcao "
                    "(P-EQP-R3). NULL permitido com justificativa."
                ),
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipamentorecebimento",
            name="ur_percentual",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Umidade relativa em % no momento da recepcao "
                    "(P-EQP-R3). NULL permitido com justificativa."
                ),
                max_digits=5,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipamentorecebimento",
            name="pressao_kpa",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Pressao atmosferica em kPa no momento da recepcao "
                    "(P-EQP-R3). NULL permitido com justificativa."
                ),
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="equipamentorecebimento",
            name="justificativa_condicoes_ambientais_ausentes",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Obrigatoria quando temp/ur/pressao sao todos NULL "
                    "(P-EQP-R3). >=20 chars + anti-PII. Texto cru "
                    "(auditoria ISO 17025)."
                ),
            ),
        ),
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_BACKWARD,
        ),
    ]
