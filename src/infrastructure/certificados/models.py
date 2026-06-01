# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Modelos da tabela ACHATADA `certificados` (ADR-0078).

A tabela física + o trigger cross-app INV-025 (`equipamento_imutabilidade_pos_cert`)
vivem AQUI (app `certificados`, NÃO-aninhado) porque o trigger faz
`SELECT ... FROM certificados WHERE status='emitido'` com nome de tabela + literal
hard-coded — mover `db_table`/app/valor quebraria INV-025 silenciosamente. A LÓGICA
(reconciliação, use cases, mappers, repositories) vive no path aninhado
`metrologia/certificados/` (ADR-0072), importando estes models.

M8 Wave A (T-CER-020/021) estende o stub Marco 2 de forma ESTRITAMENTE ADITIVA:
- `Certificado`: + colunas da emissão metrológica (numeração, perfil, faixa,
  snapshots, reconciliacao_hash) + choice `substituida` (reemissão US-CER-004).
- `PontoReconciliado` (1:N WORM): uma linha por ponto reportado.
- `AnaliseReconciliacaoCert` (WORM): decisão do RT por ponto, ligada a `calibracao_id`.

Choices derivados 1:1 dos enums de domínio (anti-drift). Domain NÃO importa Django
(ADR-0007 — mappers em `metrologia/certificados/mappers.py` convertem Model<->Snapshot).
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from django.db import models

from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    TipoAcreditacao,
)
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.tenant.models import Tenant


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class StatusCertificado(models.TextChoices):
    """Estados do certificado. Marco 2 usou 3; M8 estende com `substituida`
    (reemissão versionada — US-CER-004). ADITIVO: o trigger INV-025 só filtra
    `'emitido'`, então a nova choice não toca o contrato cross-app."""

    RASCUNHO = "rascunho", "Rascunho (sem efeito legal)"
    EMITIDO = "emitido", "Emitido (vigente — bloqueia mutacao INV-025)"
    SUBSTITUIDA = "substituida", "Substituída (reemissão versionada US-CER-004)"
    REVOGADO = "revogado", "Revogado (substituido ou erro)"


class CertificadoVigentesManager(models.Manager["Certificado"]):
    """Default manager — filtra so EMITIDO + nao revogado.

    `INV-025` usa esta visao pra detectar mutacao bloqueada. Queries que precisam
    ver substituida/revogado usam `all_objects` (TL-05 — `tem_emitido` explícito
    nos repositories, não confiar no default manager pra distinguir).
    """

    def get_queryset(self) -> models.QuerySet[Certificado]:
        return (
            super()
            .get_queryset()
            .filter(status=StatusCertificado.EMITIDO, revogado_em__isnull=True)
        )


class Certificado(models.Model):
    """Certificado de calibração — tabela achatada (ADR-0078).

    Marco 2: stub p/ destravar INV-025. M8: emissão metrológica lógica (números
    definitivos + snapshot congelado WORM + reconciliação ponto-a-ponto). PDF/A3
    plugam depois sobre o snapshot imutável (Wave A — `DocumentoCertificado`).
    Campos M8 são `null=True`/default (aditivo seguro sobre o stub); a aplicação
    (use case `emitir_certificado`) SEMPRE os preenche na emissão — a NOT-NULL
    efetiva é garantida no use case + INV-CER-SNAPSHOT-PERFIL-001.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusCertificado.choices,
        default=StatusCertificado.RASCUNHO,
    )
    emitido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Emissão metrológica (números definitivos + snapshot). A entrega "
            "normativa cl. 7.8 (RBC) é na assinatura A3 (Wave A)."
        ),
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Quando o cert foi invalidado. INV-025 deixa de bloquear "
            "mutacao no equipamento quando todos os certs ficam revogados."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    # --- M8 Wave A (T-CER-020) — emissão metrológica (aditivo) ---------------
    calibracao_id = models.UUIDField(
        null=True, blank=True, db_index=True,
        help_text="Calibração APROVADA de origem (M4). UUIDField evita FK cross-app.",
    )
    numero_interno = models.BigIntegerField(
        null=True, blank=True,
        help_text="Sequence PG `certificado_numero_seq` (buracos OK — INV-CER-NUM-002).",
    )
    numero_certificado = models.CharField(
        max_length=40, blank=True, default="",
        help_text="VO NumeroCertificado visível <SLUG>-<YYYY>-<NNNNNN> (sem buracos).",
    )
    versao = models.IntegerField(
        default=1, help_text="Reemissão cria v(N+1); v(N)→SUBSTITUIDA (US-CER-004)."
    )
    versao_anterior_id = models.UUIDField(
        null=True, blank=True, help_text="Link p/ v(N) na reemissão. NULL em v1."
    )
    perfil_emissor_no_momento = models.CharField(  # noqa: DJ001 -- NULL = não-emitido (≠ ''); preenchido server-side só na emissão
        max_length=1, null=True, blank=True,
        help_text="Perfil regulatório do tenant na emissão (CHAR(1) — ADR-0067 / "
        "INV-CER-SNAPSHOT-PERFIL-001). Preenchido server-side, imutável pós-emissão.",
    )
    faixa_certificado_min = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True,
        help_text="Menor ponto VÁLIDO (metadado — INV-CER-RECONCILIA-003).",
    )
    faixa_certificado_max = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True,
        help_text="Maior ponto VÁLIDO (metadado; pontos discretos = verdade).",
    )
    tipo_acreditacao = models.CharField(  # noqa: DJ001 -- NULL = indefinido até emissão (≠ choice vazia)
        max_length=10, choices=_choices(TipoAcreditacao), null=True, blank=True,
        help_text="RBC (perfil A, pontos cobertos) / NAO_RBC (cl. 8.1.3 / ADR-0075).",
    )
    snapshot_equipamento_json = models.JSONField(
        default=dict, blank=True,
        help_text="Equipamento congelado na emissão (paridade pós-baixa — US-CER-013).",
    )
    snapshot_padroes_usados_json = models.JSONField(
        default=list, blank=True,
        help_text="Padrões usados + vigência congelada por padrão (NC-07 / cl. 6.5).",
    )
    regra_decisao_snapshot = models.JSONField(
        null=True, blank=True,
        help_text="Regra de decisão congelada (cl. 7.8.6 / ADR-0024 — NC-04).",
    )
    reconciliacao_hash = models.CharField(
        max_length=120, blank=True, default="",
        help_text="Fecho WORM da tabela ponto-a-ponto (v<NN>$<base64> — T-CER-011).",
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4, help_text="Cadeia forense."
    )
    revision = models.IntegerField(
        default=0, help_text="Optimistic lock CAS (UPDATE WHERE revision=:esperada)."
    )

    objects = CertificadoVigentesManager()
    all_objects = models.Manager()  # noqa: DJ012 -- quirk ruff manager tipado generico

    class Meta:
        app_label = "certificados"
        db_table = "certificados"
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ["-criado_em"]
        constraints = [
            # Idempotência da emissão: 1 certificado por (tenant, calibração, versão).
            models.UniqueConstraint(
                fields=("tenant", "calibracao_id", "versao"),
                name="uq_cert_calibracao_versao",
                condition=models.Q(calibracao_id__isnull=False),
            ),
        ]
        indexes = [
            # INV-025 query hot path — trigger PG e service usam isso.
            models.Index(
                fields=["equipamento", "status", "revogado_em"],
                name="ix_cert_eq_status_rev",
            ),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"Cert {self.id} eq={self.equipamento_id} "
            f"status={self.status} v{self.versao}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)


class PontoReconciliado(models.Model):
    """Linha 1:N do certificado (WORM Padrão B) — um ponto reportado (T-CER-021).

    Imutável pós-INSERT (trigger 0005 — INV-CER-WORM-001). Espelha
    `PontoReconciliadoSnapshot` do domínio com colunas tipadas. `u_no_ponto` é
    `U` metrológico (lowercase no schema; mapper converte p/ `U_no_ponto`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="pontos_reconciliados"
    )
    certificado = models.ForeignKey(
        Certificado, on_delete=models.PROTECT, related_name="pontos_reconciliados"
    )
    ponto_calibracao = models.DecimalField(max_digits=30, decimal_places=12)
    valor_reportado = models.DecimalField(max_digits=30, decimal_places=12)
    u_no_ponto = models.DecimalField(
        max_digits=30, decimal_places=12, help_text="U expandida no ponto (ADR-0077)."
    )
    k_no_ponto = models.DecimalField(max_digits=20, decimal_places=10)
    nivel_confianca_no_ponto = models.DecimalField(max_digits=6, decimal_places=4)
    grau_liberdade_efetivo_no_ponto = models.DecimalField(
        max_digits=20, decimal_places=6, help_text="nu_eff (999999 = infinito prático)."
    )
    cmc_no_ponto = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True,
        help_text="CMC no ponto (NULL = não-RBC no ponto).",
    )
    classificacao = models.CharField(max_length=20, choices=_choices(ClassificacaoPonto))
    u_igual_cmc_suspeita = models.BooleanField(default=False)
    incluido_no_certificado = models.BooleanField(default=True)
    ressalva_nao_rbc = models.TextField(
        blank=True, default="",
        help_text="Obrigatória quando EMITIR_NAO_RBC_NO_PONTO (cl. 8.1.3 / C-03).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "certificados"
        db_table = "ponto_reconciliado"
        verbose_name = "Ponto reconciliado"
        verbose_name_plural = "Pontos reconciliados"
        ordering = ["ponto_calibracao"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "certificado", "ponto_calibracao"),
                name="uq_ponto_recon_cert_ponto",
            ),
        ]
        indexes = [
            models.Index(fields=["certificado", "ponto_calibracao"], name="ix_ponto_recon_cert"),
        ]

    def __str__(self) -> str:
        return f"PontoReconciliado({self.ponto_calibracao} {self.classificacao})"


class AnaliseReconciliacaoCert(models.Model):
    """Decisão WORM do RT sobre um ponto problemático (T-CER-021 / NC-03).

    Ligada a `calibracao_id` (existe ANTES da emissão — pré-condição), não ao
    certificado. INSERT-only (trigger 0005). `categoria_motivo` enum (C-02).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="analises_reconciliacao_cert"
    )
    calibracao_id = models.UUIDField(db_index=True)
    ponto_calibracao = models.DecimalField(max_digits=30, decimal_places=12)
    decisao_rt = models.CharField(max_length=30, choices=_choices(DecisaoReconciliacaoRT))
    categoria_motivo = models.CharField(
        max_length=30, choices=_choices(CategoriaMotivoExclusao)
    )
    justificativa_canonicalizada = models.TextField()
    justificativa_hash = models.CharField(max_length=120)
    ressalva_nao_rbc = models.TextField(blank=True, default="")
    decisor_id_hash = models.CharField(max_length=120, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        app_label = "certificados"
        db_table = "analise_reconciliacao_cert"
        verbose_name = "Análise de reconciliação (certificado)"
        verbose_name_plural = "Análises de reconciliação (certificado)"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "calibracao_id", "ponto_calibracao"),
                name="uq_analise_recon_calibracao_ponto",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "calibracao_id"], name="ix_analise_recon_calib"
            ),
        ]

    def __str__(self) -> str:
        return f"AnaliseReconciliacao({self.calibracao_id} ponto={self.ponto_calibracao} {self.decisao_rt})"


class NumeroCertificadoReservado(models.Model):
    """Reserva do número VISÍVEL do certificado (T-CER-031 / INV-CER-NUM-001).

    Densidade SEM BURACOS por (tenant, tipo, ano) — NIT-DICLA-021. Reserva TTL 5min:
    `confirmado=False` até a emissão cravar; expira e é liberada se a emissão não
    confirmar (reuso). Distinto do `numero_interno` (sequence PG global, buracos OK —
    INV-CER-NUM-002). Triggers PG (0008): consecutividade no INSERT, confirmação
    one-shot e bloqueio de DELETE de número confirmado (cancelamento PRESERVA o
    número, não devolve à sequência).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="numeros_certificado_reservados"
    )
    tipo = models.CharField(
        max_length=20, default="CERTIFICADO",
        help_text="Discriminador de sequência (1 sequência por tenant+ano).",
    )
    ano = models.IntegerField(db_index=True)
    sequencial = models.IntegerField(help_text="N do <SLUG>-<YYYY>-<NNNNNN> (sem buracos).")
    reservado_em = models.DateTimeField(auto_now_add=True)
    ttl_expira_em = models.DateTimeField(
        help_text="Reserva não-confirmada expira aqui (T-CER-031 — 5min)."
    )
    confirmado = models.BooleanField(
        default=False, help_text="True na confirmação one-shot (transação da emissão)."
    )
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        app_label = "certificados"
        db_table = "numero_certificado_reservado"
        verbose_name = "Número de certificado reservado"
        verbose_name_plural = "Números de certificado reservados"
        ordering = ["tenant", "tipo", "ano", "sequencial"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "tipo", "ano", "sequencial"),
                name="uq_num_cert_reservado",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "tipo", "ano"], name="ix_num_cert_reservado_chave"
            ),
        ]

    def __str__(self) -> str:
        return (
            f"NumeroReservado({self.tipo}-{self.ano}-{self.sequencial:06d} "
            f"confirmado={self.confirmado})"
        )
