"""DRF serializers para US-EQP-007."""

from __future__ import annotations

from rest_framework import serializers

from .models import ResponsavelTecnicoTenant, RTCompetencia


class CadastrarRTPayloadSerializer(serializers.Serializer):
    """Input do POST /responsaveis-tecnicos/."""

    usuario_rt_id = serializers.UUIDField()
    nome_completo = serializers.CharField(max_length=200)
    cpf = serializers.RegexField(regex=r"^\d{11}$", max_length=11)
    formacao_academica = serializers.CharField(max_length=200)
    registro_profissional_tipo = serializers.CharField(max_length=10)
    registro_profissional_numero = serializers.CharField(max_length=40)
    registro_profissional_descricao_outro = serializers.CharField(
        max_length=80, allow_blank=True, default=""
    )
    data_inicio_vigencia = serializers.DateField()
    data_fim_vigencia = serializers.DateField(required=False, allow_null=True)


class EncerrarRTPayloadSerializer(serializers.Serializer):
    """Input do POST /responsaveis-tecnicos/{id}/encerrar/."""

    motivo = serializers.CharField(max_length=30)
    motivo_detalhe = serializers.CharField(max_length=500, allow_blank=True, default="")


class TrocarRTPayloadSerializer(CadastrarRTPayloadSerializer):
    """Input do POST /responsaveis-tecnicos/{id}/trocar/.

    Mesmos campos do cadastro do NOVO RT + motivo de encerramento do atual.
    """

    motivo_encerramento_anterior = serializers.CharField(
        max_length=30, default="substituicao"
    )


class DeclararCompetenciaPayloadSerializer(serializers.Serializer):
    """Input do POST /responsaveis-tecnicos/{id}/competencias/."""

    grandeza = serializers.CharField(max_length=80)
    declarado_em = serializers.DateField()
    vigente_ate = serializers.DateField(required=False, allow_null=True)
    carta_competencia_anexo_id = serializers.UUIDField(required=False, allow_null=True)


class ResponsavelTecnicoLeituraSerializer(serializers.ModelSerializer):
    """Output: nao expoe `cpf_hash` (defesa em profundidade — hash so na cadeia)."""

    vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = ResponsavelTecnicoTenant
        fields = [
            "id",
            "tenant",
            "usuario",
            "nome_completo_snapshot",
            "formacao_academica",
            "registro_profissional_tipo",
            "registro_profissional_numero",
            "registro_profissional_descricao_outro",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "criado_em",
            "criado_por",
            "encerrado_em",
            "encerrado_por",
            "motivo_encerramento",
            "motivo_detalhe",
            "vigente",
        ]
        read_only_fields = fields


class RTCompetenciaLeituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = RTCompetencia
        fields = [
            "id",
            "tenant",
            "rt",
            "grandeza",
            "carta_competencia_anexo_id",
            "declarado_em",
            "vigente_ate",
            "criado_em",
            "criado_por",
        ]
        read_only_fields = fields
