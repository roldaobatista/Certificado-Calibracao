"""P9 conserto SEG-M1 (auditor-seguranca): colunas de motivo 200->600.

Os serializers aceitam motivo ate 500 chars e `corrigir_versao` prefixa
"correcao da vN: " — motivo de 201-500 chars estourava varchar(200) em
DataError 500 nao tratado (e chave de idempotencia presa). Aditiva
(ALTER TYPE); dados existentes intactos; views ganham except DataError->400
no mesmo conserto.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos_pecas_servicos', '0009_grants_staging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemcatalogoversao',
            name='motivo',
            field=models.CharField(blank=True, default='', help_text='Texto livre — em evento WORM vai HASHIFICADO (ADV-PPS-02).', max_length=600),
        ),
        migrations.AlterField(
            model_name='itemcatalogoversao',
            name='motivo_revogacao',
            field=models.CharField(blank=True, default='', max_length=600),
        ),
        migrations.AlterField(
            model_name='linhatabelapreco',
            name='motivo_revogacao',
            field=models.CharField(blank=True, default='', max_length=600),
        ),
    ]
