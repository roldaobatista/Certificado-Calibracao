"""Porta de leitura `preco_para_os` — contrato ADR-0081 §4 (T-PPS-032).

Resolução SERVER-SIDE do preço de VENDA na tabela PADRÃO do tenant,
**fail-closed** (D-PPS-2): sem linha vigente e não-revogada na
`data_referencia` → `PrecoTabelaAusenteError` (a OS avulsa mapeia 422
`PrecoTabelaAusente` — US-OS-015). SEM fallback ao `preco_padrao` da lista
(fallback silencioso cobraria preço não aprovado — ADV-PPS-09c).

Semântica de `data_referencia` (ADV-PPS-05, CDC art. 39 X): é a data do FATO
GERADOR COMERCIAL — contratação/lançamento do serviço — NÃO a data do
faturamento. O caller (OS/orçamentos) PERSISTE as referências probatórias do
`PrecoResolvido` junto do valor (INV-026 ponto 3): reconsultar depois pode dar
resposta diferente se houve correção auditada (revoga+recria D-PPS-8).

Wire-in na OS é GATE-PPS-WIREIN-OS (bloqueante pré-1º tenant externo).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.domain.produtos_pecas_servicos.entities import (
    ComponenteResolvido,
    PrecoResolvido,
)
from src.domain.produtos_pecas_servicos.enums import StatusItem, TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    ItemInativoError,
    PrecoTabelaAusenteError,
)
from src.domain.produtos_pecas_servicos.repository import (
    ItemCatalogoRepository,
    TabelaPrecoRepository,
)
from src.domain.produtos_pecas_servicos.transicoes import (
    linha_vigente_em,
    versao_vigente_em,
)
from src.infrastructure.produtos_pecas_servicos.repositories import (
    DjangoItemCatalogoRepository,
    DjangoTabelaPrecoRepository,
)


def preco_para_os(
    *,
    tenant_id: UUID,
    item_id: UUID,
    data_referencia: datetime,
    item_repo: ItemCatalogoRepository | None = None,
    tabela_repo: TabelaPrecoRepository | None = None,
) -> PrecoResolvido:
    """Resolve o preço de venda do item na tabela padrão (fail-closed).

    Levanta:
    - `PrecoTabelaAusenteError` (→ 422): item inexistente no tenant; tenant sem
      tabela padrão; sem linha vigente não-revogada na `data_referencia` (kit
      sem linha PRÓPRIA cai aqui — TL-PPS-09); sem versão de lista vigente
      (a referência probatória `item_versao_n` é obrigatória no contrato).
    - `ItemInativoError` (→ 422): item inativo não entra em venda NOVA
      (AC-CAT-005-1) — erro distinto pra mensagem acionável.

    `data_referencia` exige tz-aware (INV-VIG-004 propaga ValueError → 400).
    Repos injetáveis (Protocols) — default = adapters Django (RLS no contexto).
    """
    itens = item_repo if item_repo is not None else DjangoItemCatalogoRepository()
    tabelas = tabela_repo if tabela_repo is not None else DjangoTabelaPrecoRepository()

    item = itens.obter(tenant_id=tenant_id, item_id=item_id)
    if item is None:
        raise PrecoTabelaAusenteError(
            f"item {item_id} inexistente no tenant — resolução fail-closed."
        )
    if item.status == StatusItem.INATIVO:
        raise ItemInativoError(
            f"item {item_id} inativo — não entra em venda nova (AC-CAT-005-1)."
        )
    tabela = tabelas.obter_padrao(tenant_id=tenant_id)
    if tabela is None:
        raise PrecoTabelaAusenteError(
            "tenant sem tabela de preço padrão — cadastre a tabela (ADR-0081)."
        )
    linhas = tabelas.listar_linhas(
        tenant_id=tenant_id, tabela_id=tabela.id, item_id=item_id
    )
    linha = linha_vigente_em(
        linhas, tabela_id=tabela.id, item_id=item_id, momento=data_referencia
    )
    if linha is None:
        raise PrecoTabelaAusenteError(
            f"sem linha de preço vigente para o item {item_id} na tabela padrão "
            f"em {data_referencia.isoformat()} (kit exige linha própria — TL-PPS-09)."
        )
    versao = versao_vigente_em(
        itens.listar_versoes(tenant_id=tenant_id, item_id=item_id), data_referencia
    )
    if versao is None:
        raise PrecoTabelaAusenteError(
            f"item {item_id} sem versão de lista vigente em "
            f"{data_referencia.isoformat()} — referência probatória "
            "`item_versao_n` indisponível (fail-closed)."
        )
    composicao_resolvida: tuple[ComponenteResolvido, ...] = ()
    if item.tipo == TipoItem.KIT:
        composicao_resolvida = _resolver_composicao(
            itens, tenant_id=tenant_id, kit_item_id=item_id, momento=data_referencia
        )
    return PrecoResolvido(
        item_id=item_id,
        item_versao_n=versao.versao_n,
        linha_tabela_id=linha.id,
        tabela_id=tabela.id,
        preco=linha.preco,
        data_referencia=data_referencia,
        origem_preco=linha.origem_sugestao,
        composicao_resolvida=composicao_resolvida,
    )


def _resolver_composicao(
    itens: ItemCatalogoRepository,
    *,
    tenant_id: UUID,
    kit_item_id: UUID,
    momento: datetime,
) -> tuple[ComponenteResolvido, ...]:
    """Decomposição INFORMATIVA do kit na MESMA `data_referencia` (TL-PPS-10).

    O preço do kit vem da linha PRÓPRIA — a decomposição não participa da
    resolução (TL-PPS-09: nada de 422 em cascata). All-or-nothing: se alguma
    parte não tem versão de lista vigente no momento, retorna `()` (decomposição
    parcial enganaria a reconciliação de soma — ADV-PPS-08).
    """
    partes: list[ComponenteResolvido] = []
    for parte in itens.listar_composicao(tenant_id=tenant_id, kit_item_id=kit_item_id):
        versao_filho = versao_vigente_em(
            itens.listar_versoes(tenant_id=tenant_id, item_id=parte.item_filho_id),
            momento,
        )
        if versao_filho is None:
            return ()
        partes.append(
            ComponenteResolvido(
                item_filho_id=parte.item_filho_id,
                quantidade=parte.quantidade,
                versao_n=versao_filho.versao_n,
                preco_unitario=versao_filho.preco_padrao,
            )
        )
    return tuple(partes)
