# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""M9 `metrologia/licencas-acreditacoes` — modelos Django (T-LIC-020).

5 tabelas:
- `documento_regulatorio` (raiz) — espelha `DocumentoRegulatorio` do domínio.
  Padrão B WORM (ADR-0031): mutável só em `responsavel_id`/`bloqueante`/`observacao`;
  vigência muda criando `RevisaoDocumento` (append-only). CAS via `revision`.
- `revisao_documento` (WORM append-only) — histórico versionado imutável (INV-LIC-WORM-001).
- `alerta_vencimento` — idempotente por `(tenant, documento, janela_dias)`.
- `bloqueio_operacional` — ativo quando doc bloqueante vence (INV-032).
- `evento_emergencial_licenca` (WORM append-only) — liberação auditada (INV-033).

Choices 1:1 dos enums de domínio (anti-drift). Domain NÃO importa Django (ADR-0007 —
adapter em `repositories.py` converte Model <-> Snapshot).

Schema-irmãos (ADR-0002/0030/0031/0079):
- 0001_initial: CreateModel + UNIQUE idempotência alertas.
- 0002_rls_policies: RLS pattern v2 nas 5 tabelas.
- 0003_triggers_worm: Padrão B — block-delete + WORM em revisão/evento + raiz CONFIRMADA.
- 0004_grants_app_user: GRANT app_user.
- 0005_seed_authz_licencas: matriz papel × ação.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.metrologia.licencas_acreditacoes.enums import (
    CanalAlerta,
    MotivoRevisao,
    StatusAlerta,
    StatusDocumento,
    TipoDocumentoRegulatorio,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class DocumentoRegulatorio(models.Model):
    """Documento regulatório da empresa (acreditação CGCRE, licença, ART/RRT, etc).

    Acreditação CGCRE: fonte rica da vigência (ADR-0079) — sincroniza o cache
    `Tenant.acreditacao_vigencia_fim` via `aplicar_evento_cgcre`. PII de titular
    (ART/RRT) via par `titular_referencia_hash`/`key_id` (ADR-0032 — número/órgão
    NÃO são PII; CPF/nome sim). Vigência canônica ADR-0030; Padrão B WORM ADR-0031.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="documentos_regulatorios"
    )
    tipo = models.CharField(
        max_length=30,
        choices=_choices(TipoDocumentoRegulatorio),
        help_text="Tipo do documento (acreditação CGCRE, ART/RRT, licença, etc).",
    )
    numero = models.CharField(max_length=120, help_text="Número do documento no órgão emissor.")
    orgao_emissor = models.CharField(max_length=120, help_text="Órgão emissor (CGCRE, CREA, etc).")
    vigencia_inicio = models.DateField(help_text="Início da vigência (data_emissao da revisão atual).")
    vigencia_fim = models.DateField(help_text="Fim da vigência (data_validade). ADR-0030.")
    bloqueante = models.BooleanField(
        default=False,
        help_text="Vencido bloqueia operação dependente (INV-032). Fronteira por tipo (D-LIC-5).",
    )
    status_cache = models.CharField(
        max_length=20,
        choices=_choices(StatusDocumento),
        default=StatusDocumento.VIGENTE.value,
        help_text="Cache do status calculado (verdade = vigencia_fim vs hoje). Recalculado no job.",
    )
    escopo = models.TextField(
        blank=True, default="", help_text="Grandezas/faixas — obrigatório para ACREDITACAO_CGCRE (RBC-M9-05)."
    )
    numero_cgcre = models.CharField(
        max_length=60, blank=True, default="", help_text="Nº CGCRE (acreditação)."
    )
    ilac_mra_aderido = models.BooleanField(
        default=False, help_text="Aderência ILAC-MRA (só perfil A — espelha Tenant.ilac_mra)."
    )
    titular_referencia_hash = models.CharField(
        max_length=128, blank=True, default="",
        help_text="Hash KMS do CPF/nome do titular (ART/RRT) — ADR-0032 PII anonimizável.",
    )
    titular_referencia_key_id = models.CharField(
        max_length=40, blank=True, default="", help_text="key_id versionado (vN) do hash — ADR-0032."
    )
    responsavel_id = models.UUIDField(
        null=True, blank=True, help_text="FK Usuario que cuida da renovação (mutável)."
    )
    observacao = models.TextField(blank=True, default="")
    perfil_emissor_no_momento = models.CharField(
        max_length=1, blank=True, default="",
        help_text="Snapshot do perfil do tenant na criação (ADR-0067).",
    )
    revision = models.IntegerField(
        default=0, help_text="Optimistic lock CAS. UPDATE WHERE revision=:esperada."
    )
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Cadeia forense.")
    revogado_em = models.DateTimeField(
        null=True, blank=True, help_text="Soft-delete B (ADR-0031). NULL = vigente."
    )
    motivo_revogacao = models.TextField(
        blank=True, default="", help_text=">=10 chars quando revogado (ADR-0030)."
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    criado_por = models.UUIDField(help_text="Ator do cadastro.")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documento_regulatorio"
        verbose_name = "Documento Regulatório"
        verbose_name_plural = "Documentos Regulatórios"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "tipo", "numero", "orgao_emissor"),
                name="uq_documento_regulatorio_chave_natural",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "tipo", "status_cache"], name="docreg_tenant_tipo_st_idx"),
            models.Index(fields=["tenant", "vigencia_fim"], name="docreg_tenant_vigfim_idx"),
        ]

    def __str__(self) -> str:
        return f"DocumentoRegulatorio({self.tipo} {self.numero} — {self.status_cache})"


class RevisaoDocumento(models.Model):
    """Histórico versionado append-only (WORM — INV-LIC-WORM-001). UPDATE/DELETE
    bloqueados por trigger (0003). Renovação/retificação = nova revisão."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="revisoes_documento"
    )
    documento = models.ForeignKey(
        DocumentoRegulatorio, on_delete=models.PROTECT, related_name="revisoes"
    )
    numero_revisao = models.IntegerField(help_text="Incremental por documento (1 = cadastro inicial).")
    data_emissao = models.DateField()
    data_validade = models.DateField(help_text="data_validade > data_emissao.")
    anexo_id = models.UUIDField(help_text="FK Anexo (B2 WORM).")
    anexo_sha256 = models.CharField(max_length=64, help_text="sha256 server-side (INV-LIC-ANEXO-001).")
    motivo = models.CharField(max_length=20, choices=_choices(MotivoRevisao))
    correlation_id = models.UUIDField(default=uuid.uuid4)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    criado_por = models.UUIDField()

    class Meta:
        db_table = "revisao_documento"
        verbose_name = "Revisão de Documento"
        verbose_name_plural = "Revisões de Documento"
        ordering = ["documento", "-numero_revisao"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "documento", "numero_revisao"),
                name="uq_revisao_documento_numero",
            ),
        ]

    def __str__(self) -> str:
        return f"RevisaoDocumento(doc={self.documento_id} v{self.numero_revisao} — {self.motivo})"


class AlertaVencimento(models.Model):
    """Alerta de vencimento agendado por janela (US-LIC-002). Idempotente por
    `(tenant, documento, janela_dias)` — UNIQUE (anti reagendamento duplicado)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="alertas_vencimento"
    )
    documento = models.ForeignKey(
        DocumentoRegulatorio, on_delete=models.PROTECT, related_name="alertas"
    )
    data_disparo = models.DateField()
    janela_dias = models.IntegerField(help_text="90/60/30/15/7 (JANELAS_ALERTA_DIAS).")
    canal = models.CharField(max_length=20, choices=_choices(CanalAlerta))
    destinatario_id = models.UUIDField()
    status = models.CharField(
        max_length=20, choices=_choices(StatusAlerta), default=StatusAlerta.PENDENTE.value
    )
    tentativas = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alerta_vencimento"
        verbose_name = "Alerta de Vencimento"
        verbose_name_plural = "Alertas de Vencimento"
        ordering = ["-data_disparo"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "documento", "janela_dias"),
                name="uq_alerta_vencimento_idempotente",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status", "data_disparo"], name="alerta_tenant_st_idx"),
        ]

    def __str__(self) -> str:
        return f"AlertaVencimento(doc={self.documento_id} D-{self.janela_dias} — {self.status})"


class BloqueioOperacional(models.Model):
    """Bloqueio ativo quando documento bloqueante vence (INV-032). `data_fim_bloqueio
    is NULL` = ativo; preenchido na renovação (auto-resolve)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="bloqueios_operacionais"
    )
    documento = models.ForeignKey(
        DocumentoRegulatorio, on_delete=models.PROTECT, related_name="bloqueios"
    )
    tipo_documento = models.CharField(
        max_length=30, choices=_choices(TipoDocumentoRegulatorio),
        help_text="Determina a fronteira REBAIXA vs HARD-409 (D-LIC-5).",
    )
    operacao_bloqueada = models.CharField(max_length=80, help_text="Ex.: 'assinatura_certificado'.")
    data_inicio_bloqueio = models.DateTimeField()
    data_fim_bloqueio = models.DateTimeField(
        null=True, blank=True, help_text="NULL = ativo. Auto-resolve na renovação."
    )
    correlation_id = models.UUIDField(default=uuid.uuid4)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bloqueio_operacional"
        verbose_name = "Bloqueio Operacional"
        verbose_name_plural = "Bloqueios Operacionais"
        ordering = ["-data_inicio_bloqueio"]
        indexes = [
            models.Index(fields=["tenant", "documento", "data_fim_bloqueio"], name="bloq_tenant_doc_idx"),
        ]

    def __str__(self) -> str:
        ativo = "ativo" if self.data_fim_bloqueio is None else "resolvido"
        return f"BloqueioOperacional(doc={self.documento_id} {self.operacao_bloqueada} — {ativo})"


class EventoEmergencialLicenca(models.Model):
    """Liberação excepcional auditada (INV-033) — append-only WORM (trigger 0003).
    Registra `assinatura_a3_id` + `justificativa_hash`; validação cripto da A3 é
    DIFERIDA (GATE-LIC-EMERGENCIAL-A3-CRIPTO Wave B). Expira em ≤7d."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="eventos_emergenciais_licenca"
    )
    bloqueio = models.ForeignKey(
        BloqueioOperacional, on_delete=models.PROTECT, related_name="eventos_emergenciais"
    )
    operacao_executada = models.CharField(max_length=80)
    justificativa = models.TextField(help_text=">=100 chars (INV-033 reconciliado — D-LIC-7).")
    justificativa_hash = models.CharField(max_length=64, help_text="sha256 da justificativa (WORM).")
    admin_id = models.UUIDField()
    assinatura_a3_id = models.UUIDField(help_text="FK A3 (existência exigida; validação cripto diferida).")
    libera_apenas_nao_rbc = models.BooleanField(
        default=False, help_text="True quando o bloqueio é de acreditação CGCRE (D-LIC-6)."
    )
    expira_em = models.DateTimeField(help_text="Janela ≤7d.")
    correlation_id = models.UUIDField(default=uuid.uuid4)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "evento_emergencial_licenca"
        verbose_name = "Evento Emergencial (Licença)"
        verbose_name_plural = "Eventos Emergenciais (Licença)"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "bloqueio"], name="evtemerg_tenant_bloq_idx"),
        ]

    def __str__(self) -> str:
        return f"EventoEmergencialLicenca(bloqueio={self.bloqueio_id} — expira {self.expira_em})"
