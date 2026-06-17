"""Serializers DRF da frente agenda (Fatia 2 — T-AGE-031..038).

Regras críticas:
- NUNCA aceitar ``perfil`` nem ``regime_jornada`` do payload (INV-AG-PERFIL-001 / INV-AG-REGIME-001).
- ``aloca_em_umc``, ``tipo``, ``estado`` são campos de domínio — nunca de acesso externo direto.
- Timestamps sempre em UTC ISO-8601.
"""

from __future__ import annotations

from rest_framework import serializers

from src.domain.operacao.agenda.enums import MotivoBloqueio, RegimeJornada, TipoEvento

# Choices para campos de enum
_MOTIVO_BLOQUEIO_CHOICES = [(m.value, m.value) for m in MotivoBloqueio]
_TIPO_EVENTO_CHOICES = [(t.value, t.value) for t in TipoEvento]
_REGIME_CHOICES = [(r.value, r.value) for r in RegimeJornada]


class JanelaSerializer(serializers.Serializer):
    """Sub-serializer de janela temporal [inicia_at, termina_at)."""

    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError(
                "inicia_at deve ser anterior a termina_at (janela half-open)."
            )
        return data


class ValidarEventoSerializer(serializers.Serializer):
    """POST /agenda/validar — dry-run pré-save (US-AG-002 / R9).

    NÃO aceita ``perfil`` nem ``regime_jornada`` do payload (server-side).
    """

    tecnico_id = serializers.UUIDField()
    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()
    aloca_em_umc = serializers.BooleanField(default=True)
    acordo_coletivo_12h = serializers.BooleanField(default=False)

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError(
                "inicia_at deve ser anterior a termina_at."
            )
        return data


class CriarEventoSerializer(serializers.Serializer):
    """POST /agenda/ — criar evento de OS (US-AG-001/013).

    ``perfil_tenant`` e ``regime_jornada`` NUNCA vêm do payload.
    """

    tecnico_id = serializers.UUIDField()
    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()
    aloca_em_umc = serializers.BooleanField(default=True)
    tipo = serializers.ChoiceField(
        choices=_TIPO_EVENTO_CHOICES,
        default=TipoEvento.OS.value,
    )
    atividade_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    os_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    recorrencia_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    ocorrencia_dt = serializers.DateTimeField(required=False, allow_null=True, default=None)
    confirmar_feriado = serializers.BooleanField(default=False)
    descricao_publica = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )
    acordo_coletivo_12h = serializers.BooleanField(default=False)

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError("inicia_at deve ser anterior a termina_at.")
        if data.get("tipo") == TipoEvento.OS.value and not data.get("atividade_id"):
            raise serializers.ValidationError(
                "atividade_id é obrigatório quando tipo=os (INV-AG-ATIVIDADE-001)."
            )
        return data


class CriarBloqueioSerializer(serializers.Serializer):
    """POST /agenda/bloquear/ — criar bloqueio (US-AG-004)."""

    tecnico_id = serializers.UUIDField()
    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()
    motivo = serializers.ChoiceField(choices=_MOTIVO_BLOQUEIO_CHOICES)
    descricao_publica = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError("inicia_at deve ser anterior a termina_at.")
        return data


class MoverEventoSerializer(serializers.Serializer):
    """POST /agenda/{id}/mover/ — move janela (D-AGE-3)."""

    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()
    confirmar_feriado = serializers.BooleanField(default=False)
    acordo_coletivo_12h = serializers.BooleanField(default=False)

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError("inicia_at deve ser anterior a termina_at.")
        return data


class ReagendarEventoSerializer(serializers.Serializer):
    """POST /agenda/{id}/reagendar/ — reagenda + enfileira aviso (US-AG-008)."""

    inicia_at = serializers.DateTimeField()
    termina_at = serializers.DateTimeField()
    confirmar_feriado = serializers.BooleanField(default=False)
    acordo_coletivo_12h = serializers.BooleanField(default=False)
    motivo_reagendamento = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )
    cliente_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate(self, data: dict) -> dict:
        if data["inicia_at"] >= data["termina_at"]:
            raise serializers.ValidationError("inicia_at deve ser anterior a termina_at.")
        return data


class RegistrarNoShowSerializer(serializers.Serializer):
    """POST /agenda/{id}/no-show/ — registrar no-show (US-AG-012)."""

    cobrar_cliente = serializers.BooleanField(default=False)
    custo_estimado_centavos = serializers.IntegerField(min_value=0, default=0)
    observacao = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )
    cliente_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class ResolverConflitoSerializer(serializers.Serializer):
    """POST /agenda/resolver-conflito/ — resolução manual (US-AG-011)."""

    evento_novo_id = serializers.UUIDField()
    evento_antigo_id = serializers.UUIDField()
    opcao = serializers.ChoiceField(
        choices=["manter_novo", "manter_antigo", "reagendar_ambos"]
    )
    razao = serializers.CharField(min_length=30, max_length=5000)


class EnquadrarRegimeSerializer(serializers.Serializer):
    """POST /agenda/enquadrar-regime/ — override humano de regime (D-AGE-15 / R6).

    IA NUNCA chama este endpoint. Apenas humano (RH/gerente/advogado).
    ``regime_jornada`` aqui é o OVERRIDE que o humano está declarando —
    não vem derivado do payload de evento (campo exclusivo deste endpoint).
    """

    colaborador_id = serializers.UUIDField()
    regime = serializers.ChoiceField(choices=_REGIME_CHOICES)
    vigencia_inicio = serializers.DateField()
    vigencia_fim = serializers.DateField(required=False, allow_null=True, default=None)
    justificativa = serializers.CharField(min_length=10, max_length=5000)
