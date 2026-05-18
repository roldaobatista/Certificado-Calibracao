"""Modelo Cliente — Wave A · Marco 1 (modulo comercial/clientes).

Cliente eh PF (Pessoa Fisica, CPF) OU PJ (Pessoa Juridica, CNPJ alfanumerico).
A entidade armazena o documento normalizado (sem pontuacao, UPPER pra CNPJ).

Invariantes implementadas:
- INV-024 (dedup): UNIQUE(tenant_id, tipo_pessoa, documento) — impede que o
  mesmo CPF/CNPJ vire 2 clientes no mesmo tenant.
- INV-036 (CNPJ unico por tenant): caso particular de INV-024 quando tipo_pessoa = PJ.

VOs CNPJ/CPF (src/domain/shared/value_objects.py) sao usados no boundary
(serializer DRF) e em clean(). O banco armazena string normalizada.

ADR-0017 (CNPJ alfanumerico): documento aceita [A-Z0-9]{12}[0-9]{2} pra PJ
desde ja; vigencia oficial jul/2026.
"""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from src.domain.shared.value_objects import CNPJ, CPF
from src.infrastructure.tenant.models import Tenant


class TipoPessoa(models.TextChoices):
    PF = "PF", "Pessoa Fisica"
    PJ = "PJ", "Pessoa Juridica"


class ClienteAtivosManager(models.Manager):
    """Manager default — filtra soft-deleted (US-CLI-005 + R4 advogado)."""

    def get_queryset(self) -> models.QuerySet["Cliente"]:
        return super().get_queryset().filter(deletado_em__isnull=True)


class Cliente(models.Model):
    """Cliente PF ou PJ de um tenant.

    Modelo intencionalmente magrelo no Marco 1: nome + documento + email +
    telefone. Atributos comerciais (endereco, ramo, segmento) entram quando o
    proximo modulo (orcamentos/CRM) pedir — evitamos especular schema.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="clientes",
    )
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TipoPessoa.choices,
        help_text="PF (CPF) ou PJ (CNPJ alfanumerico IN RFB 2.229/2024).",
    )
    documento = models.CharField(
        max_length=14,
        help_text=(
            "CPF (11 digitos) OU CNPJ (12 alfanumericos + 2 DV digitos). "
            "Armazenado normalizado: sem pontuacao, UPPER para CNPJ."
        ),
    )
    nome = models.CharField(
        max_length=200,
        help_text="Nome completo (PF) ou razao social (PJ).",
    )
    nome_fantasia = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Formato livre nesta fase; normalizacao entra com modulo comunicacao.",
    )

    # =============================================================
    # Aceite LGPD (US-CLI-001 AC-2 + RAT-03)
    # Validado pelo subagente advogado-saas-regulado em 2026-05-18.
    # Snapshot legal completo (R2 advogado): em + versao + ip_hash + origem.
    # Retencao (R5 advogado): art. 16 II LGPD — acessorios a execucao do
    # contrato; mesma matriz do cliente principal; crypto-shredding Wave B.
    # =============================================================
    aceite_lgpd_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Datetime do aceite. Obrigatorio em PF. Pode ser NULL em PJ se "
            "aceite_lgpd_dispensa_motivo informado (R3 advogado — PJ sem PF associada)."
        ),
    )
    aceite_lgpd_versao = models.CharField(
        max_length=40,
        blank=True,
        help_text=(
            "Snapshot da versao vigente do texto no momento do aceite. "
            "Ver src/infrastructure/clientes/lgpd.py TEXTOS_HISTORICOS pra recuperar "
            "o texto exato que o titular aceitou. Imutavel apos gravacao."
        ),
    )
    aceite_lgpd_ip_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text=(
            "SHA-256 do IP do request (LGPD art. 6 V — qualidade + INV-013 "
            "rastreabilidade). Vazio se origem=balcao (titular nao presente)."
        ),
    )
    aceite_lgpd_origem = models.CharField(
        max_length=20,
        blank=True,
        help_text=(
            "balcao | portal | importacao | api_terceiro. Ver lgpd.py ORIGENS_VALIDAS."
        ),
    )
    aceite_lgpd_dispensa_motivo = models.CharField(
        max_length=60,
        blank=True,
        help_text=(
            "Preenchido em PJ sem PF associada (R3 advogado). Valor padrao: "
            "'pj_sem_pf_associada'. Ver lgpd.py DISPENSAS_VALIDAS."
        ),
    )

    # =============================================================
    # Soft-delete (US-CLI-005). R3 advogado: NAO eh direito ao esquecimento
    # (LGPD art. 18 VI — esse vai pra crypto-shredding em portal Wave B).
    # Soft-delete eh correcao de qualidade (art. 6 V) + retencao (art. 16 II +
    # ISO 17025 cl. 8.4 ~25 anos quando ha certificado emitido pro cliente).
    # =============================================================
    deletado_em = models.DateTimeField(null=True, blank=True, db_index=True)
    deletado_por_usuario_id = models.UUIDField(null=True, blank=True)
    deletado_motivo_categoria = models.CharField(
        max_length=40,
        blank=True,
        help_text="Enum MotivoMesclagem (ver lgpd.py / mesclagem.py).",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Manager default filtra ativos; all_objects expoe deletados (auditoria).
    objects = ClienteAtivosManager()
    all_objects = models.Manager()

    class Meta:
        app_label = "clientes"
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]
        # UNIQUE INDEX parcial criado por migration SQL (T-CLI-009b R4 advogado):
        #   CREATE UNIQUE INDEX uq_cliente_doc_ativo ON clientes
        #     (tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL;
        # Substitui UniqueConstraint Django, que nao suporta WHERE parcial.
        indexes = [
            models.Index(fields=["tenant", "documento"], name="ix_cliente_tenant_doc"),
            models.Index(fields=["tenant", "nome"], name="ix_cliente_tenant_nome"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.tipo_pessoa} {self.documento})"

    @property
    def bloqueado(self) -> bool:
        """True se ha 1 ClienteBloqueio ativo (US-CLI-004 — TL1)."""
        return ClienteBloqueio.objects.filter(
            cliente_id=self.id, desbloqueado_em__isnull=True
        ).exists()

    def clean(self) -> None:
        """Validacao no boundary — chamado por full_clean()."""
        from .lgpd import DISPENSAS_VALIDAS, ORIGENS_VALIDAS

        super().clean()
        # Documento
        try:
            if self.tipo_pessoa == TipoPessoa.PF:
                CPF(self.documento)
            elif self.tipo_pessoa == TipoPessoa.PJ:
                CNPJ(self.documento)
            else:
                raise ValidationError({"tipo_pessoa": "Tipo invalido"})
        except ValueError as e:
            raise ValidationError({"documento": str(e)}) from e

        # Aceite LGPD
        if self.tipo_pessoa == TipoPessoa.PF and self.aceite_lgpd_em is None:
            raise ValidationError(
                {"aceite_lgpd_em": "PF exige aceite LGPD (data + versao + origem)."}
            )
        if (
            self.tipo_pessoa == TipoPessoa.PJ
            and self.aceite_lgpd_em is None
            and not self.aceite_lgpd_dispensa_motivo
        ):
            raise ValidationError(
                {
                    "aceite_lgpd_dispensa_motivo": (
                        "PJ sem aceite LGPD exige motivo de dispensa "
                        "(ex: 'pj_sem_pf_associada' — R3 advogado)."
                    )
                }
            )
        if self.aceite_lgpd_em is not None and self.aceite_lgpd_origem:
            if self.aceite_lgpd_origem not in ORIGENS_VALIDAS:
                raise ValidationError(
                    {"aceite_lgpd_origem": f"Origem invalida; use {ORIGENS_VALIDAS}"}
                )
        if (
            self.aceite_lgpd_dispensa_motivo
            and self.aceite_lgpd_dispensa_motivo not in DISPENSAS_VALIDAS
        ):
            raise ValidationError(
                {"aceite_lgpd_dispensa_motivo": f"Use {DISPENSAS_VALIDAS}"}
            )


class ClienteBloqueio(models.Model):
    """Historico 1:N de bloqueios comerciais do cliente (US-CLI-004 — TL1).

    Mantém histórico de bloqueios + desbloqueios. UNIQUE INDEX parcial em
    `(cliente_id) WHERE desbloqueado_em IS NULL` garante que apenas 1 bloqueio
    pode estar ativo por cliente (migration 0008).

    R1 advogado: `justificativa_bruta` fica APENAS aqui (tenant operacional,
    crypto-shredding Wave B); audit grava só hash. Confidencialidade reforçada
    (INV-013 estendida).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="bloqueios"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="cliente_bloqueios"
    )
    motivo_categoria = models.CharField(
        max_length=40,
        help_text=(
            "Enum (ver bloqueio.py): manual_inadimplencia, manual_quebra_confianca, "
            "manual_solicitacao_juridico, manual_outro, automatico_inadimplencia_90d."
        ),
    )
    motivo_observacao = models.CharField(
        max_length=200,
        blank=True,
        help_text="Texto livre limitado; rejeita CPF/CNPJ/email/telefone (R2 advogado).",
    )
    justificativa_bruta = models.TextField(
        help_text=(
            "Texto da justificativa (>=30 chars). Confidencial — INV-013 estendida. "
            "Audit grava apenas SHA-256 (R1 advogado)."
        ),
    )
    causation_type = models.CharField(
        max_length=40,
        blank=True,
        help_text=(
            "Enum (TL4): titulo_vencido | importacao_batch | politica_inadimplencia | "
            "manual_decisao_admin. CHECK constraint na migration."
        ),
    )
    causation_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK opcional para entidade que originou (ex: TituloVencido em Wave A).",
    )
    confirmacao_comunicacao_previa = models.BooleanField(
        default=False,
        help_text=(
            "R3 advogado (CDC art. 6 III/IV + Lei 14.181/2021): bloqueio manual "
            "exige checkbox 'confirmo que comuniquei o cliente previamente'."
        ),
    )
    bloqueado_em = models.DateTimeField(auto_now_add=True)
    bloqueado_por_usuario_id = models.UUIDField(null=True, blank=True)
    desbloqueado_em = models.DateTimeField(null=True, blank=True, db_index=True)
    desbloqueado_por_usuario_id = models.UUIDField(null=True, blank=True)
    desbloqueado_motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = "clientes"
        db_table = "cliente_bloqueios"
        verbose_name = "Bloqueio de cliente"
        verbose_name_plural = "Bloqueios de cliente"
        ordering = ["-bloqueado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "cliente"], name="ix_cli_bloq_tenant_cli"
            ),
            models.Index(
                fields=["tenant", "bloqueado_em"], name="ix_cli_bloq_tenant_data"
            ),
        ]

    def __str__(self) -> str:
        status_ = "ATIVO" if self.desbloqueado_em is None else "encerrado"
        return f"Bloqueio {self.id} {status_} ({self.motivo_categoria})"
