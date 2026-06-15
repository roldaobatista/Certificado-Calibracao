"""INV-ORC-MARGEM-OFF — margem/custo/comissão NUNCA vazam (T-ORC-054).

Margem/custo/comissão do orçamento são segredo comercial (TL-ORC-06 / ADV-ORC-09 /
D-ORC-10). Este arquivo de regressão pina as duas pontas (R2/R4):

  1. SNAPSHOT: `ItemOrcamento` NÃO tem atributo de margem/custo/comissão — esses
     vivem só em `precificacao`, visíveis apenas com `orcamento.ver_margem`.
  2. SERIALIZER PÚBLICO: `serializar_orcamento_publico` devolve SÓ a allowlist
     (descricao/quantidade/preco_unitario/total no item) e NUNCA expõe
     margem/custo/comissão/observações/semáforo/preco_resolvido — nem em chave,
     nem em valor (anti-vazamento ADV-ORC-09).

Teste PURO (sem banco): exercita o domínio e a função de serialização diretamente.
A prova E2E (via SECURITY DEFINER + HTTP) está em `tests/test_orcamentos_publico.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import EstadoOrcamento, TipoAtividadeAlvo
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia
from src.infrastructure.orcamentos.serializers_publico import (
    _ITEM_CAMPOS_PUBLICOS,
    serializar_orcamento_publico,
)

# Tokens de campos internos que NUNCA podem aparecer no payload público.
_PROIBIDOS = (
    "margem",
    "custo",
    "comissao",
    "comissao_prevista",
    "preco_resolvido",
    "observac",  # observacoes/observações
    "semaforo",
)


# ---------------------------------------------------------------------------
# Builders puros
# ---------------------------------------------------------------------------


def _preco_resolvido(valor: str) -> PrecoResolvido:
    return PrecoResolvido(
        item_id=uuid4(),
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=uuid4(),
        preco=Preco(Decimal(valor)),
        data_referencia=datetime(2026, 1, 1, tzinfo=UTC),
        origem_preco=OrigemPreco.MANUAL,
    )


def _orcamento() -> Orcamento:
    return Orcamento(
        id=uuid4(),
        tenant_id=uuid4(),
        cliente_atual_id=uuid4(),
        cliente_referencia_hash="a" * 64,
        cliente_key_id="v1",
        numero=42,
        estado=EstadoOrcamento.ENVIADO,
        validade=JanelaVigencia(inicio=datetime(2026, 1, 1, tzinfo=UTC)),
        total_bruto=Dinheiro(23000),
        descontos=Dinheiro(0),
        impostos=Dinheiro(0),
        liquido=Dinheiro(23000),
        comissao_prevista=Dinheiro(5000),  # segredo comercial — NUNCA no payload público
        condicoes_pagamento=CondicoesPagamento.a_vista_pix(),
        criado_em=datetime(2026, 1, 1, tzinfo=UTC),
        criado_por=uuid4(),
        observacoes="margem alvo 35% — anotação INTERNA, jamais exposta",
    )


def _item_tecnico() -> ItemOrcamento:
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=uuid4(),
        sequencia=1,
        preco_resolvido=_preco_resolvido("150.00"),
        preco_final=Dinheiro(15000),
        desconto_pct=Decimal("0"),
        desconto_valor=Dinheiro(0),
        quantidade=Decimal("1"),
        total=Dinheiro(15000),
        semaforo="verde",
        descricao_snapshot="Calibracao balanca 30kg",
        equipamento_id=uuid4(),
        tipo_atividade_alvo=TipoAtividadeAlvo.CALIBRACAO,
        grandeza_solicitada="massa",
        faixa_solicitada_min=Decimal("0"),
        faixa_solicitada_max=Decimal("30"),
        unidade_solicitada="kg",
    )


def _item_comercial() -> ItemOrcamento:
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=uuid4(),
        sequencia=2,
        preco_resolvido=_preco_resolvido("80.00"),
        preco_final=Dinheiro(8000),
        desconto_pct=Decimal("0"),
        desconto_valor=Dinheiro(0),
        quantidade=Decimal("1"),
        total=Dinheiro(8000),
        semaforo="verde",
        descricao_snapshot="Taxa de deslocamento",
        equipamento_id=None,
        tipo_item_comercial=TipoItemComercial.TAXA_VISITA,
    )


# ---------------------------------------------------------------------------
# 1. Snapshot: ItemOrcamento não tem margem/custo/comissão
# ---------------------------------------------------------------------------


def test_inv_orc_margem_off_item_sem_atributo_de_margem() -> None:
    """INV-ORC-MARGEM-OFF: ItemOrcamento não carrega margem/custo/comissão."""
    item = _item_tecnico()
    for proibido in ("margem", "custo", "custo_unitario", "comissao", "comissao_prevista"):
        assert not hasattr(item, proibido), (
            f"ItemOrcamento não deve ter atributo {proibido!r} (INV-ORC-MARGEM-OFF)"
        )


# ---------------------------------------------------------------------------
# 2. Allowlist canônica do item público
# ---------------------------------------------------------------------------


def test_inv_orc_margem_off_allowlist_canonica() -> None:
    """A allowlist do item público é exatamente os 4 campos não-sensíveis."""
    assert _ITEM_CAMPOS_PUBLICOS == ("descricao", "quantidade", "preco_unitario", "total")
    for proibido in _PROIBIDOS:
        assert proibido not in _ITEM_CAMPOS_PUBLICOS


# ---------------------------------------------------------------------------
# 3. Serializer público nunca devolve campo interno (chave nem valor)
# ---------------------------------------------------------------------------


def test_inv_orc_margem_off_serializer_publico_sem_vazamento() -> None:
    """INV-ORC-MARGEM-OFF / ADV-ORC-09: payload público não contém campo interno."""
    orc = _orcamento()
    itens = [_item_tecnico(), _item_comercial()]

    payload = serializar_orcamento_publico(
        orc,
        itens,
        ressalvas=["Confirmar disponibilidade do padrão antes de agendar."],
        requer_confirmacao_ressalvas=True,
    )

    # Item: SÓ os 4 campos da allowlist (nem um a mais).
    for item_pub in payload["itens"]:
        assert set(item_pub.keys()) == set(_ITEM_CAMPOS_PUBLICOS), (
            f"item público expôs campos fora da allowlist: {set(item_pub.keys())}"
        )

    # Nenhum token interno em chave OU valor (varredura do payload inteiro).
    bruto = str(payload).lower()
    for proibido in _PROIBIDOS:
        assert proibido not in bruto, f"vazou campo interno no payload público: {proibido!r}"

    # Sanidade: os campos esperados ESTÃO presentes (não é um falso "limpo" por vazio).
    assert payload["numero"] == 42
    assert payload["itens"][0]["descricao"] == "Calibracao balanca 30kg"
    assert payload["itens"][0]["preco_unitario"]["centavos"] == 15000
