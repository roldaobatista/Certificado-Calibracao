"""FA-A1 — alarga AcessoDadosCliente.ip_hash para TextField.

O hash de PII passou a ser PREFIXADO com a versao da chave ('v1:'+64hex =
67 chars), estourava varchar(64). TextField (sem limite) e imune ao
crescimento futuro do key_id; no Postgres `text` nao tem custo vs varchar.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0009_auditoria_sequencia"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acessodadoscliente",
            name="ip_hash",
            field=models.TextField(blank=True),
        ),
    ]
