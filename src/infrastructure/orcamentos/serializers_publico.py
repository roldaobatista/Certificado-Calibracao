"""Serializers do endpoint PÚBLICO de orçamento (Onda 2e — T-ORC-038).

ISOLADO de `serializers.py` para a allowlist anti-vazamento ficar num único lugar
auditável (ADV-ORC-09 / INV-ORC-MARGEM-OFF). O serializer público NUNCA expõe
margem, custo, comissão, semáforo, `preco_resolvido`, observações internas, nem PII
do cliente — só o que o cliente final precisa para decidir: número, validade, itens
(descrição/quantidade/preço/total), total a pagar, condições e ressalvas (cl. 7.1.1-d).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento

# Allowlist canônica de campos do ItemOrcamento expostos publicamente.
# Adicionar campo aqui exige revisão (anti-vazamento ADV-ORC-09).
_ITEM_CAMPOS_PUBLICOS = ("descricao", "quantidade", "preco_unitario", "total")


class AprovarPublicoSerializer(serializers.Serializer):
    """Entrada do POST `{token}/aprovar` (aceite rico LGPD — ADV-ORC-04 / D-ORC-7).

    `aceite_texto` = texto do termo que o cliente VIU (hasheado server-side — prova
    do consentido). `ressalvas_confirmadas` obrigatório (=True) quando a análise
    crítica retornar `com_ressalva` com severidade média (cl. 7.1.1-d).
    """

    nome_aprovador = serializers.CharField(max_length=200, min_length=2)
    email_aprovador = serializers.EmailField(max_length=200)
    aceite_versao_termo = serializers.CharField(max_length=40)
    aceite_texto = serializers.CharField(max_length=5000, min_length=10)
    ressalvas_confirmadas = serializers.BooleanField(default=False)


def _dinheiro(d: Any) -> dict[str, Any]:
    return {"centavos": d.centavos, "moeda": d.moeda}


def _item_publico(item: ItemOrcamento) -> dict[str, Any]:
    """Item na visão do cliente — só os 4 campos da allowlist."""
    return {
        "descricao": item.descricao_snapshot,
        "quantidade": str(item.quantidade),
        "preco_unitario": _dinheiro(item.preco_final),
        "total": _dinheiro(item.total),
    }


def serializar_orcamento_publico(
    orcamento: Orcamento,
    itens: list[ItemOrcamento],
    *,
    ressalvas: list[str],
    requer_confirmacao_ressalvas: bool,
) -> dict[str, Any]:
    """Serializa o orçamento para o cliente final (allowlist estrita).

    Devolve SÓ o necessário para decidir. `ressalvas` aparece quando a análise
    crítica é `com_ressalva` (cl. 7.1.1-d); `requer_confirmacao_ressalvas` indica
    que o POST exigirá `ressalvas_confirmadas=true`.
    """
    desconto_total = Decimal(orcamento.descontos.centavos)
    return {
        "numero": orcamento.numero,
        "estado": orcamento.estado.value,
        "validade_fim": (orcamento.validade.fim.isoformat() if orcamento.validade.fim else None),
        "total": _dinheiro(orcamento.liquido),
        "tem_desconto": desconto_total > 0,
        "condicoes_pagamento": {
            "parcelas": orcamento.condicoes_pagamento.parcelas,
            "forma_pagamento": orcamento.condicoes_pagamento.forma_pagamento,
            "dias_vencimento_primeira": orcamento.condicoes_pagamento.dias_vencimento_primeira,
            "intervalo_dias": orcamento.condicoes_pagamento.intervalo_dias,
        },
        "itens": [_item_publico(i) for i in itens],
        "ressalvas": list(ressalvas),
        "requer_confirmacao_ressalvas": requer_confirmacao_ressalvas,
    }
