"""T-PRC-021 — CreateModel ×7 + UNIQUEs + CHECKs (frente precificacao).

UNIQUEs:
  uq_prc_regra_versao_n (tenant, item, versao_n) — INV-PRC-REGRA-IMUTAVEL.
  uq_prc_vinculo_cliente_vigente (tenant, cliente_id) parcial WHERE vigente —
    D-PRC-12: só 1 vínculo ativo por cliente.
  uq_prc_parametros_versao_n (tenant, versao_n) — singleton versionado.

CHECKs:
  ck_prc_pedido_decisor_independente — decisor_id != solicitante_id
    (INV-PRC-APROVACAO-INDEPENDENTE; NULL ok pré-decisão).

Estado one-shot no pedido:
  `estado` default='solicitado'; trigger 0003 garante SOLICITADO→APROVADO|NEGADO
  sem volta (INV-PRC-APROVACAO-ONE-SHOT).

# rls-policy: external 0002_rls_policies
# audit-immutability: skip -- CreateModel puro; triggers WORM em 0003
# tests-coverage: tests/test_precificacao_schema_fatia1b.py +
# management/commands/validar_precificacao.py
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenant", "0012_aplicar_evento_cgcre_vigencia"),
        ("produtos_pecas_servicos", "0011_p9_consertos_imutabilidade"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegraFormacaoPreco",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("modo", models.CharField(
                    choices=[("preco_fixo", "preco_fixo"), ("margem_alvo", "margem_alvo"), ("cost_plus", "cost_plus")],
                    help_text="preco_fixo|margem_alvo|cost_plus — imutável (trigger 0003).",
                    max_length=15,
                )),
                ("versao_n", models.IntegerField(
                    help_text="Denso por (tenant, item): 1,2,3... (max+1 sob advisory lock 880_404).",
                )),
                ("preco_fixo", models.DecimalField(
                    blank=True, decimal_places=2, max_digits=12, null=True,
                    help_text="Preço fixo declarado (obrigatório quando modo=PRECO_FIXO).",
                )),
                ("custo_manual_declarado", models.DecimalField(
                    blank=True, decimal_places=2, max_digits=12, null=True,
                    help_text="Custo manual declarado (obrigatório quando modo=MARGEM_ALVO).",
                )),
                ("custo_referencia_em", models.DateTimeField(
                    blank=True, null=True,
                    help_text="Data de referência do custo manual (staleness — TL-PRC-07).",
                )),
                ("margem_alvo_pct", models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True,
                    help_text="Margem alvo % (0..100) — MARGEM_ALVO e COST_PLUS.",
                )),
                ("margem_piso_pct", models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True,
                    help_text="Piso de margem mínima % — abaixo bloqueia (D-PRC-8).",
                )),
                ("vigencia_inicio", models.DateTimeField()),
                ("vigencia_fim", models.DateTimeField(
                    blank=True, null=True,
                    help_text="One-shot NULL→data (trigger 0003).",
                )),
                ("revogado_em", models.DateTimeField(blank=True, null=True)),
                ("motivo_revogacao", models.CharField(blank=True, default="", max_length=600)),
                ("criado_por", models.UUIDField(
                    help_text="Pseudônimo art. 12 LGPD; evento WORM leva só hash.",
                )),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("item", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="regras_preco",
                    to="produtos_pecas_servicos.itemcatalogo",
                )),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="regras_formacao_preco",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Regra de formação de preço",
                "verbose_name_plural": "Regras de formação de preço",
                "db_table": "regra_formacao_preco",
            },
        ),
        migrations.CreateModel(
            name="PerfilComposicaoPreco",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("componentes_esperados", models.JSONField(
                    default=list,
                    help_text="Lista de UUIDs de itens de catálogo esperados na cesta (D-PRC-2).",
                )),
                ("aviso_texto", models.CharField(
                    blank=True, default="", max_length=600,
                    help_text="Texto de aviso para ModoMontagem.FECHADO_COM_AVISO.",
                )),
                ("criado_por", models.UUIDField(help_text="Pseudônimo art. 12 LGPD.")),
                ("deletado_em", models.DateTimeField(
                    blank=True, null=True,
                    help_text="Soft-delete (ADR-0031 Padrão C — configuração mutável).",
                )),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("item_servico", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="perfis_composicao",
                    to="produtos_pecas_servicos.itemcatalogo",
                )),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="perfis_composicao_preco",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Perfil de composição de preço",
                "verbose_name_plural": "Perfis de composição de preço",
                "db_table": "perfil_composicao_preco",
            },
        ),
        migrations.CreateModel(
            name="FaixaAprovacaoDesconto",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("pct_de", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Limite inferior da faixa % (half-open [pct_de, pct_ate)).",
                )),
                ("pct_ate", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Limite superior da faixa % (half-open [pct_de, pct_ate)).",
                )),
                ("alcada", models.CharField(
                    choices=[("livre", "livre"), ("gerente", "gerente"), ("dono", "dono")],
                    max_length=10,
                    help_text="livre|gerente|dono — alçada exigida nesta faixa.",
                )),
                ("versao_n", models.IntegerField(
                    help_text="Versão densa do conjunto de faixas (incrementa em replace-all).",
                )),
                ("hash_conjunto", models.CharField(
                    max_length=200,
                    help_text="Hash canônico ADR-0029 do conjunto completo (fingerprint).",
                )),
                ("criado_por", models.UUIDField(help_text="Pseudônimo art. 12 LGPD.")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="faixas_aprovacao_desconto",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Faixa de aprovação de desconto",
                "verbose_name_plural": "Faixas de aprovação de desconto",
                "db_table": "faixa_aprovacao_desconto",
            },
        ),
        migrations.CreateModel(
            name="PedidoAprovacaoDesconto",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("contexto_tipo", models.CharField(
                    choices=[("orcamento", "orcamento"), ("os", "os"), ("avulso", "avulso")],
                    max_length=10,
                    help_text="orcamento|os|avulso — contexto de uso do pedido (D-PRC-14).",
                )),
                ("contexto_id", models.UUIDField(
                    blank=True, null=True,
                    help_text="ID do documento consumidor (NULL = AVULSO).",
                )),
                ("pct_solicitado", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Percentual de desconto solicitado (0..100).",
                )),
                ("cortesia", models.BooleanField(
                    default=False,
                    help_text="True quando pct_solicitado == 100 (alçada DONO obrigatória — D-PRC-13).",
                )),
                ("alcada_exigida", models.CharField(
                    choices=[("livre", "livre"), ("gerente", "gerente"), ("dono", "dono")],
                    max_length=10,
                    help_text="Alçada exigida para aprovação desta faixa.",
                )),
                ("fingerprint_calculo", models.CharField(
                    max_length=200,
                    help_text="Hash canônico ADR-0029 de (entradas+refs+pct) — binding.",
                )),
                ("estado", models.CharField(
                    choices=[("solicitado", "solicitado"), ("aprovado", "aprovado"), ("negado", "negado")],
                    default="solicitado",
                    max_length=12,
                    help_text="solicitado|aprovado|negado — one-shot via trigger.",
                )),
                ("solicitante_id", models.UUIDField(
                    help_text="Quem solicitou o desconto (pseudônimo art. 12 LGPD).",
                )),
                ("decisor_id", models.UUIDField(
                    blank=True, null=True,
                    help_text="Quem decidiu (DEVE ser != solicitante — CHECK).",
                )),
                ("snapshot_probatorio", models.TextField(
                    help_text="JSON canônico ADR-0029 das entradas do cálculo (replay).",
                )),
                ("justificativa_hash", models.CharField(
                    blank=True, default="", max_length=200,
                    help_text="Hash ADR-0029+HMAC-tenant do texto (texto cru em JustificativaDecisaoDesconto).",
                )),
                ("decidido_em", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="pedidos_aprovacao_desconto",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Pedido de aprovação de desconto",
                "verbose_name_plural": "Pedidos de aprovação de desconto",
                "db_table": "pedido_aprovacao_desconto",
            },
        ),
        migrations.CreateModel(
            name="JustificativaDecisaoDesconto",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("texto", models.TextField(
                    help_text="Texto cru da justificativa (AC-PRC-004-3).",
                )),
                ("deletado_em", models.DateTimeField(
                    blank=True, null=True,
                    help_text="Soft-delete ADR-0031 (TTL 5a — retenção comercial).",
                )),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="justificativa",
                    to="precificacao.pedidoaprovacaodesconto",
                )),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="justificativas_desconto",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Justificativa de decisão de desconto",
                "verbose_name_plural": "Justificativas de decisão de desconto",
                "db_table": "justificativa_decisao_desconto",
            },
        ),
        migrations.CreateModel(
            name="VinculoTabelaPrecoCliente",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tabela_id", models.UUIDField(
                    help_text="FK→tabela_preco.id (PPS); sem FK Django — cross-app (ADR-0007).",
                )),
                ("cliente_id", models.UUIDField(
                    help_text="Pseudônimo art. 12 LGPD; revogado quando Cliente.Anonimizado.",
                )),
                ("vigencia_inicio", models.DateTimeField()),
                ("vigencia_fim", models.DateTimeField(blank=True, null=True)),
                ("revogado_em", models.DateTimeField(blank=True, null=True)),
                ("motivo_revogacao", models.CharField(blank=True, default="", max_length=600)),
                ("criado_por", models.UUIDField(help_text="Pseudônimo art. 12 LGPD.")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="vinculos_tabela_preco_cliente",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Vínculo tabela de preço ↔ cliente",
                "verbose_name_plural": "Vínculos tabela de preço ↔ clientes",
                "db_table": "vinculo_tabela_preco_cliente",
            },
        ),
        migrations.CreateModel(
            name="ParametrosPrecificacaoTenant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("versao_n", models.IntegerField(
                    help_text="Versão densa por tenant (max+1 sob advisory lock 880_404).",
                )),
                ("custo_km", models.DecimalField(
                    decimal_places=4, max_digits=10,
                    help_text="Custo por km de deslocamento (R$/km — US-PRC-006).",
                )),
                ("taxa_parcelamento_mensal", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Taxa mensal de parcelamento %.",
                )),
                ("pct_comissao_prevista", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Comissão prevista % (PREVISTA — GATE-PRC-COMISSAO-REAL).",
                )),
                ("margem_alvo_default", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Margem alvo default %.",
                )),
                ("margem_piso_default", models.DecimalField(
                    decimal_places=2, max_digits=5,
                    help_text="Margem piso default %.",
                )),
                ("criado_por", models.UUIDField(help_text="Pseudônimo art. 12 LGPD.")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="parametros_precificacao",
                    to="tenant.tenant",
                )),
            ],
            options={
                "verbose_name": "Parâmetros de precificação do tenant",
                "verbose_name_plural": "Parâmetros de precificação dos tenants",
                "db_table": "parametros_precificacao_tenant",
            },
        ),
        # --- Índices ---
        migrations.AddIndex(
            model_name="regraformacaopreco",
            index=models.Index(fields=["tenant", "item"], name="ix_prc_regra_item"),
        ),
        migrations.AddIndex(
            model_name="perfilcomposicaopreco",
            index=models.Index(fields=["tenant", "item_servico"], name="ix_prc_perfil_item"),
        ),
        migrations.AddIndex(
            model_name="faixaaprovacaodesconto",
            index=models.Index(fields=["tenant", "versao_n"], name="ix_prc_faixa_versao"),
        ),
        migrations.AddIndex(
            model_name="pedidoaprovacaodesconto",
            index=models.Index(fields=["tenant", "estado"], name="ix_prc_pedido_estado"),
        ),
        migrations.AddIndex(
            model_name="vinculotabelaprecocliente",
            index=models.Index(fields=["tenant", "cliente_id"], name="ix_prc_vinculo_cliente"),
        ),
        migrations.AddIndex(
            model_name="parametrosprecificacaotenant",
            index=models.Index(fields=["tenant", "versao_n"], name="ix_prc_parametros_versao"),
        ),
        # --- UNIQUEs ---
        migrations.AddConstraint(
            model_name="regraformacaopreco",
            constraint=models.UniqueConstraint(
                fields=("tenant", "item", "versao_n"), name="uq_prc_regra_versao_n"
            ),
        ),
        migrations.AddConstraint(
            model_name="vinculotabelaprecocliente",
            constraint=models.UniqueConstraint(
                fields=("tenant", "cliente_id"),
                condition=models.Q(vigencia_fim__isnull=True, revogado_em__isnull=True),
                name="uq_prc_vinculo_cliente_vigente",
            ),
        ),
        migrations.AddConstraint(
            model_name="parametrosprecificacaotenant",
            constraint=models.UniqueConstraint(
                fields=("tenant", "versao_n"), name="uq_prc_parametros_versao_n"
            ),
        ),
        # --- CHECKs ---
        migrations.AddConstraint(
            model_name="pedidoaprovacaodesconto",
            constraint=models.CheckConstraint(
                check=~models.Q(decisor_id=models.F("solicitante_id"))
                | models.Q(decisor_id__isnull=True),
                name="ck_prc_pedido_decisor_independente",
            ),
        ),
    ]
