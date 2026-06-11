"""T-PPS-041 — staging da importação CSV (US-CAT-004, molde EscopoExtraido M6).

2 tabelas MUTÁVEIS (staging, NÃO WORM — TTL 90d via `limpar_importacoes_expiradas`,
ADV-PPS-06): `importacao_catalogo` (lote: sha256 + nome_hash + totais) +
`importacao_catalogo_linha` (linha tipada validada|rejeitada|aceita). Nenhum
item de catálogo nasce aqui (INV-PPS-IMPORTACAO-STAGING).

# rls-policy: external 0008_rls_staging — RLS pattern v2 na migration irmã
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos_pecas_servicos', '0006_seed_authz_catalogo'),
        ('tenant', '0012_aplicar_evento_cgcre_vigencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportacaoCatalogo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('arquivo_sha256', models.CharField(help_text='SHA-256 do arquivo original (prova de integridade).', max_length=64)),
                ('arquivo_nome_hash', models.CharField(blank=True, default='', help_text='Nome de arquivo pode carregar PII — só o hash (minimização).', max_length=80)),
                ('total_linhas', models.PositiveIntegerField()),
                ('criado_por', models.UUIDField()),
                ('criado_em', models.DateTimeField(db_index=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='importacoes_catalogo', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Importação de catálogo (staging)',
                'verbose_name_plural': 'Importações de catálogo (staging)',
                'db_table': 'importacao_catalogo',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='ImportacaoCatalogoLinha',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('linha_numero', models.PositiveIntegerField(help_text='2-based (linha 1 = header).')),
                ('status', models.CharField(choices=[('validada', 'validada'), ('rejeitada', 'rejeitada'), ('aceita', 'aceita')], max_length=10)),
                ('codigo_interno', models.CharField(blank=True, default='', max_length=60)),
                ('tipo', models.CharField(blank=True, default='', max_length=10)),
                ('nome', models.CharField(blank=True, default='', max_length=200)),
                ('unidade_medida', models.CharField(blank=True, default='', max_length=20)),
                ('preco_padrao', models.DecimalField(blank=True, decimal_places=2, help_text='Parseado (dialeto BR); NULL em linha rejeitada no parse.', max_digits=12, null=True)),
                ('categoria', models.CharField(blank=True, default='', max_length=100)),
                ('descricao', models.CharField(blank=True, default='', max_length=2000)),
                ('codigo_fabricante', models.CharField(blank=True, default='', max_length=60)),
                ('motivo_rejeicao', models.CharField(blank=True, default='', max_length=300)),
                ('item_criado_id', models.UUIDField(blank=True, help_text='Preenchido no aceite (one-shot).', null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('importacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linhas', to='produtos_pecas_servicos.importacaocatalogo')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='linhas_importacao_catalogo', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Linha de importação de catálogo (staging)',
                'verbose_name_plural': 'Linhas de importação de catálogo (staging)',
                'db_table': 'importacao_catalogo_linha',
                'indexes': [models.Index(fields=['tenant', 'importacao', 'status'], name='ix_pps_imp_linha_status')],
                'constraints': [models.UniqueConstraint(fields=('tenant', 'importacao', 'linha_numero'), name='uq_pps_imp_linha_numero')],
            },
        ),
    ]
