"""Serializers DRF — M3 OS Fase 8 (T-OS-094..104).

Serializers leves (read-only ou input puro) — view layer.
"""

from __future__ import annotations

from rest_framework import serializers


class AdicionarAtividadeRequestSerializer(serializers.Serializer):
    """Input do POST /v1/os/{os_id}/atividades/."""

    tipo = serializers.ChoiceField(
        choices=[
            "calibracao",
            "manutencao_corretiva",
            "manutencao_preventiva",
            "instalacao",
            "verificacao_inmetro",
            "vistoria",
        ]
    )
    sequencia = serializers.IntegerField(min_value=1)
    valor_unitario = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    # ADR-0082 / AC-OSME-003-1: equipamento proprio da atividade adicionada.
    # None => trigger COALESCE copia de OS.equipamento_id (compat single-equip).
    # Em OS multi-equipamento (OS.equipamento_id=NULL) DEVE vir preenchido.
    equipamento_id = serializers.UUIDField(
        required=False, allow_null=True, default=None
    )


class IniciarAtividadeRequestSerializer(serializers.Serializer):
    client_event_id = serializers.UUIDField()
    geo_lat = serializers.FloatField(required=False, allow_null=True, default=None)
    geo_long = serializers.FloatField(required=False, allow_null=True, default=None)
    geo_municipio_hash = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class ConcluirAtividadeRequestSerializer(serializers.Serializer):
    aceite_dispensado = serializers.BooleanField(default=False)


class CancelarOSRequestSerializer(serializers.Serializer):
    motivo = serializers.CharField(min_length=30, max_length=500)


class ReabrirOSRequestSerializer(serializers.Serializer):
    motivo = serializers.CharField(min_length=30, max_length=500)
    garantia_procedente = serializers.BooleanField(default=False)
    chamado_origem_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    sucessao_societaria_id = serializers.UUIDField(
        required=False, allow_null=True, default=None
    )


class TransferirTecnicoRequestSerializer(serializers.Serializer):
    novo_tecnico_id = serializers.UUIDField()
    motivo = serializers.CharField(min_length=30, max_length=500)


class ReagendarAtividadeRequestSerializer(serializers.Serializer):
    nova_agendada_para = serializers.DateTimeField()
