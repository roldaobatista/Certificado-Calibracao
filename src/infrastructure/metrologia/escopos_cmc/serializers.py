"""Serializers DRF do M6 escopos-cmc (T-ECMC-030).

Validam o payload das actions do EscopoCMCViewSet. `rbc_acreditado` é INTENÇÃO —
o efetivo é forçado server-side por perfil (anti-fraude ADR-0075). O perfil
regulatório do tenant NUNCA vem do payload (ADR-0067). Rótulo perfil-aware
(A=CMC / B-C-D=capacidade interna) é da camada de apresentação (ADR-0075).
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.metrologia.escopos_cmc.enums import FormaCMC
from src.domain.metrologia.value_objects import Grandeza

_GRANDEZA_CHOICES = [g.value for g in Grandeza]
_FORMA_CHOICES = [f.value for f in FormaCMC]


class _CMCFieldsMixin(serializers.Serializer):
    cmc_forma = serializers.ChoiceField(choices=_FORMA_CHOICES, default=FormaCMC.ABSOLUTA.value)
    cmc_valor = serializers.DecimalField(max_digits=30, decimal_places=12, min_value=0)
    cmc_unidade = serializers.CharField(max_length=20)
    cmc_coef_relativo = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    numero_escopo_cgcre = serializers.CharField(
        max_length=60, required=False, allow_blank=True, default=""
    )
    documento_regulatorio_id = serializers.UUIDField(required=False, allow_null=True)
    correlation_id = serializers.UUIDField()


class CadastrarEscopoSerializer(_CMCFieldsMixin):
    grandeza = serializers.ChoiceField(choices=_GRANDEZA_CHOICES)
    faixa_min = serializers.DecimalField(max_digits=30, decimal_places=12)
    faixa_max = serializers.DecimalField(max_digits=30, decimal_places=12)
    unidade = serializers.CharField(max_length=20)
    rbc_acreditado = serializers.BooleanField(default=False)
    procedimento_id = serializers.UUIDField(required=False, allow_null=True)


class RevisarEscopoSerializer(_CMCFieldsMixin):
    """Revisão preserva a chave natural (grandeza/faixa/método) da versão atual —
    só os campos CMC/número/documento mudam (escopo_id vem da URL)."""


class RevogarEscopoSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=2000, min_length=10)
