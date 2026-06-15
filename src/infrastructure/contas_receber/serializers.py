"""Serializers DRF da frente contas-receber (Fatia 2a — T-CR-035).

O perfil regulatório do tenant NUNCA vem do payload (INV-FIN-SNAPSHOT-PERFIL-001 —
server-side via ContextVar + `obter_perfil_tenant_corrente`).
A categoria de receita é derivada/validada no USE CASE (ADR-0073 / D-CR-5),
nunca no serializer.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.domain.contas_receber.enums import CategoriaReceita, MeioCobranca

_MEIO_CHOICES = [m.value for m in MeioCobranca]
_CATEGORIA_CHOICES = [c.value for c in CategoriaReceita]


class CriarTituloSerializer(serializers.Serializer[Any]):
    """Payload de criação manual de título (US-CR-001 / T-CR-030).

    `categoria_receita` é opcional: se omitida, é derivada automaticamente pelo perfil
    (D-CR-5). Se informada, é validada no use case (ADR-0073).
    `perfil` NUNCA vem do payload — server-side (D-CR-6 / INV-FIN-SNAPSHOT-PERFIL-001).
    """

    cliente_referencia_hash = serializers.CharField(max_length=80)
    cliente_key_id = serializers.CharField(max_length=10)
    valor_centavos = serializers.IntegerField(min_value=1)
    data_vencimento = serializers.DateField()
    meio = serializers.ChoiceField(choices=_MEIO_CHOICES)
    cliente_atual_id = serializers.UUIDField(required=False, allow_null=True)
    categoria_receita = serializers.ChoiceField(
        choices=_CATEGORIA_CHOICES,
        required=False,
        allow_null=True,
        allow_blank=False,
    )


class BaixarTituloSerializer(serializers.Serializer[Any]):
    """Payload de baixa manual de título (US-CR-003 / T-CR-032).

    `valor_centavos` — valor recebido (pode ser parcial).
    `data_pagamento` — data da baixa.
    """

    valor_centavos = serializers.IntegerField(min_value=1)
    data_pagamento = serializers.DateField()
    comprovante_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)


class CancelarTituloSerializer(serializers.Serializer[Any]):
    """Payload de cancelamento de título (T-CR-034).

    `razao` — motivo livre (vai no payload do evento; não há mínimo de chars aqui
    pois não é campo WORM — diferente do `justificativa` do override).
    """

    razao = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)
