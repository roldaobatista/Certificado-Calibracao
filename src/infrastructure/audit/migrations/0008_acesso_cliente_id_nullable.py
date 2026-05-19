"""CONCERN auditor Seguranca 2026-05-18: torna `cliente_id` nullable em
`AcessoDadosCliente` pra acessos agregados (lista historica de importacoes,
buscas que nao apontam pra cliente unico).

Antes: view `importacoes` usava `uuid.uuid4()` como placeholder fake — quebra
rastreabilidade (apontava pra cliente que nao existia). Agora aceita NULL
pra esses cases.

`AlterField` finalidade aparece junto porque o Django detectou que o enum
em codigo agora inclui `consulta_relatorio_importacao` (acrescentada em
migration 0007). Sem operacao real no banco — sincroniza state do Django.
"""

# rls-policy: external 0006 -- nao cria tabela; so altera coluna existente
# tests-coverage: tests/test_clientes_us_cli_003_importar.py

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0007_acesso_finalidade_consulta_importacao"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acessodadoscliente",
            name="cliente_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="acessodadoscliente",
            name="finalidade",
            field=models.CharField(
                choices=[
                    ("atendimento_pos_venda", "Atendimento Pos Venda"),
                    ("preparar_orcamento", "Preparar Orcamento"),
                    ("executar_os", "Executar Os"),
                    ("emitir_documento_fiscal", "Emitir Documento Fiscal"),
                    ("cobranca_inadimplencia", "Cobranca Inadimplencia"),
                    ("auditoria_interna", "Auditoria Interna"),
                    ("atendimento_lgpd_titular", "Atendimento Lgpd Titular"),
                    ("investigacao_incidente", "Investigacao Incidente"),
                    ("consulta_relatorio_importacao", "Consulta Relatorio Importacao"),
                ],
                help_text="Enum cravado pelo advogado (R2). CHECK constraint na migration.",
                max_length=40,
            ),
        ),
    ]
