"""FA-A1 — alarga Cliente.aceite_lgpd_ip_hash para TextField.

Hash de PII agora PREFIXADO com a versao da chave ('v1:'+64hex = 67 chars),
estourava varchar(64). TextField (sem limite) e imune ao crescimento futuro
do key_id; no Postgres `text` nao tem custo vs varchar.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0014_rls_fail_loud"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cliente",
            name="aceite_lgpd_ip_hash",
            field=models.TextField(blank=True),
        ),
    ]
