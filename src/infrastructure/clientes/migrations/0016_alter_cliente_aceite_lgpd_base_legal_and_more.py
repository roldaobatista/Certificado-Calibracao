"""FA-M3 — reconcilia drift model↔migration de clientes.

`makemigrations --check` acusava 12 AlterField sem migration (US-CLI-001..
003 editaram `help_text`/atributos dos campos mas as migrations originais
não capturaram a deconstrução completa). São mudanças SÓ de metadata
(help_text) — nenhuma altera schema/null/max_length real, não geram DDL
de consequência. Esta migration zera o gate `makemigrations --check`.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0015_aceite_ip_hash_textfield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cliente",
            name="aceite_lgpd_base_legal",
            field=models.CharField(
                blank=True,
                help_text="Enum (lgpd.py BASES_LEGAIS_VALIDAS): art_7_v (execucao de contrato), art_7_i (consentimento) — usado quando aceite veio de fora (importacao com flag pf_aceite_origem). CHECK constraint na migration.",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="aceite_lgpd_evidencia_externa",
            field=models.CharField(
                blank=True,
                help_text="SHA-256 do termo declarado pelo tenant na importacao (R2 advogado). Vazio quando aceite eh do proprio sistema.",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="aceite_lgpd_ip_hash",
            field=models.TextField(
                blank=True,
                help_text="HMAC-SHA256 do IP do request, PREFIXADO com versao da chave (FA-A1: 'v1:'+64hex). LGPD art. 6 V + INV-013. TextField sem limite — imune a crescimento do key_id. Vazio se origem=balcao.",
            ),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="aceite_lgpd_pendente",
            field=models.BooleanField(
                default=False,
                help_text="True quando PJ traz contato/socio PF que ainda nao deu aceite (R1 advogado caminho 3). Bloqueia comunicacao WhatsApp em RAT-06 ate titular re-aceitar via portal Wave B.",
            ),
        ),
        migrations.AlterField(
            model_name="cliente",
            name="cpf_responsavel_legal",
            field=models.CharField(
                blank=True,
                help_text="CPF do responsavel/socio em PJ (R8 advogado caminho a). So preenchido quando tenant declara aceite do responsavel; caso contrario, contato PF separado eh criado (caminho b).",
                max_length=11,
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="arquivo_hash",
            field=models.CharField(
                help_text="SHA-256 dos bytes do arquivo CSV (sem PII — hash).", max_length=64
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="compromisso_comunicar_titulares",
            field=models.BooleanField(
                help_text="Checkbox 2: tenant declara que ja comunicou ou comunicara em ate 10 dias uteis aos titulares (LGPD art. 9)."
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="declara_sem_dados_sensiveis",
            field=models.BooleanField(
                help_text="Checkbox 3: tenant declara ausencia de dados sensiveis (LGPD art. 5 II)."
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="pf_aceite_origem",
            field=models.CharField(
                blank=True,
                help_text="Quando tenant libera PF em lote (R2 advogado): enum {contrato_preexistente_documentado, consentimento_coletado_offline, migracao_sistema_anterior_com_aceite}. Vazio = PF rejeitada.",
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="procedencia_declarada",
            field=models.CharField(
                help_text="Campo livre <=200 chars (ex: 'Bling v3 export 2026-04').", max_length=200
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="tem_base_legal",
            field=models.BooleanField(
                help_text="Checkbox 1: tenant declara que tem base legal documentada (contrato/consentimento/obrigacao legal) pra tratar os dados."
            ),
        ),
        migrations.AlterField(
            model_name="clienteimportacaodeclaracao",
            name="usuario_id",
            field=models.UUIDField(blank=True, help_text="Quem operou a importacao.", null=True),
        ),
    ]
