"""Use cases do agregado `TabelaPreco` — ADR-0081 (T-PPS-031). PUROS.

A linha de VENDA é imutável molde Imposto (INV-PPS-LINHA-IMUTAVEL): preço
digitado errado → `corrigir_linha` (revoga+recria atômico — D-PPS-8); preço
mudou de verdade → `encerrar_linha` + `criar_linha` nova janela. A
não-sobreposição por (tenant, tabela, item) tem duas camadas: defesa no
domínio (`janelas_sobrepoem`, mensagem clara) + exclusion `btree_gist` 0004
(a VERDADE — INV-PPS-LINHA-SEM-SOBREPOSICAO).

`preco_padrao` da LISTA é só DEFAULT SUGERIDO na criação da linha (ADR-0081);
NUNCA fallback runtime — a porta `preco_para_os` é fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.produtos_pecas_servicos.item import ItemAusenteError
from src.domain.produtos_pecas_servicos.entities import LinhaTabelaPreco, TabelaPreco
from src.domain.produtos_pecas_servicos.enums import OrigemPreco, StatusItem, TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    ItemInativoError,
    TabelaPadraoDuplicadaError,
)
from src.domain.produtos_pecas_servicos.repository import (
    ItemCatalogoRepository,
    TabelaPrecoRepository,
)
from src.domain.produtos_pecas_servicos.transicoes import (
    janelas_sobrepoem,
    versao_vigente_em,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia


class TabelaAusenteError(Exception):
    """Tabela inexistente no tenant — view mapeia 404."""


class LinhaAusenteError(Exception):
    """Linha inexistente na tabela — view mapeia 404."""


class LinhaSobrepostaError(Exception):
    """INV-PPS-LINHA-SEM-SOBREPOSICAO (defesa no domínio) — view mapeia 422."""


class SugestaoPrecoIndisponivelError(Exception):
    """Sem base pra sugerir preço (lista sem versão vigente / kit com parte
    sem versão) — informe `preco` explícito (→ 422)."""


# === criar_tabela (D-PPS-3) ===


@dataclass(frozen=True, slots=True)
class CriarTabelaInput:
    tenant_id: UUID
    nome: str
    eh_padrao: bool = True  # MVP: a 1ª tabela do tenant é a padrão
    descricao: str = ""


def criar_tabela(inp: CriarTabelaInput, *, repo: TabelaPrecoRepository) -> TabelaPreco:
    """2ª padrão → 422 (UNIQUE parcial é a verdade; defesa aqui dá mensagem PT)."""
    if not inp.nome.strip():
        raise ValueError("nome da tabela obrigatório.")
    if inp.eh_padrao and repo.obter_padrao(tenant_id=inp.tenant_id) is not None:
        raise TabelaPadraoDuplicadaError(
            "tenant já tem tabela padrão (MVP = 1 tabela — D-PPS-3)."
        )
    tabela = TabelaPreco(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        nome=inp.nome.strip(),
        eh_padrao=inp.eh_padrao,
        descricao=inp.descricao,
    )
    repo.salvar(tabela)
    return tabela


# === criar_linha (ADR-0081 — venda vigente) ===


@dataclass(frozen=True, slots=True)
class CriarLinhaInput:
    tenant_id: UUID
    tabela_id: UUID
    item_id: UUID
    criado_por: UUID
    agora: datetime
    preco: Decimal | None = None  # None = default SUGERIDO (lista / soma das partes)
    vigencia_inicio: datetime | None = None  # None = agora
    vigencia_fim: datetime | None = None


@dataclass(frozen=True, slots=True)
class CriarLinhaOutput:
    linha: LinhaTabelaPreco


def criar_linha(
    inp: CriarLinhaInput,
    *,
    tabela_repo: TabelaPrecoRepository,
    item_repo: ItemCatalogoRepository,
) -> CriarLinhaOutput:
    """Nova linha de venda por (tabela, item).

    Sem `preco` explícito, sugere o default na CRIAÇÃO (nunca em runtime):
    item comum = `preco_padrao` da versão de lista vigente (origem MANUAL —
    operador aceitou a sugestão); kit = soma qtd×preço de lista das partes
    (origem SOMA_PARTES — AC-CAT-003-1). Kit na tabela é linha PRÓPRIA
    (TL-PPS-09) — esta função é exatamente o caminho que a cria.
    """
    tabela = tabela_repo.obter(tenant_id=inp.tenant_id, tabela_id=inp.tabela_id)
    if tabela is None:
        raise TabelaAusenteError(f"tabela {inp.tabela_id} inexistente no tenant.")
    item = item_repo.obter(tenant_id=inp.tenant_id, item_id=inp.item_id)
    if item is None:
        raise ItemAusenteError(f"item {inp.item_id} inexistente no tenant.")
    if item.status == StatusItem.INATIVO:
        raise ItemInativoError(
            f"item {inp.item_id} inativo — não entra em venda nova (AC-CAT-005-1)."
        )
    tabela_repo.travar_linha(
        tenant_id=inp.tenant_id, tabela_id=inp.tabela_id, item_id=inp.item_id
    )
    inicio = inp.vigencia_inicio if inp.vigencia_inicio is not None else inp.agora
    origem = OrigemPreco.MANUAL
    valor = inp.preco
    if valor is None:
        valor, origem = _sugerir_preco(
            item_repo=item_repo,
            tenant_id=inp.tenant_id,
            item_id=inp.item_id,
            eh_kit=item.tipo == TipoItem.KIT,
            momento=inicio,
        )
    linha = LinhaTabelaPreco(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tabela_id=inp.tabela_id,
        item_id=inp.item_id,
        preco=Preco(valor),
        vigencia=JanelaVigencia(inicio=inicio, fim=inp.vigencia_fim),
        criado_por=inp.criado_por,
        origem_sugestao=origem,
    )
    _validar_nao_sobreposicao(tabela_repo, linha)
    tabela_repo.salvar_linha(linha)
    return CriarLinhaOutput(linha=linha)


def _sugerir_preco(
    *,
    item_repo: ItemCatalogoRepository,
    tenant_id: UUID,
    item_id: UUID,
    eh_kit: bool,
    momento: datetime,
) -> tuple[Decimal, OrigemPreco]:
    if not eh_kit:
        versao = versao_vigente_em(
            item_repo.listar_versoes(tenant_id=tenant_id, item_id=item_id), momento
        )
        if versao is None:
            raise SugestaoPrecoIndisponivelError(
                "item sem versão de lista vigente — informe `preco` explícito."
            )
        return versao.preco_padrao.valor, OrigemPreco.MANUAL
    composicao = item_repo.listar_composicao(tenant_id=tenant_id, kit_item_id=item_id)
    if not composicao:
        raise SugestaoPrecoIndisponivelError(
            "kit sem composição — monte o kit antes ou informe `preco` explícito."
        )
    total = Decimal("0")
    for parte in composicao:
        versao_filho = versao_vigente_em(
            item_repo.listar_versoes(tenant_id=tenant_id, item_id=parte.item_filho_id),
            momento,
        )
        if versao_filho is None:
            raise SugestaoPrecoIndisponivelError(
                f"parte {parte.item_filho_id} sem versão de lista vigente — "
                "informe `preco` explícito."
            )
        total += parte.quantidade * versao_filho.preco_padrao.valor
    return total, OrigemPreco.SOMA_PARTES


def _validar_nao_sobreposicao(
    tabela_repo: TabelaPrecoRepository, nova: LinhaTabelaPreco
) -> None:
    existentes = tabela_repo.listar_linhas(
        tenant_id=nova.tenant_id, tabela_id=nova.tabela_id, item_id=nova.item_id
    )
    for linha in existentes:
        if linha.vigencia.revogado_em is not None:  # revogada sai do WHERE da 0004
            continue
        if linha.id != nova.id and janelas_sobrepoem(linha.vigencia, nova.vigencia):
            raise LinhaSobrepostaError(
                "vigência sobrepõe linha existente do item nesta tabela — "
                "encerre a vigência anterior antes (INV-PPS-LINHA-SEM-SOBREPOSICAO)."
            )


# === corrigir_linha (D-PPS-8 — revoga+recria atômico) ===


@dataclass(frozen=True, slots=True)
class CorrigirLinhaInput:
    tenant_id: UUID
    tabela_id: UUID
    linha_id: UUID
    preco: Decimal  # o valor CORRETO (motivo nº1: preço digitado errado)
    motivo: str  # ≥10 chars (INV-VIG-002)
    criado_por: UUID


@dataclass(frozen=True, slots=True)
class CorrigirLinhaOutput:
    linha_revogada_id: UUID
    linha: LinhaTabelaPreco  # substituta na MESMA janela


def corrigir_linha(
    inp: CorrigirLinhaInput, *, tabela_repo: TabelaPrecoRepository
) -> CorrigirLinhaOutput:
    """Revoga a linha errada (one-shot, motivo) + recria substituta na MESMA
    janela (TL-PPS-03). Ordem revoga→recria na mesma transação do caller."""
    if len(inp.motivo.strip()) < 10:
        raise ValueError("correção exige motivo com ≥10 chars (INV-VIG-002).")
    linhas = tabela_repo.listar_linhas(
        tenant_id=inp.tenant_id, tabela_id=inp.tabela_id
    )
    alvo = next((linha for linha in linhas if linha.id == inp.linha_id), None)
    if alvo is None:
        raise LinhaAusenteError(f"linha {inp.linha_id} inexistente na tabela.")
    if alvo.vigencia.revogado_em is not None:
        raise RuntimeError(f"linha {inp.linha_id} já revogada — nada a corrigir.")
    tabela_repo.travar_linha(
        tenant_id=inp.tenant_id, tabela_id=inp.tabela_id, item_id=alvo.item_id
    )
    tabela_repo.revogar_linha(
        tenant_id=inp.tenant_id, linha_id=alvo.id, motivo=inp.motivo
    )
    substituta = LinhaTabelaPreco(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tabela_id=inp.tabela_id,
        item_id=alvo.item_id,
        preco=Preco(inp.preco),
        vigencia=JanelaVigencia(inicio=alvo.vigencia.inicio, fim=alvo.vigencia.fim),
        criado_por=inp.criado_por,
        origem_sugestao=OrigemPreco.MANUAL,
    )
    tabela_repo.salvar_linha(substituta)
    return CorrigirLinhaOutput(linha_revogada_id=alvo.id, linha=substituta)


# === encerrar_linha (one-shot NULL→data) ===


@dataclass(frozen=True, slots=True)
class EncerrarLinhaInput:
    tenant_id: UUID
    tabela_id: UUID
    linha_id: UUID
    fim: datetime  # tz-aware

    def __post_init__(self) -> None:
        if self.fim.tzinfo is None:
            raise ValueError("encerrar_linha: fim exige datetime tz-aware (INV-VIG-004).")


def encerrar_linha(
    inp: EncerrarLinhaInput, *, tabela_repo: TabelaPrecoRepository
) -> None:
    """Encerra a vigência ABERTA da linha (one-shot). Já encerrada/revogada →
    RuntimeError do repo (view mapeia 409)."""
    linhas = tabela_repo.listar_linhas(
        tenant_id=inp.tenant_id, tabela_id=inp.tabela_id
    )
    alvo = next((linha for linha in linhas if linha.id == inp.linha_id), None)
    if alvo is None:
        raise LinhaAusenteError(f"linha {inp.linha_id} inexistente na tabela.")
    if inp.fim < alvo.vigencia.inicio:
        raise ValueError(
            f"fim {inp.fim.isoformat()} anterior ao início da linha (INV-VIG-001)."
        )
    tabela_repo.encerrar_vigencia_linha(
        tenant_id=inp.tenant_id, linha_id=inp.linha_id, fim=inp.fim
    )
