"""Serializers DRF da frente `configuracoes-sistema` (Fatia 2 — T-CFG-033).

O `regime_numeracao` e o `reset_anual` da série NUNCA vêm do payload — são
DERIVADOS (ADR-0080/TL-07) no use case. O CNPJ é validado pelo VO (ADR-0017) no
use case (ValueError → 400). O serializer aceita só o que é input legítimo.
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.configuracoes_sistema.enums import (
    RegimeTributario,
    TipoDocumento,
    TipoImposto,
)

_REGIME_TRIBUTARIO_CHOICES = [r.value for r in RegimeTributario]
_TIPO_IMPOSTO_CHOICES = [t.value for t in TipoImposto]
_TIPO_DOCUMENTO_CHOICES = [t.value for t in TipoDocumento]


class AtualizarEmpresaSerializer(serializers.Serializer):
    """Upsert do cadastro tributário (US-CFG-001)."""

    razao_social = serializers.CharField(max_length=200)
    cnpj = serializers.CharField(max_length=20)  # VO normaliza/valida (ADR-0017)
    regime_tributario = serializers.ChoiceField(choices=_REGIME_TRIBUTARIO_CHOICES)
    inscricao_estadual = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    inscricao_municipal = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    endereco = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    logo_url = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")
    site = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class AdicionarFilialSerializer(serializers.Serializer):
    """Filial com CNPJ próprio (AC-CFG-001-2); INV-037 validado no use case."""

    cnpj = serializers.CharField(max_length=20)
    nome = serializers.CharField(max_length=200)
    eh_matriz = serializers.BooleanField()
    endereco = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    inscricao_estadual = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    inscricao_municipal = serializers.CharField(
        max_length=20, required=False, allow_blank=True, default=""
    )
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")


class CadastrarImpostoSerializer(serializers.Serializer):
    """Nova linha de catálogo (US-CFG-003) — imutável pós-INSERT."""

    tipo = serializers.ChoiceField(choices=_TIPO_IMPOSTO_CHOICES)
    aliquota = serializers.DecimalField(max_digits=7, decimal_places=4)
    vigencia_inicio = serializers.DateTimeField()
    vigencia_fim = serializers.DateTimeField(required=False, allow_null=True, default=None)
    filial_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    cfop_padrao = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    ncm_padrao = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    iss_retido_fonte = serializers.BooleanField(required=False, default=False)
    tem_st = serializers.BooleanField(required=False, default=False)
    simples_excedeu_sublimite = serializers.BooleanField(required=False, default=False)
    observacoes = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )


class EncerrarVigenciaImpostoSerializer(serializers.Serializer):
    """Encerrar = one-shot NULL→data (D-CFG-3)."""

    fim = serializers.DateTimeField()


class CriarSerieSerializer(serializers.Serializer):
    """Série de numeração (US-CFG-002). SEM `regime_numeracao`/`reset_anual` —
    derivados do tipo/formato (ADR-0080/TL-07), nunca do caller."""

    tipo = serializers.ChoiceField(choices=_TIPO_DOCUMENTO_CHOICES)
    prefixo = serializers.CharField(max_length=16)
    formato = serializers.CharField(max_length=60, required=False, default="{prefixo}-{seq}")
    padding = serializers.IntegerField(required=False, default=6, min_value=1, max_value=12)
    filial_id = serializers.UUIDField(required=False, allow_null=True, default=None)
