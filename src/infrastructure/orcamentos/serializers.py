"""Serializers REST do modulo `orcamentos` (Fatia 2 / Onda 2a).

Entrada: validacao DRF + bifurcacao tecnico/comercial (INV-ORC-EQUIP-ITEM).
Saida: `serializar_orcamento` aplica RBAC de campo — `comissao_prevista` so com
`orcamento.ver_margem` (INV-ORC-MARGEM-OFF / D-ORC-10). O item NUNCA expoe
margem/custo (o snapshot nem os persiste).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo
from src.domain.operacao.os.value_objects import TipoItemComercial

_TIPO_ATIVIDADE_ALVO_CHOICES = [t.value for t in TipoAtividadeAlvo]
_TIPO_ITEM_COMERCIAL_CHOICES = [t.value for t in TipoItemComercial]
_FORMAS_PAGAMENTO = [
    "dinheiro",
    "pix",
    "cartao_credito",
    "cartao_debito",
    "boleto",
    "transferencia",
    "cheque",
    "a_prazo",
]


class CondicoesPagamentoSerializer(serializers.Serializer):
    """VO CondicoesPagamento (D-ORC / modelo PRD)."""

    parcelas = serializers.IntegerField(min_value=1, default=1)
    forma_pagamento = serializers.ChoiceField(choices=_FORMAS_PAGAMENTO, default="pix")
    dias_vencimento_primeira = serializers.IntegerField(min_value=0, default=0)
    intervalo_dias = serializers.IntegerField(min_value=0, default=30)
    observacoes = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True, default=None
    )


class CriarOrcamentoSerializer(serializers.Serializer):
    """Entrada de `criar_orcamento` (AC-ORC-001)."""

    cliente_id = serializers.UUIDField()
    validade_dias = serializers.IntegerField(min_value=1, max_value=3650, default=30)
    condicoes_pagamento = CondicoesPagamentoSerializer(required=False)
    template_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    tabela_preco_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    observacoes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    responsavel_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    chamado_origem_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class _ItemBaseSerializer(serializers.Serializer):
    """Campos comuns de adicionar/editar item (bifurcacao INV-ORC-EQUIP-ITEM)."""

    catalogo_item_id = serializers.UUIDField()
    descricao = serializers.CharField(max_length=300)
    quantidade = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001"), default=Decimal("1")
    )
    desconto_pct = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("100"),
        default=Decimal("0"),
    )
    km = serializers.DecimalField(
        max_digits=10, decimal_places=4, min_value=Decimal("0"), default=Decimal("0")
    )
    parcelas = serializers.IntegerField(min_value=1, default=1)
    tabela_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    # Bifurcacao tecnico x comercial
    equipamento_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    tipo_atividade_alvo = serializers.ChoiceField(
        choices=_TIPO_ATIVIDADE_ALVO_CHOICES, required=False, allow_null=True, default=None
    )
    tipo_item_comercial = serializers.ChoiceField(
        choices=_TIPO_ITEM_COMERCIAL_CHOICES, required=False, allow_null=True, default=None
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        equipamento_id = attrs.get("equipamento_id")
        tipo_atividade = attrs.get("tipo_atividade_alvo")
        tipo_comercial = attrs.get("tipo_item_comercial")
        if equipamento_id is not None:
            # Item tecnico (calibracao/manutencao/...) — exige tipo_atividade_alvo,
            # nunca tipo_item_comercial (INV-ORC-EQUIP-ITEM / D-ORC-16).
            if not tipo_atividade:
                raise serializers.ValidationError(
                    {"tipo_atividade_alvo": "obrigatorio quando equipamento_id e informado."}
                )
            if tipo_comercial:
                raise serializers.ValidationError(
                    {
                        "tipo_item_comercial": "item tecnico (com equipamento) nao tem tipo comercial."
                    }
                )
        else:
            # Item comercial (deslocamento/taxa/outro) — exige tipo_item_comercial,
            # nunca tipo_atividade_alvo.
            if not tipo_comercial:
                raise serializers.ValidationError(
                    {"tipo_item_comercial": "obrigatorio quando nao ha equipamento_id."}
                )
            if tipo_atividade:
                raise serializers.ValidationError(
                    {
                        "tipo_atividade_alvo": "item comercial (sem equipamento) nao tem tipo de atividade."
                    }
                )
        return attrs


class AdicionarItemSerializer(_ItemBaseSerializer):
    """Entrada de `adicionar_item` (AC-ORC-004)."""


class EditarItemSerializer(_ItemBaseSerializer):
    """Entrada de `editar_item` (AC-ORC-004)."""


# ---------------------------------------------------------------------------
# Saida
# ---------------------------------------------------------------------------


def _dinheiro(d: Any) -> dict[str, Any]:
    return {"centavos": d.centavos, "moeda": d.moeda}


def serializar_item(item: ItemOrcamento) -> dict[str, Any]:
    """Serializa um item. NUNCA expoe margem/custo (snapshot nem os tem)."""
    return {
        "id": str(item.id),
        "versao_id": str(item.versao_id),
        "catalogo_item_id": str(item.catalogo_item_id),
        "sequencia": item.sequencia,
        "descricao_snapshot": item.descricao_snapshot,
        "quantidade": str(item.quantidade),
        "preco_final": _dinheiro(item.preco_final),
        "desconto_pct": str(item.desconto_pct),
        "desconto_valor": _dinheiro(item.desconto_valor),
        "total": _dinheiro(item.total),
        "semaforo": item.semaforo,
        "equipamento_id": str(item.equipamento_id) if item.equipamento_id else None,
        "tipo_atividade_alvo": (
            item.tipo_atividade_alvo.value if item.tipo_atividade_alvo else None
        ),
        "tipo_item_comercial": (
            item.tipo_item_comercial.value if item.tipo_item_comercial else None
        ),
    }


def serializar_orcamento(
    orcamento: Orcamento,
    *,
    pode_ver_margem: bool,
    itens: list[ItemOrcamento] | None = None,
) -> dict[str, Any]:
    """Serializa o agregado. `comissao_prevista` so com `orcamento.ver_margem`."""
    corpo: dict[str, Any] = {
        "id": str(orcamento.id),
        "numero": orcamento.numero,
        "estado": orcamento.estado.value,
        "cliente_atual_id": (
            str(orcamento.cliente_atual_id) if orcamento.cliente_atual_id else None
        ),
        "validade_inicio": orcamento.validade.inicio.isoformat(),
        "validade_fim": (orcamento.validade.fim.isoformat() if orcamento.validade.fim else None),
        "total_bruto": _dinheiro(orcamento.total_bruto),
        "descontos": _dinheiro(orcamento.descontos),
        "impostos": _dinheiro(orcamento.impostos),
        "liquido": _dinheiro(orcamento.liquido),
        "condicoes_pagamento": {
            "parcelas": orcamento.condicoes_pagamento.parcelas,
            "forma_pagamento": orcamento.condicoes_pagamento.forma_pagamento,
            "dias_vencimento_primeira": orcamento.condicoes_pagamento.dias_vencimento_primeira,
            "intervalo_dias": orcamento.condicoes_pagamento.intervalo_dias,
            "observacoes": orcamento.condicoes_pagamento.observacoes,
        },
        "template_id": str(orcamento.template_id) if orcamento.template_id else None,
        "tabela_preco_id": (str(orcamento.tabela_preco_id) if orcamento.tabela_preco_id else None),
        "observacoes": orcamento.observacoes,
        "responsavel_id": str(orcamento.responsavel_id) if orcamento.responsavel_id else None,
        "criado_em": orcamento.criado_em.isoformat(),
    }
    if pode_ver_margem:
        corpo["comissao_prevista"] = _dinheiro(orcamento.comissao_prevista)
    if itens is not None:
        corpo["itens"] = [serializar_item(i) for i in itens]
    return corpo
