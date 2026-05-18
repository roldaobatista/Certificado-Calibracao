"""Serializers DRF do modulo Clientes.

Validacao via VOs CPF/CNPJ no boundary — rejeita formato/DV invalido ANTES de
chegar no modelo. Documento eh normalizado (sem pontuacao, UPPER pra CNPJ).
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.shared.value_objects import CNPJ, CPF
from src.infrastructure.clientes.models import Cliente, TipoPessoa


class ClienteSerializer(serializers.ModelSerializer):
    """Cliente — entrada + saida.

    O campo `tenant` NAO eh aceito da request: deriva do active_tenant
    setado pelo TenantMiddleware (defesa em profundidade — middleware injeta).
    """

    # Campo livre de tamanho na entrada — VO normaliza antes do max_length.
    documento = serializers.CharField(max_length=32)

    class Meta:
        model = Cliente
        fields = [
            "id",
            "tipo_pessoa",
            "documento",
            "nome",
            "nome_fantasia",
            "email",
            "telefone",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em"]

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        """Normaliza + valida documento via VO."""
        tipo = attrs.get("tipo_pessoa") or getattr(self.instance, "tipo_pessoa", None)
        doc = attrs.get("documento")
        if doc is not None and tipo is not None:
            try:
                if tipo == TipoPessoa.PF:
                    attrs["documento"] = CPF(doc).value
                elif tipo == TipoPessoa.PJ:
                    attrs["documento"] = CNPJ(doc).value
                else:
                    raise serializers.ValidationError({"tipo_pessoa": "Tipo invalido"})
            except ValueError as e:
                raise serializers.ValidationError({"documento": str(e)})
        return attrs
