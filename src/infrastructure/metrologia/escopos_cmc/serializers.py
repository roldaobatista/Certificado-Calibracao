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


# ----- Fatia 4: extração PDF CGCRE + conferência humana (T-ECMC-053) -----


class _MapaColunasSerializer(serializers.Serializer):
    """Índice 0-based de cada papel de coluna na tabela extraída (ADR-0072)."""

    grandeza = serializers.IntegerField(min_value=0)
    cmc = serializers.IntegerField(min_value=0)
    faixa = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    faixa_min = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    faixa_max = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    unidade = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    metodo = serializers.IntegerField(min_value=0, required=False, allow_null=True)


class ImportarExtracaoSerializer(serializers.Serializer):
    """Linhas JÁ extraídas do PDF (porta `LeitorTabelaPdf` em infra/cliente) +
    mapa de colunas. O binário->linhas (lib PDF) é porta trocável diferida
    (GATE-ECMC-EXTRACT-PDFLIB). `extraido_em` é server-side (now)."""

    origem_pdf_storage_key = serializers.CharField(max_length=200)
    numero_escopo_cgcre = serializers.CharField(
        max_length=60, required=False, allow_blank=True, default=""
    )
    linhas_cruas = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField(allow_blank=True, trim_whitespace=False)
        ),
        allow_empty=False,
    )
    mapa_colunas = _MapaColunasSerializer()
    correlation_id = serializers.UUIDField()


class ConfirmarExtraidoSerializer(serializers.Serializer):
    """Linhas APROVADAS+NORMALIZADAS pela conferência humana (cada uma vira um
    EscopoCMC CONFIRMADO). Reusa o payload de cadastro (perfil server-side)."""

    escopos = serializers.ListField(child=CadastrarEscopoSerializer(), allow_empty=False)
