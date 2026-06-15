"""Conversao de preco calculado -> item + composicao de totais — T-ORC-031.

Funcoes PURAS (sem Django, sem precificacao): a fronteira de aplicacao (use case
`adicionar_item`) extrai os primitivos do `ItemCalculado` (motor de precificacao)
e chama `montar_item_orcamento` aqui. Mantem o dominio `orcamentos` desacoplado
do dominio `precificacao` (so depende de `shared` + `pps` + `operacao.os`, como
`entities.py` ja faz).

Semantica monetaria (decisao de implementacao Onda 2a — REGRA #0.5; revisavel no
P9 auditor-produto):
  - `preco_final_unit` (do motor) = preco unitario que o cliente paga, JA com
    desconto e juros de parcelamento aplicados. Imposto e "por dentro" (embutido
    no preco, nunca somado por cima) — molde do motor `precificacao` (a margem
    liquida ja desconta imposto/comissao do preco). Logo `liquido == total_bruto -
    descontos`; `impostos`/`comissao_prevista` sao parcelas INFORMATIVAS contidas
    no liquido.
  - `preco_cheio_unit` (antes do desconto) reconstruido de `preco_final/(1-d)`
    (exato relativo ao preco pos-regra). Cortesia (d=100, preco_final=0) nao
    permite reconstrucao -> usa `preco_tabela_unit` como melhor proxy disponivel.
  - `total_bruto = SUM(preco_cheio*qty)`, `descontos = bruto-liquido`,
    `liquido = SUM(preco_final*qty)`, `impostos = SUM(liquido*aliquota)`,
    `comissao_prevista = SUM(liquido*comissao)`.

INV-ORC-MARGEM-OFF: o `ItemOrcamento` carimba SO `PrecoResolvido` + preco_final +
desconto + semaforo. NUNCA margem/custo/comissao por item (a comissao vive so no
agregado, visivel com `orcamento.ver_margem`).

Refs: spec §4; D-ORC-1/10; INV-ORC-MARGEM-OFF; AC-ORC-001/004.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
from uuid import UUID

from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.shared.value_objects import Dinheiro

_ESCALA = Decimal("0.01")
_UM = Decimal("1")
_ZERO = Decimal("0")
_CEM = Decimal("100")
_INT = Decimal("1")


def _reais_para_centavos(v: Decimal) -> int:
    """Converte um valor em reais (Decimal) para centavos (int), HALF_EVEN."""
    return int((v * _CEM).quantize(_INT, rounding=ROUND_HALF_EVEN))


def _mul_centavos(centavos: int, fator: Decimal) -> int:
    """Multiplica um valor em centavos (int) por uma fracao/quantidade (Decimal).

    Resultado arredondado para centavos inteiros (HALF_EVEN). Usado para imposto/
    comissao por dentro (fator = fracao) e para totais de linha (fator = quantidade).
    """
    return int((Decimal(centavos) * fator).quantize(_INT, rounding=ROUND_HALF_EVEN))


def montar_item_orcamento(
    *,
    id: UUID,
    versao_id: UUID,
    tenant_id: UUID,
    catalogo_item_id: UUID,
    sequencia: int,
    preco_resolvido: PrecoResolvido,
    preco_final_unit: Decimal,
    desconto_pct: Decimal,
    preco_tabela_unit: Decimal,
    quantidade: Decimal,
    semaforo: str,
    descricao_snapshot: str,
    moeda: str = "BRL",
    equipamento_id: UUID | None = None,
    tipo_atividade_alvo: TipoAtividadeAlvo | None = None,
    tipo_item_comercial: TipoItemComercial | None = None,
) -> ItemOrcamento:
    """Monta um ``ItemOrcamento`` a partir do preco calculado pelo motor.

    Args:
      preco_resolvido: snapshot probatorio (carimbo D-ORC-1 / INV-ORC-PRECO-001).
      preco_final_unit: preco unitario final (reais) do ``ItemCalculado`` — ja com
        desconto e juros; imposto por dentro.
      desconto_pct: percentual de desconto 0..100 (do ``ItemCalculado.desconto_pct``).
      preco_tabela_unit: preco de tabela unitario (``PrecoResolvido.preco.valor``) —
        usado como base do "preco cheio" apenas no caso de cortesia (d=100).
      quantidade: quantidade (pode ser fracionaria).
      semaforo: ``Semaforo.value`` (verde|amarelo|vermelho|indisponivel).

    Returns:
      ``ItemOrcamento`` frozen (bifurcacao equip/comercial validada no ``__post_init__``).
    """
    if desconto_pct >= _CEM:
        # Cortesia: preco_final=0 impede reconstrucao /(1-d); usa preco de tabela.
        preco_cheio_unit = preco_tabela_unit
    elif desconto_pct <= _ZERO:
        preco_cheio_unit = preco_final_unit
    else:
        desc_frac = desconto_pct / _CEM
        preco_cheio_unit = (preco_final_unit / (_UM - desc_frac)).quantize(
            _ESCALA, rounding=ROUND_HALF_EVEN
        )

    desconto_valor_unit = preco_cheio_unit - preco_final_unit
    if desconto_valor_unit < _ZERO:
        desconto_valor_unit = _ZERO

    total_linha = (preco_final_unit * quantidade).quantize(_ESCALA, rounding=ROUND_HALF_EVEN)

    return ItemOrcamento(
        id=id,
        versao_id=versao_id,
        tenant_id=tenant_id,
        catalogo_item_id=catalogo_item_id,
        sequencia=sequencia,
        preco_resolvido=preco_resolvido,
        preco_final=Dinheiro(_reais_para_centavos(preco_final_unit), moeda),
        desconto_pct=desconto_pct.quantize(_ESCALA, rounding=ROUND_HALF_EVEN),
        desconto_valor=Dinheiro(_reais_para_centavos(desconto_valor_unit), moeda),
        quantidade=quantidade,
        total=Dinheiro(_reais_para_centavos(total_linha), moeda),
        semaforo=semaforo,
        descricao_snapshot=descricao_snapshot,
        equipamento_id=equipamento_id,
        tipo_atividade_alvo=tipo_atividade_alvo,
        tipo_item_comercial=tipo_item_comercial,
    )


@dataclass(frozen=True, slots=True)
class TotaisOrcamento:
    """Totais agregados do orcamento (todos ``Dinheiro`` na mesma moeda)."""

    total_bruto: Dinheiro
    descontos: Dinheiro
    impostos: Dinheiro
    liquido: Dinheiro
    comissao_prevista: Dinheiro


def compor_totais(
    itens: Sequence[ItemOrcamento],
    *,
    aliquota_imposto_fracao: Decimal,
    comissao_fracao: Decimal,
    moeda: str = "BRL",
) -> TotaisOrcamento:
    """Compoe os 5 totais do orcamento a partir dos itens persistidos.

    ``liquido == total_bruto - descontos`` por construcao (imposto por dentro).
    ``impostos``/``comissao_prevista`` sao parcelas informativas contidas no liquido.

    Args:
      itens: itens da versao corrente (cada um ja com preco_final/desconto/total).
      aliquota_imposto_fracao: fracao de imposto vigente (ex: Decimal("0.10")).
      comissao_fracao: fracao de comissao prevista (ex: Decimal("0.05")).
      moeda: ISO 4217 (MVP-1 BRL).
    """
    bruto_c = 0
    descontos_c = 0
    liquido_c = 0
    impostos_c = 0
    comissao_c = 0

    for it in itens:
        liquido_item_c = it.total.centavos
        gross_unit_c = it.preco_final.centavos + it.desconto_valor.centavos
        gross_total_c = _mul_centavos(gross_unit_c, it.quantidade)
        desconto_item_c = gross_total_c - liquido_item_c
        if desconto_item_c < 0:
            desconto_item_c = 0

        bruto_c += gross_total_c
        liquido_c += liquido_item_c
        descontos_c += desconto_item_c
        impostos_c += _mul_centavos(liquido_item_c, aliquota_imposto_fracao)
        comissao_c += _mul_centavos(liquido_item_c, comissao_fracao)

    return TotaisOrcamento(
        total_bruto=Dinheiro(bruto_c, moeda),
        descontos=Dinheiro(descontos_c, moeda),
        impostos=Dinheiro(impostos_c, moeda),
        liquido=Dinheiro(liquido_c, moeda),
        comissao_prevista=Dinheiro(comissao_c, moeda),
    )


def _dinheiro_dict(d: Dinheiro) -> dict[str, Any]:
    return {"centavos": d.centavos, "moeda": d.moeda}


def montar_snapshot_versao(orcamento: Orcamento, itens: Sequence[ItemOrcamento]) -> dict[str, Any]:
    """Foto JSON-safe da versão para congelar ao enviar (D-ORC-8 / Padrão B).

    Captura o estado comercial no momento do envio: itens (sem margem/custo —
    INV-ORC-MARGEM-OFF), condições de pagamento e totais. NÃO embute o
    `PrecoResolvido` completo (já persistido por item); comparação V2/V3 = Wave B.
    Resultado é um dict não-vazio (o trigger WORM exige `{}` -> conteúdo one-shot).
    """
    return {
        "numero": orcamento.numero,
        "validade_inicio": orcamento.validade.inicio.isoformat(),
        "validade_fim": (orcamento.validade.fim.isoformat() if orcamento.validade.fim else None),
        "condicoes_pagamento": {
            "parcelas": orcamento.condicoes_pagamento.parcelas,
            "forma_pagamento": orcamento.condicoes_pagamento.forma_pagamento,
            "dias_vencimento_primeira": orcamento.condicoes_pagamento.dias_vencimento_primeira,
            "intervalo_dias": orcamento.condicoes_pagamento.intervalo_dias,
            "observacoes": orcamento.condicoes_pagamento.observacoes,
        },
        "totais": {
            "total_bruto": _dinheiro_dict(orcamento.total_bruto),
            "descontos": _dinheiro_dict(orcamento.descontos),
            "impostos": _dinheiro_dict(orcamento.impostos),
            "liquido": _dinheiro_dict(orcamento.liquido),
        },
        "itens": [
            {
                "sequencia": it.sequencia,
                "catalogo_item_id": str(it.catalogo_item_id),
                "descricao": it.descricao_snapshot,
                "quantidade": str(it.quantidade),
                "preco_final": _dinheiro_dict(it.preco_final),
                "desconto_pct": str(it.desconto_pct),
                "desconto_valor": _dinheiro_dict(it.desconto_valor),
                "total": _dinheiro_dict(it.total),
                "semaforo": it.semaforo,
                "equipamento_id": str(it.equipamento_id) if it.equipamento_id else None,
                "tipo_atividade_alvo": (
                    it.tipo_atividade_alvo.value if it.tipo_atividade_alvo else None
                ),
                "tipo_item_comercial": (
                    it.tipo_item_comercial.value if it.tipo_item_comercial else None
                ),
            }
            for it in itens
        ],
    }
