# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Frente fiscal/NFS-e — model Django (Fatia 1b, T-FIS-020/021).

1 tabela achatada `nota_fiscal_servico` (colunas tipadas). Espelha a entidade
`NotaFiscalServico` do domínio (`src/domain/fiscal/entities.py`). Choices 1:1 dos
enums de domínio (anti-drift). Domain NÃO importa Django (ADR-0007 — o mapper em
`mappers.py` converte Model ↔ entidade).

WORM Padrão B (ADR-0031 / D-FIS-4 / INV-FIS-004):
- block-delete sempre (retenção fiscal 5a — INV-FIS-008).
- campos probatórios imutáveis pós-INSERT (trigger 0003).
- `status` MUTÁVEL só pelas transições válidas (PENDING→AUTHORIZED|REJECTED;
  AUTHORIZED→CANCELED — validadas no domínio); timestamps `emitido_em`/
  `cancelado_em` one-shot. A imutabilidade probatória vem do `snapshot_hash`
  (emissão) + evento append-only na cadeia hash, não do bloqueio do `status`.

NOTA ADR-0030: NFS-e NÃO é entidade de vigência temporal (não tem janela de
validade `vigencia_inicio/fim`); é um documento de ponto-no-tempo com máquina de
estados. `cancelado_em` é timestamp de transição fiscal (cancelamento SEFAZ), não
`revogado_em` de vigência — daí o override do hook vigencia-canonica.

Schema-irmãos:
- 0001_initial: CreateModel + UNIQUE negócio (tenant, origem_id, versao).
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6).
- 0003_triggers_worm: Padrão B (block-delete + campos probatórios imutáveis).
- 0004_grants_app_user: GRANT app_user.
- 0005_seed_authz_fiscal: matriz papel × ação fiscal.*.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.fiscal.enums import (
    InvoiceStatus,
    TipoAcreditacaoVinculo,
    TipoServico,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class NotaFiscalServico(models.Model):
    """NFS-e de serviço emitida (ou em emissão). WORM Padrão B.

    Idempotência de negócio por `(tenant, origem_id, versao)` (D-FIS-2 /
    INV-FIS-005). `perfil_no_evento` = snapshot do perfil do tenant na emissão
    (ADR-0067 §3). `cliente_referencia_hash` = pseudônimo do tomador (PII clara só
    no `InvoicePayload` ao provider — INV-FIS-009).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="notas_fiscais_servico"
    )
    origem_id = models.UUIDField(
        help_text="Certificado ou OS que disparou a emissão (idempotência de negócio)."
    )
    versao = models.IntegerField(
        default=1, help_text="Tentativa de emissão para a origem (REJECTED → nova versão)."
    )
    status = models.CharField(
        max_length=20,
        choices=_choices(InvoiceStatus),
        help_text="PENDING/AUTHORIZED/REJECTED/CANCELED (D-FIS-3). Mutável só por transição válida.",
    )
    tipo_servico = models.CharField(
        max_length=20,
        choices=_choices(TipoServico),
        help_text="CALIBRACAO exige documento metrológico por perfil (INV-FIS-001).",
    )
    perfil_no_evento = models.CharField(
        max_length=1,
        help_text="Snapshot do perfil regulatório do tenant na emissão (ADR-0067 §3).",
    )
    valor_centavos = models.BigIntegerField(help_text="Valor do serviço em centavos (input do caller).")
    cliente_referencia_hash = models.CharField(
        max_length=80, help_text="Pseudônimo do tomador na trilha (INV-FIS-009 — sem PII clara)."
    )
    provider_invoice_id = models.CharField(
        max_length=120, blank=True, default="", help_text="id do documento no fornecedor (vazio até emitir)."
    )
    autorizacao_codigo = models.CharField(
        max_length=120, blank=True, default="", help_text="Código de autorização do fornecedor."
    )
    rejeicao_motivo = models.TextField(blank=True, default="", help_text="Motivo da rejeição (REJECTED).")
    certificado_id = models.UUIDField(
        null=True, blank=True, help_text="Vínculo metrológico (perfil A/B/C). FK lógica ao M8."
    )
    declaracao_id = models.UUIDField(
        null=True, blank=True, help_text="Declaração de calibração básica (perfil D)."
    )
    tipo_acreditacao_vinculo = models.CharField(
        max_length=10,
        choices=_choices(TipoAcreditacaoVinculo),
        blank=True,
        default="",
        help_text="Snapshot do Certificado.tipo_acreditacao do M8 (INV-FIS-002 — nunca reconsulta Tenant).",
    )
    snapshot_hash = models.CharField(
        max_length=200, help_text="Hash versionado canonicalizado da emissão (ADR-0029/0064). Imutável."
    )
    emitido_em = models.DateTimeField(null=True, blank=True, help_text="One-shot quando autorizada.")
    # vigencia-canonica: skip -- NFS-e nao tem janela de vigencia; cancelado_em e transicao fiscal SEFAZ, nao revogado_em ADR-0030
    cancelado_em = models.DateTimeField(null=True, blank=True, help_text="One-shot no cancelamento SEFAZ.")
    motivo_cancelamento = models.TextField(
        blank=True, default="", help_text=">=30 chars quando cancelada (AC-FIS-003-1)."
    )
    revision = models.IntegerField(
        default=0,
        help_text=(
            "Contador de transições de status (observabilidade). Concorrência "
            "garantida por advisory lock da view + triggers one-shot do banco "
            "(cancelado_em/emitido_em), NÃO por CAS — FIS-SEG-01."
        ),
    )
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Cadeia forense.")
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nota_fiscal_servico"
        verbose_name = "Nota Fiscal de Serviço (NFS-e)"
        verbose_name_plural = "Notas Fiscais de Serviço (NFS-e)"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "origem_id", "versao"),
                name="uq_nfse_origem_versao",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status"], name="nfse_tenant_status_idx"),
            models.Index(fields=["tenant", "origem_id"], name="nfse_tenant_origem_idx"),
        ]

    def __str__(self) -> str:
        return f"NFSe({self.origem_id} v{self.versao} — {self.status})"
