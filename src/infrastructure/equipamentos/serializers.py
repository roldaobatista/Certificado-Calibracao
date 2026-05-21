"""DRF serializers Marco 2 — Equipamento.

Cobertura T-EQP-002: schema minimo de retorno do equipamento pra GET +
campos read-only do estado. Serializer COMPLETO de criacao (POST /equipamentos/)
fica para T-EQP-001 (viewset POST) — esta task entrega apenas endpoint
de etiqueta PDF.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import Equipamento


class EquipamentoLeituraSerializer(serializers.ModelSerializer[Equipamento]):
    """Schema de leitura (GET retrieve / dump rapido).

    T-EQP-024 vai expandir com ficha 360. Aqui o minimo pra retornar
    no header `Link` da etiqueta + futuras chamadas.
    """

    class Meta:
        model = Equipamento
        fields = [
            "id",
            "tag",
            "numero_serie",
            "fabricante",
            "modelo",
            "status",
            "criado_em",
        ]
        read_only_fields = fields
