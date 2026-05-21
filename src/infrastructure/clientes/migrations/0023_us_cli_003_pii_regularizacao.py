"""T-CLI-106 (AC-CLI-003-7) — campo `pii_regularizacao_em`.

Cliente importado com origem IMPORTACAO_LEGADA fica em ESTADO RESTRITO
(este campo NULL) — sem campanhas, sem compartilhamento intermodular —
até regularização formal (tenant captura aceite explícito do titular
ou aplica nova base legal).

Defaults da chamada do importador (BLOQ advogado §D + tech-lead §C
item 3) já entregam `aceite_lgpd_origem=IMPORTACAO_LEGADA` +
`aceite_lgpd_base_legal ∈ {EXECUCAO_CONTRATO, OBRIG_LEGAL}` quando
não há aceite explícito (use case `importar_clientes`). Este campo
fecha o estado restrito como diferenciador de aceite informal.

# tests-coverage: tests/test_us_cli_003_pii_regularizacao_t_cli_106.py
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0022_us_cli_006_consentimento_revogado"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="pii_regularizacao_em",
            field=models.DateTimeField(
                blank=True,
                help_text="T-CLI-106 (AC-CLI-003-7): cliente importado com origem "
                "IMPORTACAO_LEGADA fica em ESTADO RESTRITO (NULL aqui) — sem "
                "campanhas marketing, sem compartilhamento intermodular — até "
                "regularização. Tenant regulariza via fluxo de aceite formal → "
                "seta este timestamp.",
                null=True,
            ),
        ),
    ]
