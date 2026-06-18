# T-CT-022 — frente caixa_tecnico schema inicial (6 tabelas achatadas).
# caixa_tecnico + adiantamento_caixa + despesa_caixa +
# prestacao_contas_caixa + politica_caixa + consentimento_gps_colaborador.
#
# UNIQUE de negócio:
#   uq_ct_caixa_tecnico_hash: (tenant_id, tecnico_referencia_hash)
#   (INV-CT-CAIXA-UNICO — 1 caixa por técnico por tenant)
#
# Índices relevantes:
#   (tenant_id, tecnico_referencia_hash) em caixa_tecnico
#   (tenant_id, data) em despesa_caixa
#
# RLS policies = migration-irmã 0002_rls_policies (ADR-0002 §6 pattern v2).
# Triggers WORM = 0003_triggers_worm.
# Constraints parciais = 0004_constraints.
# GRANT app_user = 0005. Seed authz = 0006.
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
            name="CaixaTecnico",
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
                    "tecnico_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do técnico — pseudônimo na trilha (ADR-0032). Imutável, NOT NULL.",
                    ),
                ),
                (
                    "tecnico_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ex: v1, v2 — ADR-0064 / rotação anual).",
                    ),
                ),
                (
                    "desligado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text=(
                            "Preenchido pelo consumer colaborador.desligado (D-CT-11). "
                            "Fail-closed: novos lançamentos bloqueados quando presente."
                        ),
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "revision",
                    models.IntegerField(
                        default=0,
                        help_text="Contador de transições (OCC). Bumpa por F('revision')+1.",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="caixas_tecnico",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Caixa do Técnico",
                "verbose_name_plural": "Caixas de Técnicos",
                "db_table": "caixa_tecnico",
                "ordering": ["-criado_em"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("tenant", "tecnico_referencia_hash"),
                        name="uq_ct_caixa_tecnico_hash",
                    ),
                ],
                "indexes": [
                    models.Index(
                        fields=["tenant", "tecnico_referencia_hash"],
                        name="ct_caixa_tenant_hash_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AdiantamentoCaixa",
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
                    "tecnico_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do técnico — cópia desnormalizada para trilha (ADR-0032).",
                    ),
                ),
                (
                    "tecnico_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ADR-0064).",
                    ),
                ),
                (
                    "valor",
                    models.BigIntegerField(
                        help_text="Valor do adiantamento em centavos (Dinheiro BRL).",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("solicitado", "solicitado"),
                            ("aprovado", "aprovado"),
                            ("entregue", "entregue"),
                            ("recusado", "recusado"),
                            ("cancelado", "cancelado"),
                        ],
                        help_text="Estado da máquina de estados (D-CT-7).",
                    ),
                ),
                (
                    "meio",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("pix", "pix"),
                            ("transferencia", "transferencia"),
                            ("dinheiro", "dinheiro"),
                        ],
                        help_text="Meio de entrega do adiantamento (US-CT-001).",
                    ),
                ),
                (
                    "solicitado_em",
                    models.DateTimeField(
                        help_text="Momento da solicitação do adiantamento.",
                    ),
                ),
                (
                    "aprovado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da aprovação.",
                    ),
                ),
                (
                    "entregue_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da entrega (estado terminal).",
                    ),
                ),
                (
                    "recusado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da recusa (terminal).",
                    ),
                ),
                (
                    "cancelado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento do cancelamento (terminal).",
                    ),
                ),
                (
                    "motivo_recusa",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Motivo da recusa.",
                    ),
                ),
                (
                    "justificativa",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Justificativa do solicitante.",
                    ),
                ),
                (
                    "aprovado_por_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text="ID concreto do usuário que aprovou.",
                    ),
                ),
                (
                    "entregue_por_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text="ID concreto do usuário que confirmou a entrega.",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "revision",
                    models.IntegerField(default=0, help_text="Contador de transições (OCC)."),
                ),
                (
                    "caixa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="adiantamentos",
                        to="caixa_tecnico.caixatecnico",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="adiantamentos_caixa",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Adiantamento de Caixa",
                "verbose_name_plural": "Adiantamentos de Caixa",
                "db_table": "adiantamento_caixa",
                "ordering": ["-solicitado_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "caixa", "estado"],
                        name="ct_adian_caixa_estado_idx",
                    ),
                    models.Index(
                        fields=["tenant", "solicitado_em"],
                        name="ct_adian_solicitado_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DespesaCaixa",
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
                    "tecnico_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do técnico — trilha imutável (ADR-0032).",
                    ),
                ),
                (
                    "tecnico_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ADR-0064).",
                    ),
                ),
                (
                    "categoria",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("combustivel", "combustivel"),
                            ("alimentacao", "alimentacao"),
                            ("pedagio", "pedagio"),
                            ("hospedagem", "hospedagem"),
                            ("peca", "peca"),
                            ("deslocamento", "deslocamento"),
                        ],
                        help_text="Categoria da despesa (D-CT-9).",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("normal", "normal"),
                            ("estorno", "estorno"),
                        ],
                        default="normal",
                        help_text="normal | estorno (D-CT-3).",
                    ),
                ),
                (
                    "valor",
                    models.BigIntegerField(
                        help_text="Valor em centavos (Dinheiro BRL).",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        max_length=10,
                        choices=[
                            ("pendente", "pendente"),
                            ("validada", "validada"),
                            ("rejeitada", "rejeitada"),
                            ("cancelada", "cancelada"),
                        ],
                        default="pendente",
                        help_text="Estado da máquina de estados (D-CT-3).",
                    ),
                ),
                (
                    "foto_hash",
                    models.CharField(
                        max_length=80,
                        help_text=(
                            "HMAC-SHA256 dos bytes pós-EXIF-strip (D-CT-4/ADR-0064). "
                            "NOT NULL — foto obrigatória (INV-CT-FOTO-001)."
                        ),
                    ),
                ),
                (
                    "foto_url",
                    models.URLField(
                        max_length=500,
                        help_text="URL relativa da foto content-addressed (D-CT-4).",
                    ),
                ),
                (
                    "data",
                    models.DateField(
                        help_text="Data da despesa (informada pelo técnico).",
                    ),
                ),
                (
                    "descricao",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Descrição livre da despesa.",
                    ),
                ),
                (
                    "km_percorridos",
                    models.DecimalField(
                        max_digits=10,
                        decimal_places=2,
                        null=True,
                        blank=True,
                        help_text="Km rodados (obrigatório quando categoria=deslocamento).",
                    ),
                ),
                (
                    "gps_lat",
                    models.DecimalField(
                        max_digits=10,
                        decimal_places=7,
                        null=True,
                        blank=True,
                        help_text="Latitude GPS (opt-in server-side — D-CT-6). NULL sem consentimento.",
                    ),
                ),
                (
                    "gps_lng",
                    models.DecimalField(
                        max_digits=10,
                        decimal_places=7,
                        null=True,
                        blank=True,
                        help_text="Longitude GPS (opt-in server-side — D-CT-6). NULL sem consentimento.",
                    ),
                ),
                (
                    "gps_referencia_pii",
                    models.CharField(
                        max_length=80,
                        blank=True,
                        default="",
                        help_text="Hash PII da referência GPS (retenção curta — D-CT-6/ADR-0021).",
                    ),
                ),
                (
                    "os_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text="FK lógica à OS vinculada (rastro histórico — D-CT-11).",
                    ),
                ),
                (
                    "client_offline_id",
                    models.CharField(
                        max_length=120,
                        blank=True,
                        default="",
                        help_text="ID gerado pelo cliente offline (idempotência dupla-camada — D-CT-5).",
                    ),
                ),
                (
                    "despesa_origem_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text="FK lógica à despesa original (tipo=estorno — D-CT-3).",
                    ),
                ),
                (
                    "acima_limite",
                    models.BooleanField(
                        default=False,
                        help_text="Flag calculada: despesa acima do limite configurado (D-CT-9).",
                    ),
                ),
                (
                    "motivo_rejeicao",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Motivo da rejeição.",
                    ),
                ),
                (
                    "rejeitado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da rejeição.",
                    ),
                ),
                (
                    "validado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da validação (WORM — trigger bloqueia UPDATE pós-validada).",
                    ),
                ),
                (
                    "cancelado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento do cancelamento (terminal).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "revision",
                    models.IntegerField(default=0, help_text="Contador de transições (OCC)."),
                ),
                (
                    "caixa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="despesas",
                        to="caixa_tecnico.caixatecnico",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="despesas_caixa",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Despesa de Caixa",
                "verbose_name_plural": "Despesas de Caixa",
                "db_table": "despesa_caixa",
                "ordering": ["-data", "-criado_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "caixa", "estado"],
                        name="ct_desp_caixa_estado_idx",
                    ),
                    models.Index(
                        fields=["tenant", "data"],
                        name="ct_desp_tenant_data_idx",
                    ),
                    models.Index(
                        fields=["tenant", "os_id"],
                        name="ct_desp_tenant_os_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="PrestacaoContasCaixa",
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
                    "tecnico_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do técnico — cópia imutável na trilha (ADR-0032).",
                    ),
                ),
                (
                    "tecnico_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ADR-0064).",
                    ),
                ),
                (
                    "periodo_de",
                    models.DateField(
                        help_text="Início do período coberto (Periodo.de achatado).",
                    ),
                ),
                (
                    "periodo_ate",
                    models.DateField(
                        help_text="Fim do período coberto (Periodo.ate achatado).",
                    ),
                ),
                (
                    "total_adiantado",
                    models.BigIntegerField(
                        help_text="Total de adiantamentos entregues no período (centavos). WORM pós-fechamento.",
                    ),
                ),
                (
                    "total_despesas_validadas",
                    models.BigIntegerField(
                        help_text="Total de despesas validadas no período (centavos). WORM pós-fechamento.",
                    ),
                ),
                (
                    "saldo_final",
                    models.BigIntegerField(
                        help_text="Saldo final em centavos (D-CT-8). WORM pós-fechamento.",
                    ),
                ),
                (
                    "direcao",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("tecnico_deve", "tecnico_deve"),
                            ("tenant_deve", "tenant_deve"),
                            ("quitado", "quitado"),
                        ],
                        help_text="Direção do saldo (D-CT-8). WORM pós-fechamento.",
                    ),
                ),
                (
                    "fechada_em",
                    models.DateTimeField(
                        help_text="Momento do fechamento (WORM — trigger bloqueia sobrescrita).",
                    ),
                ),
                (
                    "pdf_url",
                    models.URLField(
                        max_length=500,
                        blank=True,
                        default="",
                        help_text="URL do PDF gerado (Fatia 3c — WeasyPrint).",
                    ),
                ),
                (
                    "observacoes",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Observações livres do gestor.",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "caixa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prestacoes_contas",
                        to="caixa_tecnico.caixatecnico",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prestacoes_contas_caixa",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prestação de Contas de Caixa",
                "verbose_name_plural": "Prestações de Contas de Caixa",
                "db_table": "prestacao_contas_caixa",
                "ordering": ["-fechada_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "caixa"],
                        name="ct_prest_tenant_caixa_idx",
                    ),
                    models.Index(
                        fields=["tenant", "periodo_de"],
                        name="ct_prest_tenant_periodo_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="PoliticaCaixa",
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
                    "tarifa_km",
                    models.BigIntegerField(
                        null=True,
                        blank=True,
                        help_text="Tarifa por km em centavos (D-CT-9). NULL = km desabilitado.",
                    ),
                ),
                (
                    "prazo_prestacao_dias",
                    models.IntegerField(
                        default=30,
                        help_text="Prazo máximo para fechar prestação (dias). Default 30.",
                    ),
                ),
                (
                    "exige_gps",
                    models.BooleanField(
                        default=False,
                        help_text="Tenant exige GPS nas despesas de deslocamento (D-CT-6/D-CT-9).",
                    ),
                ),
                (
                    "limite_por_categoria",
                    models.JSONField(
                        null=True,
                        blank=True,
                        help_text="Mapa {categoria: centavos} de limite por categoria (D-CT-9).",
                    ),
                ),
                (
                    "alcada_aprovacao",
                    models.BigIntegerField(
                        null=True,
                        blank=True,
                        help_text="Centavos; adiantamentos acima exigem aprovação (D-CT-7/D-CT-9).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="politicas_caixa",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Política de Caixa",
                "verbose_name_plural": "Políticas de Caixa",
                "db_table": "politica_caixa",
                "ordering": ["-criado_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant"],
                        name="ct_pol_tenant_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ConsentimentoGpsColaborador",
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
                    "colaborador_referencia_hash",
                    models.CharField(
                        max_length=80,
                        help_text="HMAC do colaborador — pseudônimo na trilha (ADR-0032). NOT NULL.",
                    ),
                ),
                (
                    "colaborador_key_id",
                    models.CharField(
                        max_length=10,
                        help_text="Versão da chave HMAC (ADR-0064).",
                    ),
                ),
                (
                    "vigencia_inicio",
                    models.DateTimeField(
                        help_text="Início da vigência do consentimento GPS (ADR-0030).",
                    ),
                ),
                (
                    "revogado_em",
                    models.DateTimeField(
                        null=True,
                        blank=True,
                        help_text="Momento da revogação (one-shot — ADR-0030). NULL = vigente.",
                    ),
                ),
                (
                    "motivo_revogacao",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Motivo da revogação (LGPD — recomendado ≥10 chars).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="consentimentos_gps_colaborador",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consentimento GPS do Colaborador",
                "verbose_name_plural": "Consentimentos GPS dos Colaboradores",
                "db_table": "consentimento_gps_colaborador",
                "ordering": ["-vigencia_inicio"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "colaborador_referencia_hash", "vigencia_inicio"],
                        name="ct_cgps_tenant_col_vig_idx",
                    ),
                ],
            },
        ),
    ]
