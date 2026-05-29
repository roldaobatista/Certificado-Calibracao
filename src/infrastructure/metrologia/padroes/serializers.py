"""Serializers DRF do M5 padroes (T-PAD-040).

Validam o payload das actions do PadraoViewSet. PII NUNCA entra por aqui:
`responsavel_envio`/`aprovado_rt` user hashes sao derivados server-side na view
(derivar_user_id_hash — ADR-0064); `localizacao_lab`/`cert_externo_storage_key`
sao texto anti-PII / chave opaca. Os VOs (grandezas/faixas/incertezas) chegam no
shape canonico e a view os converte via mappers + dominio.
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)

_SUBTIPO_CHOICES = [e.value for e in SubtipoPadrao]
_VINCULACAO_CHOICES = [e.value for e in VinculacaoCadeia]
_CLASSE_CHOICES = [e.value for e in ClassePadrao]
_STATUS_RECAL_CHOICES = [e.value for e in StatusRecal]


class _FaixaSerializer(serializers.Serializer):
    inferior = serializers.DecimalField(max_digits=30, decimal_places=12)
    superior = serializers.DecimalField(max_digits=30, decimal_places=12)
    unidade = serializers.CharField(max_length=10)


class _IncertezaSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=30, decimal_places=12)
    fator_k = serializers.DecimalField(max_digits=10, decimal_places=4)
    nivel_confianca = serializers.DecimalField(max_digits=6, decimal_places=4)
    unidade = serializers.CharField(max_length=10)
    graus_liberdade_efetivos = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )


class CadastrarPadraoSerializer(serializers.Serializer):
    numero_serie = serializers.CharField(max_length=120)
    fabricante = serializers.CharField(max_length=120)
    modelo = serializers.CharField(max_length=120)
    subtipo = serializers.ChoiceField(choices=_SUBTIPO_CHOICES)
    grandezas = serializers.ListField(
        child=serializers.CharField(max_length=40), allow_empty=False
    )
    faixas = _FaixaSerializer(many=True, allow_empty=False)
    incertezas_certificado = _IncertezaSerializer(many=True, allow_empty=False)
    vinculacao = serializers.ChoiceField(choices=_VINCULACAO_CHOICES)
    classe = serializers.ChoiceField(choices=_CLASSE_CHOICES)
    cert_externo_storage_key = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    validade_certificado_rastreabilidade = serializers.DateField()
    proximo_recal = serializers.DateField()
    intervalo_recal_meses = serializers.IntegerField(min_value=1)
    intervalo_vi_meses = serializers.IntegerField(min_value=1)
    criterio_intervalo = serializers.CharField(max_length=2000)
    descricao = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    localizacao_lab = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    correlation_id = serializers.UUIDField()


class RecalEnvioSerializer(serializers.Serializer):
    lab_externo = serializers.CharField(max_length=200)
    numero_protocolo_lab_externo = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )


class RecalRetornoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=_STATUS_RECAL_CHOICES)
    incertezas_novas = _IncertezaSerializer(many=True, required=False, default=list)
    validade_nova = serializers.DateField(required=False, allow_null=True)
    valor_convencional_novo = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    cert_externo_novo_storage_key = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )


class AprovarRecalSerializer(serializers.Serializer):
    aprovado = serializers.BooleanField()
    proximo_recal_novo = serializers.DateField(required=False, allow_null=True)


class BaixarPadraoSerializer(serializers.Serializer):
    sucatar = serializers.BooleanField(default=False)
    motivo_revogacao = serializers.CharField(max_length=2000, min_length=10)


class RevogarRastreabilidadeSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=2000, min_length=10)


class CriarVinculoAuxiliarSerializer(serializers.Serializer):
    """US-PAD-007-4 / cl. 6.4.5 — vincula auxiliar ao principal (pk da URL).

    `padrao_principal_id` vem do pk da rota; aqui só o auxiliar + a grandeza de
    influência (string canônica → Grandeza no use case). Sem PII.
    """

    padrao_auxiliar_id = serializers.UUIDField()
    grandeza_influencia = serializers.CharField(max_length=40)
    correlation_id = serializers.UUIDField()
