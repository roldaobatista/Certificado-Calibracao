# Fix bug latente M4 (descoberto no 1o INSERT PG-real de OrcamentoIncerteza, M8
# Fatia 2b): o valor canonico REGRA_ID='NIT_DICLA_030_2_DIGITOS_SIG' (27 chars) —
# usado em producao por calcular_orcamento_incerteza.py e como default do campo —
# NAO cabia em varchar(20). Toda a suite M4 usa Fakes in-memory, entao o estouro
# nunca foi exercido. Alargar varchar(20)->(40) e aditivo/nao-destrutivo (preserva
# dados; nao afeta calculo upstream). Sem este fix a emissao de certificado RBC
# (que consome OrcamentoPorPonto sob OrcamentoIncerteza) falharia em PG real.
#
# metrologia-classificacao: IQ
# replay-fixture: none

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibracao', '0019_orcamentoincerteza_cadeia_pontos_hash_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orcamentoincerteza',
            name='arredondamento_aplicado_regra',
            field=models.CharField(default='NIT_DICLA_030_2_DIGITOS_SIG', help_text='Regra de arredondamento (NIT-DICLA-030 §7.5).', max_length=40),
        ),
    ]
