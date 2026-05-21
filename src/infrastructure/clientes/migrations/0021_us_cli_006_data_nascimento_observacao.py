"""T-CLI-117 + T-CLI-118 (US-CLI-006) — campos `data_nascimento` +
`observacao` com CHECK constraint anti < 18 anos (LGPD art. 14 +
NG-CLI-12).

BLOQ-TL-1 tech-lead: CHECK constraint cobre CREATE+UPDATE em camada
do banco (defesa em profundidade ao validador do serializer —
NG-CLI-12 vale CREATE+UPDATE conforme A6 advogado).

# tests-coverage: tests/test_us_cli_006_validadores_t_cli_117_118.py
"""

from __future__ import annotations

from django.db import migrations, models

FORWARD = """
-- T-CLI-118 (BLOQ-TL-1): CHECK anti < 18 anos
ALTER TABLE clientes ADD CONSTRAINT ck_cliente_idade_minima_18
    CHECK (
        data_nascimento IS NULL
        OR data_nascimento <= (current_date - interval '18 years')::date
    );
"""

REVERSE = """
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_idade_minima_18;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0020_cliente_identidade_historico"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="data_nascimento",
            field=models.DateField(
                blank=True,
                help_text="LGPD art. 14 + NG-CLI-12: cadastro PF < 18 anos rejeitado "
                "(CHECK constraint no banco). PJ deixa em branco.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="cliente",
            name="observacao",
            field=models.TextField(
                blank=True,
                help_text="Campo livre — passa por validador anti-PII sensivel "
                "(LGPD art. 11 + NG-CLI-11) no serializer.",
            ),
        ),
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
