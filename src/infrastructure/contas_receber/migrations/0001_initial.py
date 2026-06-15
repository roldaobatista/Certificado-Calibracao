# T-CR-022 — frente contas-receber schema inicial (4 tabelas achatadas).
# titulo_receber + parcela_titulo + pagamento_titulo + override_bloqueio.
#
# UNIQUE de negócio:
#   uq_cr_titulo_os_ativo: (tenant_id, os_id_origem) WHERE estado != cancelado
#   (INV-CR-OS-TITULO-UNICO / R6 — 1 OS → 1 título ativo)
#   uq_cr_parcela_titulo_numero: (titulo_id, numero)
#
# CHECK:
#   chk_cr_titulo_pix_recorrente_convenio:
#     meio != pix_recorrente OR convenio_pix_id != '' (INV-FIN-GW-002)
#
# RLS policies = migration-irmã 0002_rls_policies (ADR-0002 §6 pattern v2).
# Triggers WORM Padrão B (block-delete + campos probatórios imutáveis;
# Pagamento/OverrideBloqueio INSERT-only; perfil fallback) = 0003_triggers_worm.
# GRANT app_user = 0004. Seed authz = 0005.
#
# rls-policy: external 0002_rls_policies

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenant", "0012_aplicar_evento_cgcre_vigencia"),
    ]

    operations = [
        migrations.CreateModel(
            name="Titulo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "cliente_atual_id",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text="FK lógica SET_NULL ao cliente (PII direta; zerada em anonimização).",
                    ),
                ),
                (
                    "cliente_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do cliente — pseudônimo na trilha (ADR-0032). Imutável, NOT NULL.",
                    ),
                ),
                (
                    "cliente_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ex: v1, v2 — ADR-0064 / rotação anual).",
                    ),
                ),
                (
                    "valor_original",
                    models.BigIntegerField(
                        help_text="Valor original do título em centavos (Dinheiro). Imutável pos-INSERT.",
                    ),
                ),
                (
                    "data_emissao",
                    models.DateField(help_text="Data de emissão do título. Imutável."),
                ),
                (
                    "data_vencimento",
                    models.DateField(help_text="Data de vencimento original. Imutável."),
                ),
                (
                    "data_baixa",
                    models.DateField(
                        blank=True,
                        null=True,
                        help_text="One-shot: NULL→data quando pago. Trigger 0003 bloqueia sobrescrita.",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("emitido", "emitido"),
                            ("pago", "pago"),
                            ("parcialmente_pago", "parcialmente_pago"),
                            ("vencido", "vencido"),
                            ("cancelado", "cancelado"),
                        ],
                        help_text="Estado do título (D-CR-3). Mutável por transição válida.",
                    ),
                ),
                (
                    "meio",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("boleto", "boleto"),
                            ("pix", "pix"),
                            ("pix_recorrente", "pix_recorrente"),
                            ("cartao", "cartao"),
                            ("cartao_recorrente", "cartao_recorrente"),
                        ],
                        help_text="Canal de cobrança (D-CR-7).",
                    ),
                ),
                (
                    "categoria_receita",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("CALIBRACAO_RBC", "CALIBRACAO_RBC"),
                            ("CALIBRACAO_NAO_RBC", "CALIBRACAO_NAO_RBC"),
                            ("CALIBRACAO_BASICA", "CALIBRACAO_BASICA"),
                            ("MANUTENCAO_CORRETIVA", "MANUTENCAO_CORRETIVA"),
                            ("MANUTENCAO_PREVENTIVA", "MANUTENCAO_PREVENTIVA"),
                            ("PECA_REVENDA", "PECA_REVENDA"),
                            ("DESLOCAMENTO", "DESLOCAMENTO"),
                            ("OUTROS", "OUTROS"),
                        ],
                        help_text="Categoria da receita — perfil-aware (D-CR-5 / INV-FIN-PERFIL-001). Imutável.",
                    ),
                ),
                (
                    "perfil_no_evento",
                    models.CharField(
                        max_length=1,
                        help_text=(
                            "Snapshot CHAR(1) do perfil regulatório do tenant na emissão (ADR-0067 §3 / D-CR-6). "
                            "Imutável. Trigger BEFORE INSERT preenche via COALESCE se NULL (R4)."
                        ),
                    ),
                ),
                (
                    "origem",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("os", "os"),
                            ("nfse", "nfse"),
                            ("contrato", "contrato"),
                            ("manual", "manual"),
                        ],
                        help_text="Fato gerador do título (D-CR-12). Imutável.",
                    ),
                ),
                (
                    "os_id_origem",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text="OS que originou este título (gatilho canônico — D-CR-12). Imutável.",
                    ),
                ),
                (
                    "nfse_id_origem",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text="NF-e de origem (GATE-CR-NFSE — Wave B). Imutável.",
                    ),
                ),
                (
                    "gateway_externo_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=120,
                        help_text="ID no gateway (NOT NULL ⟺ cobrança emitida — derivado, não estado). Mutável.",
                    ),
                ),
                (
                    "convenio_pix_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=120,
                        help_text="Convênio PIX recorrente (NOT NULL obrigatório se meio=pix_recorrente — INV-FIN-GW-002).",
                    ),
                ),
                (
                    "linha_digitavel",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        help_text="Linha digitável do boleto. Mutável.",
                    ),
                ),
                (
                    "qr_code",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="QR code do PIX (payload). Mutável.",
                    ),
                ),
                (
                    "tx_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=120,
                        help_text="TxID do PIX direto. Mutável.",
                    ),
                ),
                (
                    "desconto_pontualidade_pct",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        help_text="Percentual de desconto por pontualidade (bps 0-10000). Imutável.",
                    ),
                ),
                (
                    "numero_sequencial_tenant",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        help_text="Numeração GAP_LESS via SerieDocumento (D-CR-18). NULL = não exigida.",
                    ),
                ),
                (
                    "cancelado_em",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        help_text="One-shot: NULL→datetime quando cancelado. Trigger 0003 bloqueia sobrescrita.",
                    ),
                ),
                (
                    "revision",
                    models.IntegerField(
                        default=0,
                        help_text="Contador de transições (observabilidade / OCC). Bumpa por F('revision')+1.",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="titulos_receber",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Título a Receber",
                "verbose_name_plural": "Títulos a Receber",
                "db_table": "titulo_receber",
                "ordering": ["-criado_em"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("tenant", "os_id_origem"),
                        condition=~models.Q(estado="cancelado"),
                        name="uq_cr_titulo_os_ativo",
                    ),
                    models.CheckConstraint(
                        condition=(
                            ~models.Q(meio="pix_recorrente") | ~models.Q(convenio_pix_id="")
                        ),
                        name="chk_cr_titulo_pix_recorrente_convenio",
                    ),
                ],
                "indexes": [
                    models.Index(fields=["tenant", "estado"], name="cr_titulo_tenant_estado_idx"),
                    models.Index(fields=["tenant", "os_id_origem"], name="cr_titulo_tenant_os_idx"),
                    models.Index(
                        fields=["tenant", "cliente_atual_id"], name="cr_titulo_tenant_cliente_idx"
                    ),
                    models.Index(
                        fields=["tenant", "data_vencimento"], name="cr_titulo_vencimento_idx"
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Parcela",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("numero", models.IntegerField(help_text="Número 1-based da parcela.")),
                ("valor", models.BigIntegerField(help_text="Valor da parcela em centavos.")),
                ("vencimento", models.DateField()),
                (
                    "status",
                    models.CharField(
                        default="aberta",
                        max_length=20,
                        help_text="aberta | paga | cancelada.",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "titulo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="parcelas",
                        to="contas_receber.titulo",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="parcelas_titulo",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Parcela de Título",
                "verbose_name_plural": "Parcelas de Título",
                "db_table": "parcela_titulo",
                "ordering": ["numero"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("titulo", "numero"),
                        name="uq_cr_parcela_titulo_numero",
                    ),
                ],
                "indexes": [
                    models.Index(fields=["tenant", "titulo"], name="cr_parcela_tenant_titulo_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Pagamento",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("valor", models.BigIntegerField(help_text="Valor efetivamente pago (centavos).")),
                ("data", models.DateField(help_text="Data do pagamento.")),
                (
                    "origem",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("webhook_gateway", "webhook_gateway"),
                            ("manual", "manual"),
                            ("pix_direto", "pix_direto"),
                        ],
                        help_text="Como o pagamento foi confirmado (D-CR-8).",
                    ),
                ),
                (
                    "valor_atualizado_snapshot_em_pagamento",
                    models.BigIntegerField(
                        help_text="Snapshot do valor atualizado (com juros/multa) na data da baixa (M-FIN-002).",
                    ),
                ),
                (
                    "gateway_event_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=120,
                        help_text="ID do evento de webhook do gateway (idempotência — INV-FIN-GW-001).",
                    ),
                ),
                (
                    "comprovante_url",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text="URL do comprovante (baixa manual ou PIX). Sem PII do pagador (D-CR-19).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "titulo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagamentos",
                        to="contas_receber.titulo",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pagamentos_titulo",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pagamento de Título",
                "verbose_name_plural": "Pagamentos de Título",
                "db_table": "pagamento_titulo",
                "ordering": ["criado_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "titulo"], name="cr_pagamento_tenant_titulo_idx"
                    ),
                    models.Index(fields=["gateway_event_id"], name="cr_pagamento_gw_event_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="OverrideBloqueio",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "cliente_id",
                    models.UUIDField(
                        help_text="ID concreto do cliente no momento (não hash — OverrideBloqueio é ato gerencial).",
                    ),
                ),
                (
                    "novo_prazo_max_dias",
                    models.IntegerField(
                        help_text="Novo prazo máximo de bloqueio em dias (≤90 — AC-CR-010-5).",
                    ),
                ),
                (
                    "justificativa",
                    models.TextField(
                        help_text="Justificativa textual ≥100 chars + filtro anti-PII (INV-CR-OVERRIDE-ANTI-PII).",
                    ),
                ),
                (
                    "a3_signature_id",
                    models.CharField(
                        max_length=200,
                        help_text="Referência da assinatura A3 (stub Wave A — verificação real = GATE-CR-A3).",
                    ),
                ),
                (
                    "usuario_id",
                    models.UUIDField(
                        help_text="ID do usuário que executou o override (papel gerente).",
                    ),
                ),
                (
                    "perfil_no_evento",
                    models.CharField(
                        max_length=1,
                        help_text="Snapshot CHAR(1) do perfil do tenant no momento do override (D-CR-6).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "titulo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="overrides_bloqueio",
                        to="contas_receber.titulo",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="overrides_bloqueio",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Override de Bloqueio",
                "verbose_name_plural": "Overrides de Bloqueio",
                "db_table": "override_bloqueio",
                "ordering": ["criado_em"],
                "indexes": [
                    models.Index(fields=["tenant", "titulo"], name="cr_override_tenant_titulo_idx"),
                    models.Index(
                        fields=["tenant", "criado_em"], name="cr_override_tenant_criado_idx"
                    ),
                ],
            },
        ),
    ]
