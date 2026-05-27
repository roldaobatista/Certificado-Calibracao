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
    """POST /api/v1/calibracoes/recepcionar — cria Calibracao em RECEPCIONADA.

    SEG-CAL-01 (2026-05-27 — 1a passada Familia 5): `cliente_referencia_hash`
    e `cliente_key_id` REMOVIDOS do body — derivados server-side via
    `lgpd.derivar_cliente_referencia_hash/_key_id` a partir de
    (tenant_id, cliente_id). Cliente nao pode mais spoofar referencia
    de outro cliente.
    """

    origem_recepcao = serializers.ChoiceField(
        choices=["ATIVIDADE_OS", "AVULSA"],
    )
    atividade_os_id = serializers.UUIDField(required=False, allow_null=True)
    instrumento_id = serializers.UUIDField()
    snapshot_equipamento_json = serializers.JSONField()
    cliente_id = serializers.UUIDField(required=False, allow_null=True)
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
    """POST /api/v1/calibracoes/{id}/configurar — RECEPCIONADA -> CONFIGURADA.

    SEG-CAL-08 (2026-05-27): `analise_critica_pedido_inline_hash` REMOVIDO
    do body. Body envia `analise_critica_pedido_inline_texto` (texto livre
    >=10 chars OU vazio); view deriva hash server-side via
    `lgpd.derivar_hash_texto_canonicalizado`.
    """

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
    analise_critica_pedido_inline_texto = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=2000
    )
    capacidade_tecnica_confirmada_por_user_id = serializers.UUIDField(
        required=False, allow_null=True
    )


class CancelarCalibracaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/cancelar.

    SEG-CAL-07 (2026-05-27): `motivo_hash` REMOVIDO do body — derivado
    server-side a partir de `motivo_cancelamento_canonicalizado`.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    motivo_cancelamento_canonicalizado = serializers.CharField(min_length=30)


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


# =============================================================
# Leitura / LeituraCorrecao (T-CAL-124)
# =============================================================


class RegistrarLeituraSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/registrar-leitura.

    SEG-CAL-09: `executor_id_hash` derivado server-side a partir do
    `usuario_id` autenticado — NUNCA aceita no body.
    """

    ponto_calibracao = serializers.DecimalField(
        max_digits=20, decimal_places=8
    )
    numero_repeticao = serializers.IntegerField(min_value=1)
    valor_lido = serializers.DecimalField(max_digits=20, decimal_places=8)
    unidade = serializers.CharField(max_length=20, min_length=1)
    origem = serializers.ChoiceField(
        choices=["MANUAL", "INSTRUMENTO_INTEGRADO", "IMPORT_CSV"]
    )
    timestamp = serializers.DateTimeField()
    correlation_id = serializers.UUIDField()
    client_event_id = serializers.UUIDField(required=False, allow_null=True)


class CorrigirLeituraSerializer(serializers.Serializer):
    """POST /api/v1/leituras/{id}/corrigir — rasura digital cl. 7.5.

    SEG-CAL-09/SEG-CAL-08: `razao_correcao_hash` + `corretor_id_hash`
    derivados server-side. Body envia `razao_correcao_canonicalizada`
    (>=30 chars) — view hasheia + injeta hash do usuario logado.
    """

    valor_corrigido = serializers.DecimalField(
        max_digits=20, decimal_places=8
    )
    razao_correcao_canonicalizada = serializers.CharField(min_length=30)
    corrigido_em = serializers.DateTimeField()
    correlation_id = serializers.UUIDField()


class LeituraOutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    calibracao_id = serializers.UUIDField()
    ponto_calibracao = serializers.DecimalField(max_digits=20, decimal_places=8)
    numero_repeticao = serializers.IntegerField()
    valor_lido = serializers.DecimalField(max_digits=20, decimal_places=8)
    unidade = serializers.CharField()
    origem = serializers.CharField()
    timestamp = serializers.DateTimeField()
    correlation_id = serializers.UUIDField()
    idempotente = serializers.BooleanField(required=False)


class LeituraCorrecaoOutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    leitura_id = serializers.UUIDField()
    valor_original = serializers.DecimalField(max_digits=20, decimal_places=8)
    valor_corrigido = serializers.DecimalField(max_digits=20, decimal_places=8)
    corrigido_em = serializers.DateTimeField()
    correlation_id = serializers.UUIDField()
