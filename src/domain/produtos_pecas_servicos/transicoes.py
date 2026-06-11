"""Funções puras de transição/consulta do catálogo (T-PPS-013).

Lição M2 da frente #1 embutida: linha/versão REVOGADA nunca resolve — filtro
`revogado_em is None` EXPLÍCITO além do `vigente_em` (revogação é retroativa à
janela inteira; `vigente_em(D)` com D anterior à revogação retornaria True).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from uuid import UUID

from src.domain.produtos_pecas_servicos.entities import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaTabelaPreco,
)
from src.domain.produtos_pecas_servicos.enums import StatusItem, TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    ItemInativoError,
    KitComCicloError,
    VersaoRetroativaError,
)
from src.domain.shared.value_objects import JanelaVigencia


def validar_vigencia_nao_retroativa(
    *,
    inicio_nova: datetime,
    vigente_atual: ItemCatalogoVersao | None,
    agora: datetime,
    primeira_versao: bool = False,
) -> None:
    """INV-PPS-PRECO-NAO-RETROATIVO (TL-PPS-08).

    Nova versão exige `inicio_nova >= max(agora, inicio_da_vigente)` — encerrar a
    anterior NÃO pode truncar vigência já decorrida (consulta histórica
    `preco_vigente_em(D)` nunca muda de resposta). Exceção única: PRIMEIRA versão
    de item novo (importação de catálogo legado) pode carregar vigência passada.
    """
    if primeira_versao and vigente_atual is None:
        return
    piso = agora
    if vigente_atual is not None and vigente_atual.vigencia.inicio > piso:
        piso = vigente_atual.vigencia.inicio
    if inicio_nova < piso:
        raise VersaoRetroativaError(
            f"vigencia_inicio {inicio_nova.isoformat()} anterior ao piso "
            f"{piso.isoformat()} — versão nova não trunca história (TL-PPS-08)."
        )


def validar_kit_sem_ciclo(
    *, kit: ItemCatalogo, filhos: Sequence[ItemCatalogo], composicao: Sequence[KitComposicao]
) -> None:
    """INV-PPS-KIT-SEM-CICLO — kit só contém produto/peça/serviço (1 nível).

    Também barra: kit vazio, filho repetido e filho INATIVO (AC-CAT-005-1 —
    item inativo não entra em composição nova).
    """
    if kit.tipo != TipoItem.KIT:
        raise KitComCicloError(f"item {kit.id} não é kit (tipo={kit.tipo.value}).")
    if not composicao:
        raise KitComCicloError("kit exige >=1 componente.")
    ids_vistos: set[UUID] = set()
    filhos_por_id = {f.id: f for f in filhos}
    for parte in composicao:
        if parte.item_filho_id in ids_vistos:
            raise KitComCicloError(f"componente {parte.item_filho_id} repetido no kit.")
        ids_vistos.add(parte.item_filho_id)
        filho = filhos_por_id.get(parte.item_filho_id)
        if filho is None:
            raise KitComCicloError(f"componente {parte.item_filho_id} inexistente no tenant.")
        if filho.tipo == TipoItem.KIT:
            raise KitComCicloError(
                f"componente {filho.id} é kit — kit não contém kit (1 nível, TL anti-ciclo)."
            )
        if filho.status == StatusItem.INATIVO:
            raise ItemInativoError(
                f"componente {filho.id} está inativo — não entra em kit novo (AC-CAT-005-1)."
            )


def proxima_versao_n(versoes_existentes: Iterable[ItemCatalogoVersao]) -> int:
    """Versão densa por item: `max+1` (TL-PPS-04 — densidade vem DESTA função
    rodando sob advisory lock por item, não do UNIQUE; sem trigger de
    consecutividade: não é numeração gap-less fiscal)."""
    maior = 0
    for v in versoes_existentes:
        if v.versao_n > maior:
            maior = v.versao_n
    return maior + 1


def versao_vigente_em(
    versoes: Iterable[ItemCatalogoVersao], momento: datetime
) -> ItemCatalogoVersao | None:
    """Versão de LISTA vigente em `momento`. Revogada NUNCA resolve (lição M2)."""
    for v in versoes:
        if v.vigencia.revogado_em is None and v.vigencia.vigente_em(momento):
            return v
    return None


def linha_vigente_em(
    linhas: Iterable[LinhaTabelaPreco],
    *,
    tabela_id: UUID,
    item_id: UUID,
    momento: datetime,
) -> LinhaTabelaPreco | None:
    """Linha de VENDA vigente em `momento` na tabela. Revogada NUNCA resolve.

    Determinístico: não-sobreposição por (tenant, tabela, item) garante no
    máximo 1 resultado entre as não-revogadas (INV-PPS-LINHA-SEM-SOBREPOSICAO).
    """
    for linha in linhas:
        if (
            linha.tabela_id == tabela_id
            and linha.item_id == item_id
            and linha.vigencia.revogado_em is None
            and linha.vigencia.vigente_em(momento)
        ):
            return linha
    return None


def janelas_sobrepoem(a: JanelaVigencia, b: JanelaVigencia) -> bool:
    """Sobreposição half-open `[inicio, fim)` — defesa no domínio (mensagem
    clara no use case); a VERDADE é a exclusion `btree_gist` 0004 no banco."""
    fim_a = a.fim or datetime.max.replace(tzinfo=UTC)
    fim_b = b.fim or datetime.max.replace(tzinfo=UTC)
    return a.inicio < fim_b and b.inicio < fim_a

