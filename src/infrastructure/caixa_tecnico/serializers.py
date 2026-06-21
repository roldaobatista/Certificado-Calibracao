"""Serializers DRF da frente caixa_tecnico (Fatia 2 — T-CT-031).

GPS (``gps_lat``/``gps_lng``) é ``read_only=True`` em TODOS os serializers
de escrita — nunca vem do payload (D-CT-6 / INV-LGPD-CONSENT-001 /
mass-assignment-check).

``perfil`` NUNCA vem do payload — server-side via ContextVar +
``obter_perfil_tenant_corrente`` (INV-FIN-SNAPSHOT-PERFIL-001).

# mass-assignment-check: gps_lat e gps_lng são read_only=True (D-CT-6 / INV-LGPD-CONSENT-001)
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    MeioEntrega,
    TipoDespesa,
)

_CATEGORIA_CHOICES = [c.value for c in CategoriaDespesa]
_MEIO_CHOICES = [m.value for m in MeioEntrega]
_TIPO_CHOICES = [t.value for t in TipoDespesa]


class LancarDespesaSerializer(serializers.Serializer[Any]):
    """Payload de lançamento de despesa (US-CT-002 / D-CT-3/4).

    ``gps_lat`` / ``gps_lng`` são ``read_only=True`` — NUNCA aceitos do payload
    (D-CT-6 / INV-LGPD-CONSENT-001).
    ``perfil`` NUNCA vem do payload — server-side.
    ``foto_base64`` é a foto codificada em Base64 para envio REST.
    """

    foto_base64 = serializers.CharField(max_length=10_000_000)  # ~7.5 MB original
    foto_mime = serializers.ChoiceField(choices=["image/jpeg", "image/png"])
    categoria = serializers.ChoiceField(choices=_CATEGORIA_CHOICES)
    valor_centavos = serializers.IntegerField(min_value=0, required=False, default=0)
    data = serializers.DateField()  # type: ignore[assignment]  # DRF: campo "data" (data da despesa) shadowa a property Serializer.data; OK em runtime (campos coletados via metaclass _declared_fields)
    colaborador_id = serializers.UUIDField()
    descricao = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    km_percorridos = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=0
    )
    client_offline_id = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None, max_length=120
    )
    os_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    tipo = serializers.ChoiceField(
        choices=_TIPO_CHOICES, required=False, default=TipoDespesa.NORMAL.value
    )
    despesa_origem_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    # GPS — read_only: nunca aceitos do payload (D-CT-6 / mass-assignment-check)
    gps_lat = serializers.FloatField(read_only=True)
    gps_lng = serializers.FloatField(read_only=True)


class ReapresentarDespesaSerializer(serializers.Serializer[Any]):
    """Payload de reapresentação de despesa rejeitada (US-CT-007 / D-CT-3).

    Nova foto substitui a anterior. GPS sempre read_only.

    # mass-assignment-check: gps_lat e gps_lng são read_only=True (D-CT-6 / INV-LGPD-CONSENT-001)
    """

    foto_base64 = serializers.CharField(max_length=10_000_000)
    foto_mime = serializers.ChoiceField(choices=["image/jpeg", "image/png"])
    colaborador_id = serializers.UUIDField()

    # GPS — read_only
    gps_lat = serializers.FloatField(read_only=True)
    gps_lng = serializers.FloatField(read_only=True)


class RejeitarDespesaSerializer(serializers.Serializer[Any]):
    """Payload de rejeição de despesa (US-CT-004 / D-CT-3).

    ``motivo`` obrigatório ≥ 30 chars (validado no use case).
    """

    motivo = serializers.CharField(min_length=30, max_length=5000)


class SolicitarAdiantamentoSerializer(serializers.Serializer[Any]):
    """Payload de solicitação de adiantamento (US-CT-001 / D-CT-7)."""

    caixa_id = serializers.UUIDField()
    valor_centavos = serializers.IntegerField(min_value=1)
    meio = serializers.ChoiceField(choices=_MEIO_CHOICES)
    justificativa = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None, max_length=2000
    )


class AprovarAdiantamentoSerializer(serializers.Serializer[Any]):
    """Payload de aprovação de adiantamento (US-CT-005 / D-CT-7).

    ``aprovado_por_id`` é o ID do gestor que aprova (ato gerencial rastreável).
    Alçada validada server-side no use case (D-CT-9).
    """

    aprovado_por_id = serializers.UUIDField()


class RecusarAdiantamentoSerializer(serializers.Serializer[Any]):
    """Payload de recusa de adiantamento (US-CT-006 / D-CT-7).

    ``motivo`` obrigatório ≥ 30 chars (validado no use case).
    """

    motivo = serializers.CharField(min_length=30, max_length=5000)


class EntregarAdiantamentoSerializer(serializers.Serializer[Any]):
    """Payload de entrega de adiantamento (US-CT-008 / D-CT-7).

    ``entregue_por_id`` é o ID de quem confirmou a entrega.
    """

    entregue_por_id = serializers.UUIDField()


class FecharPrestacaoSerializer(serializers.Serializer[Any]):
    """Payload de fechamento de prestação de contas (US-CT-009 / D-CT-8).

    ``periodo_de`` / ``periodo_ate`` delimitam o período fechado.
    ``caixa_id`` identifica o caixa do técnico.
    """

    caixa_id = serializers.UUIDField()
    periodo_de = serializers.DateField()
    periodo_ate = serializers.DateField()
    observacoes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None, max_length=5000
    )


# ---------------------------------------------------------------------------
# Serializer do lote
# ---------------------------------------------------------------------------


class ItemLoteSerializer(serializers.Serializer[Any]):
    """Item individual do lote de sincronização offline (D-CT-5).

    ``foto_base64`` é a foto codificada em Base64.
    GPS sempre read_only — nunca do payload.

    # mass-assignment-check: gps_lat e gps_lng são read_only=True (D-CT-6 / INV-LGPD-CONSENT-001)
    """

    foto_base64 = serializers.CharField(max_length=10_000_000)
    foto_mime = serializers.ChoiceField(choices=["image/jpeg", "image/png"])
    categoria = serializers.ChoiceField(choices=_CATEGORIA_CHOICES)
    valor_centavos = serializers.IntegerField(min_value=0, required=False, default=0)
    data = serializers.DateField()  # type: ignore[assignment]  # DRF: campo "data" (data da despesa) shadowa a property Serializer.data; OK em runtime (campos coletados via metaclass _declared_fields)
    descricao = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    km_percorridos = serializers.IntegerField(
        required=False, allow_null=True, default=None, min_value=0
    )
    client_offline_id = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None, max_length=120
    )
    os_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    # GPS — read_only
    gps_lat = serializers.FloatField(read_only=True)
    gps_lng = serializers.FloatField(read_only=True)


class SyncDespesasLoteSerializer(serializers.Serializer[Any]):
    """Payload do endpoint de sincronização em lote (US-CT-010 / D-CT-5).

    ``caixa_id`` e ``colaborador_id`` identificam o técnico.
    ``itens`` são os itens do lote (máximo 20 — LoteExcedido 413 se ultrapassar).
    """

    caixa_id = serializers.UUIDField()
    colaborador_id = serializers.UUIDField()
    itens = ItemLoteSerializer(many=True)
