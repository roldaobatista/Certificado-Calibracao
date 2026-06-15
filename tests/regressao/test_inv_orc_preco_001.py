"""INV-ORC-PRECO-001 — snapshot de preço imutável, não retroage (T-ORC-061 / P9 conserto).

Invariante de abertura da família INV-ORC-* (REGRAS-INEGOCIAVEIS.md seção ## INV-ORC-*):
o `ItemOrcamento` carimba `PrecoResolvido` na criação e esse carimbo é IMUTÁVEL — não
retroage quando o preço de origem (catálogo/tabela) muda depois (herda INV-026 / ADR-0083).

Achado P9 (auditor-qualidade, MÉDIO): a barreira existe no código (`ItemOrcamento` e
`PrecoResolvido` são `@dataclass(frozen=True)`), mas a invariante não tinha teste citando
o ID (TST-004). Este arquivo fecha o gap. Teste PURO (sem banco).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.comercial.orcamentos.entities import ItemOrcamento
from src.domain.comercial.orcamentos.enums import TipoAtividadeAlvo
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import Dinheiro


def _preco_resolvido(valor: str, *, item_id, tabela_id) -> PrecoResolvido:
    return PrecoResolvido(
        item_id=item_id,
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=tabela_id,
        preco=Preco(Decimal(valor)),
        data_referencia=datetime(2026, 1, 1, tzinfo=UTC),
        origem_preco=OrigemPreco.MANUAL,
    )


def _item(preco_resolvido: PrecoResolvido, *, preco_final_centavos: int) -> ItemOrcamento:
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=preco_resolvido.item_id,
        sequencia=1,
        preco_resolvido=preco_resolvido,
        preco_final=Dinheiro(preco_final_centavos),
        desconto_pct=Decimal("0"),
        desconto_valor=Dinheiro(0),
        quantidade=Decimal("1"),
        total=Dinheiro(preco_final_centavos),
        semaforo="verde",
        descricao_snapshot="Calibracao balanca 30kg",
        equipamento_id=uuid4(),
        tipo_atividade_alvo=TipoAtividadeAlvo.CALIBRACAO,
        grandeza_solicitada="massa",
        faixa_solicitada_min=Decimal("0"),
        faixa_solicitada_max=Decimal("30"),
        unidade_solicitada="kg",
    )


def test_inv_orc_preco_001_item_orcamento_frozen_nao_muta() -> None:
    """INV-ORC-PRECO-001: `ItemOrcamento` é frozen — atribuição direta é proibida.

    Usa `setattr` (não atribuição estática) porque o ponto é provar a barreira de
    RUNTIME (`FrozenInstanceError`), não escapar do type-checker.
    """
    item_id, tabela_id = uuid4(), uuid4()
    item = _item(_preco_resolvido("150.00", item_id=item_id, tabela_id=tabela_id), preco_final_centavos=15000)

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(item, "preco_final", Dinheiro(99999))
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(item, "preco_resolvido", _preco_resolvido("999.00", item_id=item_id, tabela_id=tabela_id))


def test_inv_orc_preco_001_preco_resolvido_carimbo_frozen() -> None:
    """INV-ORC-PRECO-001: o carimbo `PrecoResolvido` é frozen (não reescrevível)."""
    pr = _preco_resolvido("150.00", item_id=uuid4(), tabela_id=uuid4())
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(pr, "preco", Preco(Decimal("999.00")))


def test_inv_orc_preco_001_snapshot_nao_retroage_quando_preco_fonte_muda() -> None:
    """INV-ORC-PRECO-001 / INV-026: mudança posterior no preço de origem não retroage.

    O item carimba `PrecoResolvido` a R$150,00. Depois, o catálogo/tabela passa a
    resolver R$300,00 para o MESMO item (novo `PrecoResolvido`). O snapshot gravado no
    `ItemOrcamento` permanece R$150,00 — o preço aprovado não muda sob os pés do cliente.
    """
    item_id, tabela_id = uuid4(), uuid4()
    carimbo_original = _preco_resolvido("150.00", item_id=item_id, tabela_id=tabela_id)
    item = _item(carimbo_original, preco_final_centavos=15000)

    # Origem muda depois: novo PrecoResolvido a 300,00 para o mesmo item do catálogo.
    preco_fonte_novo = _preco_resolvido("300.00", item_id=item_id, tabela_id=tabela_id)
    assert preco_fonte_novo.preco.valor == Decimal("300.00")  # a fonte de fato mudou

    # O snapshot do item NÃO acompanha a mudança (frozen + valor independente da fonte).
    assert item.preco_resolvido.preco.valor == Decimal("150.00")
    assert item.preco_resolvido is carimbo_original
    assert item.preco_final == Dinheiro(15000)
    assert item.total == Dinheiro(15000)
