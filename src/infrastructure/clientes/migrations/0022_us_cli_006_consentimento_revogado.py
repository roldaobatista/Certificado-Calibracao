"""T-CLI-115 (AC-CLI-006-2) — campo `consentimento_revogado_em`.

Revogacao de consentimento (LGPD art. 8º §5º). Efeito ≤ 1 min:
quando setado, base CONSENTIMENTO deixa de aplicar; outras bases
(EXECUCAO_CONTRATO, OBRIG_LEGAL, LEGITIMO_INTERESSE) subsistem
conforme mapa em `politicas_lgpd.MAPA_FINALIDADE_BASE_LEGAL_ACEITA`
(BLOQ-A2 advogado).

# tests-coverage: tests/test_us_cli_006_revogacao_incidente_t_cli_115_119.py
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0021_us_cli_006_data_nascimento_observacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="consentimento_revogado_em",
            field=models.DateTimeField(
                blank=True,
                help_text="LGPD art. 8º §5º — timestamp da revogação do consentimento. "
                "NULL = consentimento vigente (se houver). Bases não-CONSENTIMENTO "
                "continuam aplicáveis conforme mapa POLITICA.",
                null=True,
            ),
        ),
    ]
