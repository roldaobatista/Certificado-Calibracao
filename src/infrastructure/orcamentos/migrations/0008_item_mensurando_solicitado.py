"""T-ORC-033 (Onda 2c) — item declara o MENSURANDO solicitado (D-ORC-5).

Consultor-rbc C1-ORC-MENSURANDO: a analise critica cl. 7.1.1 precisa de
grandeza/faixa/unidade por item de calibracao. O `Equipamento` so tem `faixa`
string livre (nao herdavel); espelha-se o ADR-0076 da Calibracao — o item DECLARA
o mensurando a calibrar. 4 colunas tipadas + CHECK condicional:
  tipo_atividade_alvo='calibracao'  -> mensurando NOT NULL (faixa_min < faixa_max)
  tipo_atividade_alvo<>'calibracao' -> mensurando ausente (NULL/'')

Aditivo (tabela vazia em Wave A). Nomes `*_solicitada` (NAO `*_calibrada`): aqui e
intencao comercial, ainda nao travada pelo RT (C1-ORC-MENSURANDO-1).

# policy-test-coverage: skip -- AddField + CHECK; sem CREATE POLICY
"""

from __future__ import annotations

from django.db import migrations, models

_CHECK_NAME = "ck_orc_item_mensurando_calibracao"

_CHECK_SQL = f"""
ALTER TABLE item_orcamento ADD CONSTRAINT {_CHECK_NAME} CHECK (
    (
        tipo_atividade_alvo = 'calibracao'
        AND grandeza_solicitada <> '' AND unidade_solicitada <> ''
        AND faixa_solicitada_min IS NOT NULL AND faixa_solicitada_max IS NOT NULL
        AND faixa_solicitada_min < faixa_solicitada_max
    )
    OR (
        tipo_atividade_alvo <> 'calibracao'
        AND grandeza_solicitada = '' AND unidade_solicitada = ''
        AND faixa_solicitada_min IS NULL AND faixa_solicitada_max IS NULL
    )
);
"""

_CHECK_REVERSE = f"ALTER TABLE item_orcamento DROP CONSTRAINT IF EXISTS {_CHECK_NAME};"


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0007_item_semaforo_maxlen"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemorcamento",
            name="grandeza_solicitada",
            field=models.CharField(
                blank=True,
                help_text="VO Grandeza (massa/temperatura/...). '' se nao-calibracao.",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="itemorcamento",
            name="faixa_solicitada_min",
            field=models.DecimalField(
                blank=True,
                decimal_places=12,
                help_text="Limite inferior a calibrar.",
                max_digits=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="itemorcamento",
            name="faixa_solicitada_max",
            field=models.DecimalField(
                blank=True,
                decimal_places=12,
                help_text="Limite superior a calibrar.",
                max_digits=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="itemorcamento",
            name="unidade_solicitada",
            field=models.CharField(
                blank=True,
                help_text="Unidade SI/RBC (whitelist FaixaMedicao). '' se nao-calibracao.",
                max_length=20,
            ),
        ),
        migrations.RunSQL(sql=_CHECK_SQL, reverse_sql=_CHECK_REVERSE),
    ]
