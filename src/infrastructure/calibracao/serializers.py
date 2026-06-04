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

from src.domain.metrologia.calibracao.enums import (
    DistribuicaoIncerteza,
    FormulaCalculoComponente,
    LeiEscalonamento,
    TipoOrigemComponente,
)


def _choices(enum_cls: type) -> list[str]:
    """Lista de `.value` do enum — choices DRY (sem hardcode duplicado)."""
    return [membro.value for membro in enum_cls]


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
    # Faixa calibrada declarada pelo RT (ADR-0076). Obrigatoria em RBC (use case
    # valida); opcional NAO_RBC. Validacao fina (vocabulario/unidade/min<max) no
    # use case via VOs Grandeza/FaixaMedicao.
    grandeza_calibrada = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=30
    )
    faixa_calibrada_min = serializers.DecimalField(
        required=False, allow_null=True, max_digits=30, decimal_places=12
    )
    faixa_calibrada_max = serializers.DecimalField(
        required=False, allow_null=True, max_digits=30, decimal_places=12
    )
    unidade_calibrada = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=10
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


# =============================================================
# Revisao / 2a Conferencia (T-CAL-126 + T-CAL-127)
# =============================================================


_CHAVES_SNAPSHOT_COMPETENCIA = {
    "grandeza",
    "faixa_min",
    "faixa_max",
    "vigencia_inicio",
    "vigencia_fim",
    "rt_competencia_id",
}


def _validar_snapshot_competencia(valor: dict) -> dict:
    """Wave A interim: cliente envia o snapshot.

    SEG-CAL-10 GATE Wave A: server-side deve derivar de
    RTCompetencia consultando (rt_id, grandeza, faixa, data atual).
    Por enquanto o serializer valida a SHAPE (chaves obrigatorias) e
    o use case re-valida no `__post_init__`. Quando GATE-CAL-10 fechar,
    serializer passara a IGNORAR snapshot enviado e view buscara
    RTCompetencia.
    """
    if not isinstance(valor, dict):
        raise serializers.ValidationError(
            "snapshot_competencia precisa ser objeto JSON"
        )
    faltando = _CHAVES_SNAPSHOT_COMPETENCIA - set(valor.keys())
    if faltando:
        raise serializers.ValidationError(
            f"snapshot_competencia sem chaves obrigatorias {sorted(faltando)} "
            "(AC-CAL-007-5 + AC-CAL-008-4)"
        )
    return valor


class AprovarRevisaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/aprovar-revisao — US-CAL-007.

    SEG-CAL-09: `revisor_id` NAO aceito no body — vem do usuario logado.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    snapshot_competencia_revisor_json = serializers.DictField()
    excecao_motivo = serializers.CharField(
        required=False, allow_null=True, allow_blank=False, max_length=80
    )

    def validate_snapshot_competencia_revisor_json(self, valor: dict) -> dict:
        return _validar_snapshot_competencia(valor)


class RejeitarRevisaoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/rejeitar-revisao — US-CAL-007 caminho B."""

    revision_esperada = serializers.IntegerField(min_value=0)
    motivo_rejeicao_canonicalizado = serializers.CharField(min_length=30)


class Aprovar2aConferenciaSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/aprovar-2a-conferencia — US-CAL-008.

    SEG-CAL-09: `conferente_id` NAO aceito no body — vem do usuario logado.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    snapshot_competencia_conferente_json = serializers.DictField()
    excecao_motivo = serializers.CharField(
        required=False, allow_null=True, allow_blank=False, max_length=80
    )
    excecao_2a_conf_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_snapshot_competencia_conferente_json(self, valor: dict) -> dict:
        return _validar_snapshot_competencia(valor)


# =============================================================
# Nao-Conformidade (T-CAL-128 — abrir + fechar)
# =============================================================


class AbrirNCSerializer(serializers.Serializer):
    """POST /api/v1/nao-conformidades/abrir — US-CAL-013 marcar-nc.

    SEG-CAL-09: `descricao_hash` + `responsavel_acao_user_id` +
    `responsavel_acao_user_id_hash` derivados server-side. Body envia
    descricao_canonicalizada (>=30 chars) + origem (calibracao_id XOR
    origem_proficiencia_id) + correlation_id.
    """

    calibracao_id = serializers.UUIDField(required=False, allow_null=True)
    origem_proficiencia_id = serializers.UUIDField(
        required=False, allow_null=True
    )
    descricao_canonicalizada = serializers.CharField(min_length=30)
    correlation_id = serializers.UUIDField()

    def validate(self, attrs: dict) -> dict:
        cal = attrs.get("calibracao_id")
        prof = attrs.get("origem_proficiencia_id")
        if (cal is None) == (prof is None):
            raise serializers.ValidationError(
                "origem XOR — exatamente UMA de "
                "{calibracao_id, origem_proficiencia_id} deve ser fornecida"
            )
        return attrs


class FecharNCSerializer(serializers.Serializer):
    """POST /api/v1/nao-conformidades/{id}/fechar — US-CAL-014 resolver-nc.

    Sem campos no body — body opcional. Use case `fechar` consome apenas
    nc_id; EFICACIA_VERIFICADA -> FECHADA.
    """

    correlation_id = serializers.UUIDField(required=False)


# =============================================================
# ReclamacaoCalibracao (T-CAL-132 — abrir + atribuir-rt + responder)
# =============================================================


class AbrirReclamacaoSerializer(serializers.Serializer):
    """POST /api/v1/reclamacoes/abrir — US-CAL-018.

    SEG-CAL-01-style: `cliente_referencia_hash` + `relato_hash` derivados
    server-side a partir de (cliente_id, tenant_id) e relato.
    SEG-CAL-11 GATE Wave A M5: `certificado_emitido_em` ainda aceito do
    body; deve passar a ser buscado em Certificado quando M5 plugar.
    """

    calibracao_id = serializers.UUIDField()
    certificado_id = serializers.UUIDField()
    certificado_emitido_em = serializers.DateTimeField()
    cliente_id = serializers.UUIDField()
    relato_canonicalizado = serializers.CharField(min_length=100)
    prazo_resposta_dia_util = serializers.IntegerField(
        min_value=1, default=15
    )
    correlation_id = serializers.UUIDField()


class AtribuirRTReclamacaoSerializer(serializers.Serializer):
    """POST /api/v1/reclamacoes/{id}/atribuir-rt — US-CAL-018 AC-018-2.

    SEG-CAL-09: `rt_atribuido_user_id_hash` derivado do usuario logado.
    `revisor_original_id_hash` + `conferente_original_id_hash` derivados
    server-side a partir da Calibracao original (view fetcha).
    """

    permitir_mesmo_rt_excecao = serializers.BooleanField(default=False)


class ResponderReclamacaoSerializer(serializers.Serializer):
    """POST /api/v1/reclamacoes/{id}/responder — US-CAL-018 AC-018-4.

    SEG-CAL-09 style: `resposta_hash` derivado server-side.
    """

    resposta_canonicalizada = serializers.CharField(min_length=100)
    decisao = serializers.ChoiceField(
        choices=[
            "IMPROCEDENTE",
            "PROCEDENTE_RETRABALHO",
            "PROCEDENTE_RECALL",
        ]
    )
    respondida_em = serializers.DateTimeField()


# =============================================================
# Subcontratacao ISO 17025 cl. 6.6 (T-CAL-129 — US-CAL-017)
# =============================================================


class SubcontratarSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/subcontratar — CONFIGURADA -> AGUARDANDO.

    SEG-CAL-07 style: `motivo_hash` derivado server-side a partir de
    `motivo_canonicalizado` (>=30 chars + anti-PII + NFC). assinatura_modo
    TOUCH exige declaracao (AC-CAL-017-7 + Lei 14.063 art. 4o);
    eh_pais_estrangeiro exige DPA (AC-CAL-017-8 + LGPD art. 33) — use case
    re-valida e levanta excecao especifica que a view traduz pra 412.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    subcontratado_id = serializers.UUIDField()
    aceite_subcontratacao_id = serializers.UUIDField()
    motivo_canonicalizado = serializers.CharField(min_length=30)
    eh_pais_estrangeiro = serializers.BooleanField(default=False)
    dpa_clausulas_internacionais_id = serializers.UUIDField(
        required=False, allow_null=True
    )
    assinatura_modo = serializers.ChoiceField(
        choices=["A3", "TOUCH"], default="A3"
    )
    declaracao_aceite_touch_alto_risco_id = serializers.UUIDField(
        required=False, allow_null=True
    )


class RegistrarRecebimentoSubcontratadoSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/registrar-recebimento-subcontratado.

    SEG-CAL-04: `recebedor_user_id` NAO aceito no body — eh o usuario logado
    (actor do contexto auth). O use case enforce `recebedor == actor` (anti
    spoofing) E `recebedor != executor` (separacao de funcoes cl. 6.2.5 —
    INV-CAL-FRAUDE-RECEB-001). As chaves obrigatorias do snapshot do cert
    externo (AC-CAL-017-3) sao validadas no `__post_init__` do use case.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    certificado_subcontratado_snapshot_json = serializers.JSONField()


# =============================================================
# OrcamentoIncerteza (T-CAL-125 — calcular-incerteza + avaliar-conformidade)
# =============================================================


class AvaliarConformidadeSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/avaliar-conformidade — US-CAL-006.

    Regra de decisao ISO 17025 cl. 7.8.6 + ILAC G8. `regra_decisao` ja vem
    cravada da configuracao (nao no body). Decimais como string p/ precisao.
    """

    revision_esperada = serializers.IntegerField(min_value=0)
    valor_medido = serializers.DecimalField(max_digits=30, decimal_places=12)
    U_expandida = serializers.DecimalField(
        max_digits=30, decimal_places=12, min_value=0
    )
    k = serializers.DecimalField(
        max_digits=10, decimal_places=6, required=False, default="2.0"
    )
    lsl = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    usl = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    correlation_id = serializers.UUIDField(required=False)


class _ComponenteIncertezaInSerializer(serializers.Serializer):
    """Um componente de entrada do orcamento GUM (proveniencia NIT-DICLA-030 §16.6).

    Tipo A exige s_x + n_amostras>=6 (INV-CAL-INC-003 — re-validado no use case).
    """

    nome = serializers.CharField(max_length=120)
    tipo = serializers.ChoiceField(choices=["A", "B"])
    u_i = serializers.DecimalField(max_digits=30, decimal_places=12, min_value=0)
    grau_liberdade = serializers.IntegerField(required=False, allow_null=True)
    tipo_origem_componente = serializers.ChoiceField(
        choices=_choices(TipoOrigemComponente)
    )
    distribuicao = serializers.ChoiceField(choices=_choices(DistribuicaoIncerteza))
    divisor = serializers.DecimalField(
        max_digits=20, decimal_places=12, min_value=0
    )
    formula_calculo = serializers.ChoiceField(
        choices=_choices(FormulaCalculoComponente)
    )
    s_x = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    n_amostras = serializers.IntegerField(required=False, allow_null=True)
    correlacao_com_componente_id = serializers.UUIDField(
        required=False, allow_null=True
    )
    coeficiente_correlacao = serializers.DecimalField(
        max_digits=10, decimal_places=6, required=False, allow_null=True
    )
    fonte_default_padrao_id = serializers.UUIDField(
        required=False, allow_null=True
    )
    lei_escalonamento = serializers.ChoiceField(
        choices=_choices(LeiEscalonamento),
        required=False,
        default=LeiEscalonamento.CONSTANTE.value,
    )


class _PontoIncertezaInSerializer(serializers.Serializer):
    """Um ponto com repeticoes — deriva Tipo A por ponto (ADR-0077, modo por-ponto).

    `s_pooled` = {s, dof} desvio combinado validado do metodo (2<=n<6 ou n=1).
    """

    ponto_calibracao = serializers.DecimalField(max_digits=30, decimal_places=12)
    valores_repeticoes = serializers.ListField(
        child=serializers.DecimalField(max_digits=30, decimal_places=12),
        allow_empty=True,
    )
    s_pooled_s = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    s_pooled_dof = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        s = attrs.get("s_pooled_s")
        dof = attrs.get("s_pooled_dof")
        if (s is None) != (dof is None):
            raise serializers.ValidationError(
                "s_pooled_s e s_pooled_dof devem vir juntos (ou ambos ausentes)"
            )
        return attrs


class CalcularOrcamentoIncertezaSerializer(serializers.Serializer):
    """POST /api/v1/calibracoes/{id}/calcular-incerteza — US-CAL-005 (GUM cl. 5).

    `perfil_tenant` NAO vem do body (ADR-0067 — perfil canonico do contexto
    server-side). Modo por-ponto (ADR-0077): `pontos` nao-vazio + `componentes`
    so Tipo B (Tipo A derivado das repeticoes) — re-validado no use case.
    `calculado_em` derivado server-side (now UTC).
    """

    componentes = _ComponenteIncertezaInSerializer(many=True, allow_empty=False)
    correlacoes = serializers.ListField(
        child=serializers.ListField(), required=False, default=list
    )
    versao_motor_calculo = serializers.CharField(max_length=120)
    documentacao_agregacao = serializers.CharField(min_length=50)
    bias_orcado = serializers.DecimalField(
        max_digits=30, decimal_places=12, required=False, allow_null=True
    )
    bias_origem = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=200
    )
    correlation_id = serializers.UUIDField()
    pontos = _PontoIncertezaInSerializer(many=True, required=False, default=list)
