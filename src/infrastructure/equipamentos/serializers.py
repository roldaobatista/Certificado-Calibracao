"""DRF serializers Marco 2 — Equipamento (T-EQP-002 + T-EQP-005)."""

from __future__ import annotations

from rest_framework import serializers

from .models import Equipamento
from .validators import (
    LIMITE_LOCALIZACAO_FISICA,
    MENSAGEM_REJEICAO_PII_DIRETA,
    conter_pii_direta,
)


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


class EquipamentoCriarSerializer(serializers.Serializer):
    """Schema de criacao (POST /equipamentos/) — T-EQP-005.

    Campos exigidos por AC-EQP-001-1; `cliente_atual_id` opcional
    (equipamento pode nascer "em estoque" antes de virar de um cliente).
    `localizacao_fisica` valida INV-EQP-LOC-001 (anti-PII direta).
    `perfil_tenant_snapshot` recebe payload validado em Wave A — aqui
    aceitamos qualquer dict; trigger PG impede mutacao pos-INSERT.
    """

    tag = serializers.CharField(max_length=40)
    numero_serie = serializers.CharField(max_length=80)
    fabricante = serializers.CharField(max_length=80)
    modelo = serializers.CharField(max_length=80)
    cliente_atual_id = serializers.UUIDField(required=False, allow_null=True)
    localizacao_fisica = serializers.CharField(
        max_length=LIMITE_LOCALIZACAO_FISICA,
        required=False,
        allow_blank=True,
        default="",
    )
    perfil_tenant_snapshot = serializers.JSONField(required=False, default=dict)
    snapshot_schema_version = serializers.CharField(
        max_length=16, required=False, default="1.0.0"
    )

    def validate_localizacao_fisica(self, value: str) -> str:
        """INV-EQP-LOC-001: rejeita PII direta (CPF/CNPJ/email/telefone/nomes)."""
        if value and conter_pii_direta(value):
            raise serializers.ValidationError(MENSAGEM_REJEICAO_PII_DIRETA)
        return value
