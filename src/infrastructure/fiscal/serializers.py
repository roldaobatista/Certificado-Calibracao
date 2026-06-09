"""Serializers DRF da frente fiscal/NFS-e (Fatia 2 — T-FIS-032).

O perfil regulatório do tenant NUNCA vem do payload (INV-FIS-001 — server-side via
ContextVar). O `tipo_acreditacao` do vínculo também é resolvido server-side a partir
do `certificado_id` (INV-FIS-002 — nunca do payload). O serializer aceita só o que é
input legítimo do caller.
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.fiscal.enums import TipoServico

_TIPO_SERVICO_CHOICES = [t.value for t in TipoServico]


class EmitirNfseSerializer(serializers.Serializer):
    """Payload de emissão (US-FIS-001). `amount_centavos` é input do caller
    (orçamentos diferido — seam pronto)."""

    origem_id = serializers.UUIDField()
    tipo_servico = serializers.ChoiceField(choices=_TIPO_SERVICO_CHOICES)
    amount_centavos = serializers.IntegerField(min_value=1)
    issuer_taxid = serializers.CharField(max_length=20)
    customer_taxid = serializers.CharField(max_length=20)
    customer_name = serializers.CharField(max_length=200)
    cliente_referencia_hash = serializers.CharField(max_length=80)
    service_description = serializers.CharField(max_length=1000)
    service_code = serializers.CharField(max_length=40)
    correlation_id = serializers.UUIDField()
    certificado_id = serializers.UUIDField(required=False, allow_null=True)
    declaracao_id = serializers.UUIDField(required=False, allow_null=True)


class CancelarNfseSerializer(serializers.Serializer):
    """Cancelamento (US-FIS-003) — motivo ≥30ch (AC-FIS-003-1)."""

    motivo = serializers.CharField(min_length=30, max_length=2000)
