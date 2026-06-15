"""Use cases `adicionar_item` / `editar_item` — T-ORC-031 (Fatia 2 / Onda 2a).

A VIEW (infra) monta as deps de `calcular_precos`, chama-o e passa o
`ItemCalculado` resolvido a estes use cases (D-FATIA2-C / TL-ORC ALTO-2) — os use
cases NAO instanciam repos de precificacao. Aqui extraimos os primitivos do
`ItemCalculado` e persistimos SO o carimbo probatorio (INV-ORC-MARGEM-OFF):
`PrecoResolvido` + preco_final + desconto + semaforo. NUNCA margem/custo no item.

Itens so podem ser adicionados/editados em RASCUNHO (estado mutavel; a versao
corrente congela ao enviar — D-ORC-8). A cada mutacao recompomos os 5 totais do
agregado (imposto por dentro — ver `calculo.compor_totais`).

Bifurcacao (INV-ORC-EQUIP-ITEM / D-ORC-16): item de calibracao tem `equipamento_id`
+ `tipo_atividade_alvo`; item comercial tem `tipo_item_comercial` e nenhum dos dois
primeiros (validado no `ItemOrcamento.__post_init__`).

Caller (view) abre `transaction.atomic`. Refs: spec §4; D-ORC-1/10; AC-ORC-001/004.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.comercial.orcamentos import calculo
from src.domain.comercial.orcamentos.entities import ItemOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import EstadoOrcamento, TipoAtividadeAlvo
from src.domain.comercial.orcamentos.erros import (
    EstadoInvalido,
    OrcamentoConvertido,
)
from src.domain.comercial.orcamentos.repository import OrcamentoRepository
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.precificacao.value_objects import ItemCalculado


class ItemOrcamentoNaoEncontrado(EstadoInvalido):
    """Item informado nao pertence a versao corrente do orcamento (404 logico)."""

    codigo = "item_orcamento_nao_encontrado"
    http_status = 404


@dataclass(frozen=True, slots=True)
class AdicionarItemInput:
    tenant_id: UUID
    orcamento_id: UUID
    item_calculado: ItemCalculado
    quantidade: Decimal
    descricao_snapshot: str
    aliquota_imposto_fracao: Decimal
    comissao_fracao: Decimal
    equipamento_id: UUID | None = None
    tipo_atividade_alvo: TipoAtividadeAlvo | None = None
    tipo_item_comercial: TipoItemComercial | None = None
    grandeza_solicitada: str | None = None
    faixa_solicitada_min: Decimal | None = None
    faixa_solicitada_max: Decimal | None = None
    unidade_solicitada: str | None = None


@dataclass(frozen=True, slots=True)
class EditarItemInput:
    tenant_id: UUID
    orcamento_id: UUID
    item_id: UUID
    item_calculado: ItemCalculado
    quantidade: Decimal
    descricao_snapshot: str
    aliquota_imposto_fracao: Decimal
    comissao_fracao: Decimal
    equipamento_id: UUID | None = None
    tipo_atividade_alvo: TipoAtividadeAlvo | None = None
    tipo_item_comercial: TipoItemComercial | None = None
    grandeza_solicitada: str | None = None
    faixa_solicitada_min: Decimal | None = None
    faixa_solicitada_max: Decimal | None = None
    unidade_solicitada: str | None = None


@dataclass(frozen=True, slots=True)
class ItemOrcamentoOutput:
    orcamento: Orcamento
    item: ItemOrcamento


def _carregar_rascunho_editavel(
    orcamento_id: UUID, tenant_id: UUID, *, repo: OrcamentoRepository
) -> tuple[Orcamento, UUID]:
    """Carrega o orcamento garantindo que esta em RASCUNHO + devolve a versao corrente."""
    orcamento = repo.get_by_id(orcamento_id, tenant_id=tenant_id)
    if orcamento is None:
        raise ItemOrcamentoNaoEncontrado(
            f"orcamento {orcamento_id} inexistente neste tenant.",
            orcamento_id=str(orcamento_id),
        )
    if orcamento.estado == EstadoOrcamento.CONVERTIDO:
        raise OrcamentoConvertido(
            f"orcamento {orcamento_id} ja convertido — itens imutaveis (INV-ORC-CONVERTIDO-TERMINAL).",
            orcamento_id=str(orcamento_id),
        )
    if orcamento.estado != EstadoOrcamento.RASCUNHO:
        raise EstadoInvalido(
            f"orcamento {orcamento_id} em estado {orcamento.estado.value!r} — "
            "itens so podem ser alterados em rascunho (D-ORC-3).",
            estado_atual=orcamento.estado.value,
        )
    versao = repo.get_versao_ativa(orcamento_id, tenant_id=tenant_id)
    if versao is None:
        raise EstadoInvalido(
            f"orcamento {orcamento_id} sem versao corrente — estado inconsistente.",
            orcamento_id=str(orcamento_id),
        )
    return orcamento, versao.id


def _montar(
    *,
    item_id: UUID,
    versao_id: UUID,
    tenant_id: UUID,
    sequencia: int,
    item_calc: ItemCalculado,
    quantidade: Decimal,
    descricao_snapshot: str,
    moeda: str,
    equipamento_id: UUID | None,
    tipo_atividade_alvo: TipoAtividadeAlvo | None,
    tipo_item_comercial: TipoItemComercial | None,
    grandeza_solicitada: str | None,
    faixa_solicitada_min: Decimal | None,
    faixa_solicitada_max: Decimal | None,
    unidade_solicitada: str | None,
) -> ItemOrcamento:
    """Extrai os primitivos do `ItemCalculado` e delega ao dominio puro."""
    return calculo.montar_item_orcamento(
        id=item_id,
        versao_id=versao_id,
        tenant_id=tenant_id,
        catalogo_item_id=item_calc.preco_base.item_id,
        sequencia=sequencia,
        preco_resolvido=item_calc.preco_base,
        preco_final_unit=item_calc.preco_final,
        desconto_pct=item_calc.desconto_pct.valor,
        preco_tabela_unit=item_calc.preco_base.preco.valor,
        quantidade=quantidade,
        semaforo=item_calc.semaforo.value,
        descricao_snapshot=descricao_snapshot,
        moeda=moeda,
        equipamento_id=equipamento_id,
        tipo_atividade_alvo=tipo_atividade_alvo,
        tipo_item_comercial=tipo_item_comercial,
        grandeza_solicitada=grandeza_solicitada,
        faixa_solicitada_min=faixa_solicitada_min,
        faixa_solicitada_max=faixa_solicitada_max,
        unidade_solicitada=unidade_solicitada,
    )


def _recompor_agregado(
    orcamento: Orcamento,
    itens: list[ItemOrcamento],
    *,
    aliquota_imposto_fracao: Decimal,
    comissao_fracao: Decimal,
    repo: OrcamentoRepository,
) -> Orcamento:
    """Recompoe os totais do agregado a partir dos itens e persiste."""
    moeda = orcamento.total_bruto.moeda
    totais = calculo.compor_totais(
        itens,
        aliquota_imposto_fracao=aliquota_imposto_fracao,
        comissao_fracao=comissao_fracao,
        moeda=moeda,
    )
    atualizado = replace(
        orcamento,
        total_bruto=totais.total_bruto,
        descontos=totais.descontos,
        impostos=totais.impostos,
        liquido=totais.liquido,
        comissao_prevista=totais.comissao_prevista,
    )
    return repo.salvar(atualizado)


def adicionar_item(inp: AdicionarItemInput, *, repo: OrcamentoRepository) -> ItemOrcamentoOutput:
    """Adiciona um item a versao corrente + recompoe os totais (AC-ORC-001/004)."""
    orcamento, versao_id = _carregar_rascunho_editavel(inp.orcamento_id, inp.tenant_id, repo=repo)
    moeda = orcamento.total_bruto.moeda
    itens = repo.listar_itens_versao(versao_id, tenant_id=inp.tenant_id)
    sequencia = (max((i.sequencia for i in itens), default=0)) + 1

    novo = _montar(
        item_id=uuid4(),
        versao_id=versao_id,
        tenant_id=inp.tenant_id,
        sequencia=sequencia,
        item_calc=inp.item_calculado,
        quantidade=inp.quantidade,
        descricao_snapshot=inp.descricao_snapshot,
        moeda=moeda,
        equipamento_id=inp.equipamento_id,
        tipo_atividade_alvo=inp.tipo_atividade_alvo,
        tipo_item_comercial=inp.tipo_item_comercial,
        grandeza_solicitada=inp.grandeza_solicitada,
        faixa_solicitada_min=inp.faixa_solicitada_min,
        faixa_solicitada_max=inp.faixa_solicitada_max,
        unidade_solicitada=inp.unidade_solicitada,
    )
    novo = repo.salvar_item(novo)

    orcamento = _recompor_agregado(
        orcamento,
        [*itens, novo],
        aliquota_imposto_fracao=inp.aliquota_imposto_fracao,
        comissao_fracao=inp.comissao_fracao,
        repo=repo,
    )
    return ItemOrcamentoOutput(orcamento=orcamento, item=novo)


def editar_item(inp: EditarItemInput, *, repo: OrcamentoRepository) -> ItemOrcamentoOutput:
    """Reprecifica/edita um item existente (preserva sequencia) + recompoe totais."""
    orcamento, versao_id = _carregar_rascunho_editavel(inp.orcamento_id, inp.tenant_id, repo=repo)
    moeda = orcamento.total_bruto.moeda
    itens = repo.listar_itens_versao(versao_id, tenant_id=inp.tenant_id)
    alvo = next((i for i in itens if i.id == inp.item_id), None)
    if alvo is None:
        raise ItemOrcamentoNaoEncontrado(
            f"item {inp.item_id} nao pertence ao orcamento {inp.orcamento_id}.",
            item_id=str(inp.item_id),
        )

    editado = _montar(
        item_id=inp.item_id,
        versao_id=versao_id,
        tenant_id=inp.tenant_id,
        sequencia=alvo.sequencia,
        item_calc=inp.item_calculado,
        quantidade=inp.quantidade,
        descricao_snapshot=inp.descricao_snapshot,
        moeda=moeda,
        equipamento_id=inp.equipamento_id,
        tipo_atividade_alvo=inp.tipo_atividade_alvo,
        tipo_item_comercial=inp.tipo_item_comercial,
        grandeza_solicitada=inp.grandeza_solicitada,
        faixa_solicitada_min=inp.faixa_solicitada_min,
        faixa_solicitada_max=inp.faixa_solicitada_max,
        unidade_solicitada=inp.unidade_solicitada,
    )
    editado = repo.salvar_item(editado)

    itens_atualizados = [editado if i.id == inp.item_id else i for i in itens]
    orcamento = _recompor_agregado(
        orcamento,
        itens_atualizados,
        aliquota_imposto_fracao=inp.aliquota_imposto_fracao,
        comissao_fracao=inp.comissao_fracao,
        repo=repo,
    )
    return ItemOrcamentoOutput(orcamento=orcamento, item=editado)
