"""Serializers REST da frente `precificacao` (T-PRC-034).

RBAC de campo (D-PRC-4 / INV-PRC-MARGEM-RBAC):
  Choke-point ÚNICO `filtrar_visao_margem(payload, pode_ver_margem)` aplicado
  em TODOS os serializers de saída desta frente (incl. pedido de aprovação).

  `semaforo` + `preco_minimo` → visível a qualquer papel com `precificacao.calcular`
  `margem_estimada` + `custo_estimado` → SÓ com `precificacao.ver_margem`

Segredo comercial: Parametros/Faixas NUNCA em claro em respostas de evento
(INV-PRC-SEGREDO-LOG). Nos serializers de leitura de config, os valores NUMÉRICOS
de parâmetros exigem `ver_margem` (segredo comercial).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

# ---------------------------------------------------------------------------
# Choke-point ÚNICO de RBAC de campo (D-PRC-4 / INV-PRC-MARGEM-RBAC)
# ---------------------------------------------------------------------------


def filtrar_visao_margem(payload: dict[str, Any], pode_ver_margem: bool) -> dict[str, Any]:
    """Remove campos de margem/custo se papel não tem `precificacao.ver_margem`.

    ÚNICO ponto de filtragem da frente — todo serializer de saída passa por aqui.
    Campos restritos: `margem_estimada`, `custo_estimado`.
    Campos sempre visíveis: `semaforo`, `preco_minimo` (D-PRC-4 decisão Roldão).

    Args:
      payload: dict de saída antes da filtragem.
      pode_ver_margem: True se o papel tem `precificacao.ver_margem`.

    Returns:
      Novo dict com campos restritos removidos (se não autorizado).
    """
    if pode_ver_margem:
        return payload

    campos_restritos = {"margem_estimada", "custo_estimado"}
    return {k: v for k, v in payload.items() if k not in campos_restritos}


# ---------------------------------------------------------------------------
# Serializers de entrada
# ---------------------------------------------------------------------------


class PublicarRegraSerializer(serializers.Serializer):
    """Validação de entrada para publicar_regra."""

    item_id = serializers.UUIDField()
    modo = serializers.ChoiceField(choices=["preco_fixo", "margem_alvo", "cost_plus"])
    vigencia_inicio = serializers.DateTimeField(required=False, allow_null=True, default=None)
    preco_fixo = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None
    )
    custo_manual_declarado = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None
    )
    custo_referencia_em = serializers.DateTimeField(required=False, allow_null=True, default=None)
    margem_alvo_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True, default=None
    )
    margem_piso_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True, default=None
    )


class RevogarRegraSerializer(serializers.Serializer):
    """Validação de entrada para revogar_regra."""

    motivo = serializers.CharField(min_length=10)


class ItemCestaSerializer(serializers.Serializer):
    """Item individual na cesta para calcular_precos."""

    item_id = serializers.UUIDField()
    tabela_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class CalcularPrecosSerializer(serializers.Serializer):
    """Validação de entrada para calcular_precos (D-PRC-11 — cesta)."""

    itens = ItemCestaSerializer(many=True, min_length=1)  # type: ignore[call-arg]  # DRF 3.14+ aceita min_length em many=True (stubs desatualizadas)
    desconto_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    modo_montagem = serializers.ChoiceField(choices=["componentes_checklist", "fechado_com_aviso"])
    km = serializers.DecimalField(
        max_digits=10, decimal_places=4, min_value=Decimal("0"), default=Decimal("0")
    )
    parcelas = serializers.IntegerField(min_value=1, default=1)
    cliente_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class SolicitarAprovacaoSerializer(serializers.Serializer):
    """Validação de entrada para solicitar_aprovacao."""

    desconto_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    contexto_tipo = serializers.ChoiceField(choices=["orcamento", "os", "avulso"])
    contexto_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    # fingerprint do cálculo que originou o pedido
    fingerprint_calculo = serializers.CharField(min_length=64, max_length=64)
    # eco das entradas (replay D-PRC-14)
    motor_versao = serializers.CharField(default="v1")
    faixas_versao = serializers.CharField(default="", allow_blank=True)
    parametros_versao = serializers.IntegerField(min_value=1)
    eco_km = serializers.CharField(default="0")
    eco_modo_montagem = serializers.CharField(default="fechado_com_aviso")
    eco_parcelas = serializers.CharField(default="1")
    eco_aliquota_imposto = serializers.CharField(default="0")


class DecidirAprovacaoSerializer(serializers.Serializer):
    """Validação de entrada para decidir_aprovacao."""

    estado = serializers.ChoiceField(choices=["aprovado", "negado"])
    justificativa = serializers.CharField(min_length=1, max_length=2000)
    # Recalculado pelo caller — fingerprint atual do cálculo
    fingerprint_calculo_atual = serializers.CharField(min_length=64, max_length=64)


class FaixaInputSerializer(serializers.Serializer):
    """Uma faixa no replace-all de configurar_faixas."""

    pct_de = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    pct_ate = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    alcada = serializers.ChoiceField(choices=["livre", "gerente", "dono"])


class ConfigurarFaixasSerializer(serializers.Serializer):
    """Validação de entrada para configurar_faixas (replace-all atômico)."""

    faixas = FaixaInputSerializer(many=True, min_length=1)  # type: ignore[call-arg]  # DRF 3.14+ aceita min_length em many=True (stubs desatualizadas)


class ConfigurarPerfilComposicaoSerializer(serializers.Serializer):
    """Validação de entrada para configurar_perfil_composicao."""

    item_servico_id = serializers.UUIDField()
    componentes_esperados = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
    aviso_texto = serializers.CharField(required=False, allow_blank=True, default="")


class ConfigurarParametrosSerializer(serializers.Serializer):
    """Validação de entrada para configurar_parametros."""

    custo_km = serializers.DecimalField(max_digits=10, decimal_places=4, min_value=Decimal("0"))
    taxa_parcelamento_mensal = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    pct_comissao_prevista = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    margem_alvo_default = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )
    margem_piso_default = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100")
    )


# ---------------------------------------------------------------------------
# Funções de serialização de saída (com filtrar_visao_margem aplicado)
# ---------------------------------------------------------------------------


def serializar_item_calculado(
    item: Any,
    *,
    pode_ver_margem: bool,
) -> dict[str, Any]:
    """Serializa ItemCalculado aplicando RBAC de campo (D-PRC-4).

    Usa filtrar_visao_margem para garantir que margem/custo não vazem.
    """
    payload: dict[str, Any] = {
        "item_id": str(item.preco_base.item_id),
        "preco_base": str(item.preco_base.preco.valor),
        "preco_final": str(item.preco_final),
        "desconto_pct": str(item.desconto_pct.valor),
        "semaforo": item.semaforo.value,
        "origem_custo": item.origem_custo.value,
        "sem_regra_formacao": item.sem_regra_formacao,
        "cortesia": item.cortesia,
        "preco_minimo": str(item.preco_minimo) if item.preco_minimo is not None else None,
        # Campos restritos — filtrar_visao_margem remove se não autorizado
        "margem_estimada": str(item.margem_estimada) if item.margem_estimada is not None else None,
        "custo_estimado": str(item.custo_estimado) if item.custo_estimado is not None else None,
    }
    return filtrar_visao_margem(payload, pode_ver_margem)


def serializar_resultado_calculo(
    resultado: Any,
    *,
    pode_ver_margem: bool,
) -> dict[str, Any]:
    """Serializa CalculoPrecoResultado aplicando RBAC de campo (D-PRC-4).

    Estrutura autossuficiente para replay (INV-026): inclui motor_versao,
    faixas_versao, parametros_versao, imposto_ref, eco_entradas.
    """
    return {
        "itens": [
            serializar_item_calculado(item, pode_ver_margem=pode_ver_margem)
            for item in resultado.itens
        ],
        "componentes_faltantes": [str(uid) for uid in resultado.componentes_faltantes],
        "avisos": list(resultado.avisos),
        "alcada_exigida": resultado.alcada_exigida.value,
        "motor_versao": resultado.motor_versao,
        "faixas_versao": resultado.faixas_versao or "",
        "parametros_versao": resultado.parametros_versao,
        "imposto_ref": (
            {"id": str(resultado.imposto_ref[0]), "versao": resultado.imposto_ref[1]}
            if resultado.imposto_ref is not None
            else None
        ),
        "eco_entradas": resultado.eco_entradas,
    }


def serializar_regra(regra: Any, *, pode_ver_margem: bool) -> dict[str, Any]:
    """Serializa RegraFormacaoPreco com RBAC de campo (leitura gated — D-PRC-4).

    Regra expõe custo_manual_declarado e margem_alvo_pct — exige `ver_margem`.
    `preco_fixo` é visível a qualquer papel com `configurar` (preço publicado).
    """
    base: dict[str, Any] = {
        "id": str(regra.id),
        "regra_id": str(regra.id),  # alias explícito — testes e callers usam regra_id
        "item_id": str(regra.item_id),
        "modo": regra.modo.value,
        "versao_n": regra.versao_n,
        "vigencia_inicio": regra.vigencia.inicio.isoformat(),
        "vigencia_fim": regra.vigencia.fim.isoformat() if regra.vigencia.fim else None,
        "revogado_em": regra.vigencia.revogado_em.isoformat()
        if regra.vigencia.revogado_em
        else None,
        "preco_fixo": str(regra.preco_fixo) if regra.preco_fixo is not None else None,
    }
    campos_margem: dict[str, Any] = {
        "margem_estimada": str(regra.margem_alvo_pct.valor)
        if regra.margem_alvo_pct is not None
        else None,
        "custo_estimado": str(regra.custo_manual_declarado)
        if regra.custo_manual_declarado is not None
        else None,
    }
    base.update(filtrar_visao_margem(campos_margem, pode_ver_margem))
    return base


def serializar_pedido(pedido: Any, *, pode_ver_margem: bool) -> dict[str, Any]:
    """Serializa PedidoAprovacaoDesconto com RBAC de campo (ADV-PRC-06).

    Pedido expõe pct_solicitado — visível (é o próprio dado da negociação).
    O snapshot_probatorio contém eco sem valores comerciais (D-PRC-4).
    filtrar_visao_margem aplicado para consistência com outros serializers.
    """
    payload: dict[str, Any] = {
        "id": str(pedido.id),
        "pedido_id": str(
            pedido.id
        ),  # alias explícito — corp_resumo idempotência e testes usam pedido_id
        "contexto_tipo": pedido.contexto_tipo.value,
        "contexto_id": str(pedido.contexto_id) if pedido.contexto_id else None,
        "pct_solicitado": str(pedido.pct_solicitado.valor),
        "cortesia": pedido.cortesia,
        "alcada_exigida": pedido.alcada_exigida.value,
        "estado": pedido.estado.value,
        "criado_em": pedido.criado_em.isoformat(),
        "decidido_em": pedido.decidido_em.isoformat() if pedido.decidido_em else None,
        # Campos restritos: snap do resultado tem margem/custo no eco somente se o
        # caller passou via ver_margem — o snapshot_probatorio em si não expõe valores
        # comerciais (D-PRC-4 — eco só contém refs e entradas de km/modo/parcelas)
        "margem_estimada": None,  # pedido não guarda margem; filtrar_visao_margem remove
        "custo_estimado": None,  # pedido não guarda custo; filtrar_visao_margem remove
    }
    return filtrar_visao_margem(payload, pode_ver_margem)


def serializar_faixa(faixa: Any) -> dict[str, Any]:
    """Serializa FaixaAprovacaoDesconto (config — sem margem/custo)."""
    return {
        "id": str(faixa.id),
        "pct_de": str(faixa.pct_de.valor),
        "pct_ate": str(faixa.pct_ate.valor),
        "alcada": faixa.alcada.value,
        "versao_n": faixa.versao_n,
    }


def serializar_parametros(
    params: Any,
    *,
    pode_ver_margem: bool,
) -> dict[str, Any]:
    """Serializa ParametrosPrecificacaoTenant com RBAC de campo.

    Valores numéricos são segredo comercial (INV-PRC-SEGREDO-LOG):
    NUNCA expostos sem `ver_margem`.
    """
    base: dict[str, Any] = {
        "id": str(params.id),
        "versao_n": params.versao_n,
        "criado_em": params.criado_em.isoformat(),
    }
    campos_comerciais: dict[str, Any] = {
        "margem_estimada": str(params.margem_alvo_default.valor),
        "custo_estimado": str(params.custo_km),  # custo_km é segredo comercial
    }
    base.update(filtrar_visao_margem(campos_comerciais, pode_ver_margem))
    return base
