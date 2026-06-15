"""Testes PUROS das funcoes de calculo do dominio orcamentos — T-ORC-031 (TST-005).

Cobre `montar_item_orcamento` + `compor_totais` (`src/domain/comercial/orcamentos/
calculo.py`) DIRETAMENTE — casos de borda que o E2E PG-real nao aciona (cortesia
d=100, desconto 0, quantidade fracionaria, imposto por dentro com aliquota>0 +
comissao>0, multiplos itens, invariante liquido == bruto - descontos).

Sem Django, sem banco — funcoes puras. Origem do gap: auditor-qualidade (TST-005,
licao do `sanitizar_payload_audit`): funcao monetaria sempre exercitada com o mesmo
padrao (desconto 0/10%, params zerados) esconde bug latente.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from src.domain.comercial.orcamentos import calculo
from src.domain.comercial.orcamentos.entities import ItemOrcamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco


def _preco_resolvido(valor: str = "150.00") -> PrecoResolvido:
    return PrecoResolvido(
        item_id=uuid4(),
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=uuid4(),
        preco=Preco(Decimal(valor)),
        data_referencia=datetime(2026, 6, 14, tzinfo=UTC),
        origem_preco=OrigemPreco.MANUAL,
        composicao_resolvida=(),
    )


def _item(
    *,
    preco_final_unit: str,
    desconto_pct: str,
    preco_tabela_unit: str = "150.00",
    quantidade: str = "1",
    semaforo: str = "indisponivel",
) -> ItemOrcamento:
    pr = _preco_resolvido(preco_tabela_unit)
    return calculo.montar_item_orcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=pr.item_id,
        sequencia=1,
        preco_resolvido=pr,
        preco_final_unit=Decimal(preco_final_unit),
        desconto_pct=Decimal(desconto_pct),
        preco_tabela_unit=Decimal(preco_tabela_unit),
        quantidade=Decimal(quantidade),
        semaforo=semaforo,
        descricao_snapshot="Item teste",
        tipo_item_comercial=TipoItemComercial.OUTRO,
    )


# ---------------------------------------------------------------------------
# montar_item_orcamento
# ---------------------------------------------------------------------------


def test_montar_item_sem_desconto() -> None:
    it = _item(preco_final_unit="150.00", desconto_pct="0", quantidade="1")
    assert it.preco_final.centavos == 15000
    assert it.desconto_valor.centavos == 0
    assert it.total.centavos == 15000
    assert it.desconto_pct == Decimal("0.00")


def test_montar_item_com_desconto_reconstroi_preco_cheio() -> None:
    # preco final ja descontado = 135 (de 150 -10%). Reconstrucao: 135/(1-0.10)=150.
    it = _item(preco_final_unit="135.00", desconto_pct="10", quantidade="1")
    assert it.preco_final.centavos == 13500
    assert it.desconto_valor.centavos == 1500  # 150 - 135
    assert it.total.centavos == 13500


def test_montar_item_cortesia_d100_usa_preco_tabela() -> None:
    # Cortesia: preco_final=0; preco cheio cai no preco de tabela (sem div/0).
    it = _item(
        preco_final_unit="0.00",
        desconto_pct="100",
        preco_tabela_unit="150.00",
        quantidade="1",
    )
    assert it.preco_final.centavos == 0
    assert it.desconto_valor.centavos == 15000
    assert it.total.centavos == 0


def test_montar_item_quantidade_fracionaria() -> None:
    it = _item(preco_final_unit="10.00", desconto_pct="0", quantidade="2.5")
    assert it.total.centavos == 2500  # 10.00 * 2.5 = 25.00
    assert it.quantidade == Decimal("2.5")


# ---------------------------------------------------------------------------
# compor_totais
# ---------------------------------------------------------------------------


def test_compor_totais_multiplos_itens_imposto_por_dentro() -> None:
    item1 = _item(preco_final_unit="100.00", desconto_pct="0", quantidade="1")
    item2 = _item(preco_final_unit="200.00", desconto_pct="0", quantidade="2")
    totais = calculo.compor_totais(
        [item1, item2],
        aliquota_imposto_fracao=Decimal("0.10"),
        comissao_fracao=Decimal("0.05"),
    )
    assert totais.liquido.centavos == 50000  # 10000 + 40000
    assert totais.total_bruto.centavos == 50000  # sem desconto
    assert totais.descontos.centavos == 0
    # imposto por dentro: 10% do liquido de cada item
    assert totais.impostos.centavos == 5000
    assert totais.comissao_prevista.centavos == 2500
    # invariante central
    assert totais.liquido.centavos == totais.total_bruto.centavos - totais.descontos.centavos


def test_compor_totais_com_desconto_mantem_invariante() -> None:
    # 150 -10% = 135/un, qty 2 -> liquido 270; bruto 300; desconto 30.
    item = _item(preco_final_unit="135.00", desconto_pct="10", quantidade="2")
    totais = calculo.compor_totais(
        [item],
        aliquota_imposto_fracao=Decimal("0.10"),
        comissao_fracao=Decimal("0.00"),
    )
    assert totais.total_bruto.centavos == 30000
    assert totais.descontos.centavos == 3000
    assert totais.liquido.centavos == 27000
    assert totais.impostos.centavos == 2700
    assert totais.comissao_prevista.centavos == 0
    assert totais.liquido.centavos == totais.total_bruto.centavos - totais.descontos.centavos


def test_compor_totais_vazio() -> None:
    totais = calculo.compor_totais(
        [], aliquota_imposto_fracao=Decimal("0.10"), comissao_fracao=Decimal("0.05")
    )
    assert totais.total_bruto.centavos == 0
    assert totais.liquido.centavos == 0
    assert totais.descontos.centavos == 0
    assert totais.impostos.centavos == 0
    assert totais.comissao_prevista.centavos == 0
