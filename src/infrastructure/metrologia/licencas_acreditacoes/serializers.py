"""Serializers DRF do M9 licencas-acreditacoes (T-LIC-044).

Validam o payload das actions do `DocumentoRegulatorioViewSet`. O perfil regulatório
do tenant NUNCA vem do payload (ADR-0067 — defesa L6): é derivado server-side. O
`bloqueante` é DERIVADO da fronteira por tipo (D-LIC-5) — também não vem do payload.
`anexo_sha256` é exigido não-vazio (INV-LIC-ANEXO-001); a recomputação a partir do
binário real fica no GATE-LIC-PDF (anexo B2 diferido — espelha M7). O read-path
(`retrieve`/`listar`) usa funções de serialização (não Serializers DRF) lendo só
campos persistidos.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from rest_framework import serializers

from src.domain.metrologia.licencas_acreditacoes.entities import (
    DocumentoRegulatorio,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    MotivoRevisao,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import calcular_status

_TIPO_CHOICES = [t.value for t in TipoDocumentoRegulatorio]
# Renovação nunca é CADASTRO_INICIAL (validado também no use case).
_MOTIVO_RENOVACAO_CHOICES = [
    MotivoRevisao.RENOVACAO.value,
    MotivoRevisao.RETIFICACAO.value,
]
_PERFIL_PROMOCAO_CHOICES = ["A", "B", "C"]  # alvo monotônico (função valida transição)


class CadastrarDocumentoSerializer(serializers.Serializer):
    """US-LIC-001 — cadastro de documento regulatório (não-promoção)."""

    tipo = serializers.ChoiceField(choices=_TIPO_CHOICES)
    numero = serializers.CharField(max_length=120)
    orgao_emissor = serializers.CharField(max_length=120)
    vigencia_inicio = serializers.DateField()
    vigencia_fim = serializers.DateField()
    anexo_id = serializers.UUIDField()
    anexo_sha256 = serializers.CharField(min_length=1, max_length=64)
    escopo = serializers.CharField(required=False, allow_blank=True, default="")
    numero_cgcre = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=60
    )
    ilac_mra_aderido = serializers.BooleanField(required=False, default=False)
    titular_referencia_hash = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=128
    )
    titular_referencia_key_id = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=40
    )
    responsavel_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    observacao = serializers.CharField(required=False, allow_blank=True, default="")
    correlation_id = serializers.UUIDField()


class PromoverPerfilASerializer(serializers.Serializer):
    """US-LIC-001 AC-LIC-001-4 — cadastro de acreditação CGCRE + promoção de perfil."""

    perfil_novo = serializers.ChoiceField(choices=_PERFIL_PROMOCAO_CHOICES)
    numero = serializers.CharField(max_length=120)
    orgao_emissor = serializers.CharField(max_length=120)
    vigencia_inicio = serializers.DateField()
    vigencia_fim = serializers.DateField()
    escopo = serializers.CharField(max_length=10000)
    numero_cgcre = serializers.CharField(max_length=60)
    assinatura_a3_id = serializers.UUIDField()
    motivo = serializers.CharField(min_length=100, max_length=2000)
    auditor_cgcre = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None, max_length=200
    )
    ilac_mra_aderido = serializers.BooleanField(required=False, default=False)
    anexo_id = serializers.UUIDField()
    anexo_sha256 = serializers.CharField(min_length=1, max_length=64)
    correlation_id = serializers.UUIDField()


class RenovarDocumentoSerializer(serializers.Serializer):
    """US-LIC-002/004 — nova revisão (renovação/retificação)."""

    nova_vigencia_inicio = serializers.DateField()
    nova_vigencia_fim = serializers.DateField()
    anexo_id = serializers.UUIDField()
    anexo_sha256 = serializers.CharField(min_length=1, max_length=64)
    motivo = serializers.ChoiceField(
        choices=_MOTIVO_RENOVACAO_CHOICES, default=MotivoRevisao.RENOVACAO.value
    )
    correlation_id = serializers.UUIDField()


class AcionarEmergencialSerializer(serializers.Serializer):
    """US-LIC-003 / INV-033 — liberação emergencial auditada."""

    operacao_executada = serializers.CharField(max_length=80)
    justificativa = serializers.CharField(min_length=100, max_length=2000)
    assinatura_a3_id = serializers.UUIDField()
    janela_dias = serializers.IntegerField(min_value=1, max_value=7)
    correlation_id = serializers.UUIDField()


def serializar_historico_revisoes(
    revisoes: Sequence[RevisaoDocumento],
) -> dict[str, object]:
    """Read-path do histórico versionado (US-LIC-004) — revisões append-only imutáveis
    (WORM), ordenadas por `numero_revisao`. Inclui metadados de auditoria."""
    return {
        "total_revisoes": len(revisoes),
        "revisoes": [
            {
                "numero_revisao": r.numero_revisao,
                "data_emissao": r.data_emissao.isoformat(),
                "data_validade": r.data_validade.isoformat(),
                "motivo": r.motivo.value,
                "anexo_id": str(r.anexo_id),
                "anexo_sha256": r.anexo_sha256,
                "criado_em": r.criado_em.isoformat(),
                "criado_por": str(r.criado_por),
            }
            for r in revisoes
        ],
    }


def serializar_documento_leitura(
    doc: DocumentoRegulatorio, *, hoje: date, revisoes: Sequence[RevisaoDocumento] = ()
) -> dict[str, object]:
    """Read-path do documento (status recalculado on-demand — verdade é vigência)."""
    status = calcular_status(vigencia_fim=doc.vigencia_fim, hoje=hoje)
    return {
        "id": str(doc.id),
        "tipo": doc.tipo.value,
        "numero": doc.numero,
        "orgao_emissor": doc.orgao_emissor,
        "vigencia_inicio": doc.vigencia_inicio.isoformat(),
        "vigencia_fim": doc.vigencia_fim.isoformat(),
        "status": status.value,
        "bloqueante": doc.bloqueante,
        "escopo": doc.escopo,
        "numero_cgcre": doc.numero_cgcre,
        "ilac_mra_aderido": doc.ilac_mra_aderido,
        "responsavel_id": str(doc.responsavel_id) if doc.responsavel_id else None,
        "observacao": doc.observacao,
        "perfil_no_evento": doc.perfil_no_evento,
        "revogado_em": doc.revogado_em.isoformat() if doc.revogado_em else None,
        "revisoes": [
            {
                "numero_revisao": r.numero_revisao,
                "data_emissao": r.data_emissao.isoformat(),
                "data_validade": r.data_validade.isoformat(),
                "motivo": r.motivo.value,
                "anexo_sha256": r.anexo_sha256,
            }
            for r in revisoes
        ],
    }
