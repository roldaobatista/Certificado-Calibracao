"""Serializers DRF M4 P4 Fase 8 (T-CAL-123..134).

Esqueleto Wave A: cobre apenas o fluxo basico de Calibracao
(recepcionar / configurar / cancelar). Demais serializers (Leitura,
OrcamentoIncerteza, NaoConformidade, Reclamacao) seguem mesmo padrao
e serao plugados quando viewsets respectivos chegarem.

INV-TENANT: serializers NUNCA aceitam tenant_id no body — vem do
contexto autenticado.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class RecepcionarCalibracaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/recepcionar — cria Calibracao em RECEPCIONADA."""

    origem_recepcao = serializers.ChoiceField(
        choices=["ATIVIDADE_OS", "AVULSA"],
    )
    atividade_os_id = serializers.UUIDField(required=False, allow_null=True)
    instrumento_id = serializers.UUIDField()
    snapshot_equipamento_json = serializers.JSONField()
    cliente_id = serializers.UUIDField(required=False, allow_null=True)
    cliente_referencia_hash = serializers.RegexField(
        regex=r"^v\d{2}\$[A-Za-z0-9+/=]+$",
        max_length=80,
    )
    cliente_key_id = serializers.CharField(max_length=64)
    tipo_acreditacao = serializers.ChoiceField(choices=["RBC", "NAO_RBC"])
    correlation_id = serializers.UUIDField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """ADR-0023: origem coerente com atividade_os_id."""
        origem = attrs.get("origem_recepcao")
        ativ = attrs.get("atividade_os_id")
        if origem == "ATIVIDADE_OS" and ativ is None:
            raise serializers.ValidationError(
                "origem=ATIVIDADE_OS exige atividade_os_id (ADR-0023)"
            )
        if origem == "AVULSA" and ativ is not None:
            raise serializers.ValidationError(
                "origem=AVULSA proibe atividade_os_id (ADR-0023)"
            )
        return attrs


class ConfigurarCalibracaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/configurar — RECEPCIONADA -> CONFIGURADA."""

    revision_esperada = serializers.IntegerField(min_value=0)
    procedimento_id = serializers.UUIDField()
    procedimento_versao_snapshot = serializers.DictField()
    regra_decisao = serializers.ChoiceField(
        choices=["ACEITACAO_SIMPLES", "BANDA_GUARDA_30", "RISCO_COMPARTILHADO"],
    )
    regra_decisao_acordada_em = serializers.DateTimeField()
    regra_decisao_acordada_documento_id = serializers.UUIDField()
    escopo_id = serializers.UUIDField(required=False, allow_null=True)
    analise_critica_pedido_id = serializers.UUIDField(
        required=False, allow_null=True
    )
    analise_critica_pedido_inline_hash = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=80
    )
    capacidade_tecnica_confirmada_por_user_id = serializers.UUIDField(
        required=False, allow_null=True
    )


class CancelarCalibracaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/cancelar."""

    revision_esperada = serializers.IntegerField(min_value=0)
    motivo_cancelamento_canonicalizado = serializers.CharField(min_length=30)
    motivo_hash = serializers.RegexField(
        regex=r"^v\d{2}\$[A-Za-z0-9+/=]+$",
        max_length=80,
    )


class CalibracaoOutSerializer(serializers.Serializer):
    """Resposta padrao — snapshot serializado.

    Wave A: campos minimos. Resposta completa eh CalibracaoVisao360
    (endpoint /api/v1/calibracoes/{id}/visao-360).
    """

    id = serializers.UUIDField()
    numero_interno = serializers.IntegerField()
    numero_exibido = serializers.CharField()
    status = serializers.CharField()
    revision = serializers.IntegerField()
    tipo_acreditacao = serializers.CharField()
    criada_em = serializers.DateTimeField()
