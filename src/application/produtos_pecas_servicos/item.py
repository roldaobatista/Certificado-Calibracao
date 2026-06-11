"""Use cases do agregado `ItemCatalogo` — US-CAT-001/002/003/005 (T-PPS-030). PUROS.

Concorrência (D-PPS-4): `nova_versao_preco`/`corrigir_versao` chamam
`repo.travar_item` (advisory lock por item no adapter PG) — o CALLER embrulha
em `transaction.atomic`; a densidade `versao_n = max+1` e o par encerrar-
anterior+inserir-nova ficam serializados. A exclusion 0004 é a verdade no
banco contra qualquer corrida que escape (camada independente).

Imutabilidade (D-PPS-8 / INV-026): versão errada NUNCA sofre UPDATE — o use
case composto `corrigir_versao` revoga (one-shot, motivo auditado) e recria
substituta na MESMA janela (a exclusion tem `WHERE revogado_em IS NULL`).
`nova_versao_preco` é o caminho NORMAL (preço mudou de verdade) e respeita
INV-PPS-PRECO-NAO-RETROATIVO — consulta histórica nunca muda de resposta.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.produtos_pecas_servicos.entities import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
)
from src.domain.produtos_pecas_servicos.enums import StatusItem, TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    CodigoDuplicadoError,
    ItemInativoError,
)
from src.domain.produtos_pecas_servicos.repository import ItemCatalogoRepository
from src.domain.produtos_pecas_servicos.transicoes import (
    proxima_versao_n,
    validar_kit_sem_ciclo,
    validar_vigencia_nao_retroativa,
    versao_vigente_em,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia


class ItemAusenteError(Exception):
    """Item inexistente no tenant (RLS cobre cross-tenant) — view mapeia 404."""


class VersaoAusenteError(Exception):
    """Versão inexistente no item — view mapeia 404."""


# === cadastrar_item (US-CAT-001) ===


@dataclass(frozen=True, slots=True)
class CadastrarItemInput:
    tenant_id: UUID
    codigo_interno: str
    tipo: TipoItem
    nome: str
    unidade_medida: str
    preco_padrao: Decimal  # VO valida escala 2 + > 0 (ValueError → 400)
    criado_por: UUID
    agora: datetime  # tz-aware, injetado pela view (testes determinísticos)
    vigencia_inicio: datetime | None = None  # None = agora
    controla_estoque: bool | None = None  # None = derivado do tipo (TL-PPS-14)
    codigo_fabricante: str = ""
    descricao: str = ""
    categoria: str = ""
    motivo: str = ""
    importacao: bool = False  # Fatia 3 — ÚNICA exceção que permite vigência passada


@dataclass(frozen=True, slots=True)
class CadastrarItemOutput:
    item: ItemCatalogo
    versao: ItemCatalogoVersao


def cadastrar_item(
    inp: CadastrarItemInput, *, repo: ItemCatalogoRepository
) -> CadastrarItemOutput:
    """Cria o item + versão 1 da lista (AC-CAT-001-1/2).

    Código duplicado → `CodigoDuplicadoError` (409); a corrida residual cai no
    UNIQUE do banco (IntegrityError → 409 na view). Vigência passada só com
    `importacao=True` (exceção única da INV-PPS-PRECO-NAO-RETROATIVO).
    """
    codigo = inp.codigo_interno.strip()
    if not codigo:
        raise ValueError("codigo_interno obrigatório (INV-PPS-CODIGO-UNICO).")
    if repo.obter_por_codigo(tenant_id=inp.tenant_id, codigo_interno=codigo) is not None:
        raise CodigoDuplicadoError(
            f"código '{codigo}' já existe no tenant (INV-PPS-CODIGO-UNICO)."
        )
    inicio = inp.vigencia_inicio if inp.vigencia_inicio is not None else inp.agora
    validar_vigencia_nao_retroativa(
        inicio_nova=inicio,
        vigente_atual=None,
        agora=inp.agora,
        primeira_versao=inp.importacao,
    )
    controla_estoque = (
        inp.controla_estoque
        if inp.controla_estoque is not None
        else inp.tipo not in (TipoItem.SERVICO, TipoItem.KIT)
    )
    item = ItemCatalogo(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        codigo_interno=codigo,
        tipo=inp.tipo,
        controla_estoque=controla_estoque,
        status=StatusItem.ATIVO,
        codigo_fabricante=inp.codigo_fabricante,
    )
    versao = ItemCatalogoVersao(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        item_id=item.id,
        versao_n=1,
        nome=inp.nome,
        unidade_medida=inp.unidade_medida,
        preco_padrao=Preco(inp.preco_padrao),
        vigencia=JanelaVigencia(inicio=inicio),
        criado_por=inp.criado_por,
        descricao=inp.descricao,
        categoria=inp.categoria,
        motivo=inp.motivo,
    )
    repo.salvar(item)
    repo.salvar_versao(versao)
    return CadastrarItemOutput(item=item, versao=versao)


# === nova_versao_preco (US-CAT-002) ===


@dataclass(frozen=True, slots=True)
class NovaVersaoPrecoInput:
    tenant_id: UUID
    item_id: UUID
    preco_padrao: Decimal
    criado_por: UUID
    agora: datetime
    vigencia_inicio: datetime | None = None  # None = agora
    # None = herda da versão base (vigente ou última não-revogada)
    nome: str | None = None
    unidade_medida: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    motivo: str = ""


@dataclass(frozen=True, slots=True)
class NovaVersaoPrecoOutput:
    versao: ItemCatalogoVersao
    versao_encerrada_id: UUID | None  # anterior cuja vigência foi fechada


def nova_versao_preco(
    inp: NovaVersaoPrecoInput, *, repo: ItemCatalogoRepository
) -> NovaVersaoPrecoOutput:
    """Nova versão de LISTA sem tocar a história (AC-CAT-002-1/2).

    INV-PPS-PRECO-NAO-RETROATIVO (TL-PPS-08): `inicio_nova ≥ max(agora,
    inicio_da_vigente)`; encerra a vigente EM `inicio_nova` na MESMA transação
    (consulta `preco_vigente_em(D)` com D passado nunca muda). Se a vigente já
    tem fim próprio, não há o que encerrar — colisão residual cai na exclusion
    (IntegrityError → 422).
    """
    repo.travar_item(tenant_id=inp.tenant_id, item_id=inp.item_id)
    item = repo.obter(tenant_id=inp.tenant_id, item_id=inp.item_id)
    if item is None:
        raise ItemAusenteError(f"item {inp.item_id} inexistente no tenant.")
    if item.status == StatusItem.INATIVO:
        raise ItemInativoError(
            f"item {inp.item_id} inativo — reative antes de versionar preço (AC-CAT-005-1)."
        )
    versoes = repo.listar_versoes(tenant_id=inp.tenant_id, item_id=inp.item_id)
    vigente = versao_vigente_em(versoes, inp.agora)
    base = vigente or _ultima_nao_revogada(versoes)
    if base is None:
        raise VersaoAusenteError(
            f"item {inp.item_id} sem versão de lista utilizável como base."
        )
    inicio = inp.vigencia_inicio if inp.vigencia_inicio is not None else inp.agora
    validar_vigencia_nao_retroativa(
        inicio_nova=inicio, vigente_atual=vigente, agora=inp.agora
    )
    nova = ItemCatalogoVersao(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        item_id=inp.item_id,
        versao_n=proxima_versao_n(versoes),
        nome=inp.nome if inp.nome is not None else base.nome,
        unidade_medida=(
            inp.unidade_medida if inp.unidade_medida is not None else base.unidade_medida
        ),
        preco_padrao=Preco(inp.preco_padrao),
        vigencia=JanelaVigencia(inicio=inicio),
        criado_por=inp.criado_por,
        descricao=inp.descricao if inp.descricao is not None else base.descricao,
        categoria=inp.categoria if inp.categoria is not None else base.categoria,
        motivo=inp.motivo,
    )
    encerrada_id: UUID | None = None
    if vigente is not None and vigente.vigencia.fim is None:
        repo.encerrar_vigencia_versao(
            tenant_id=inp.tenant_id, versao_id=vigente.id, fim=inicio
        )
        encerrada_id = vigente.id
    repo.salvar_versao(nova)
    return NovaVersaoPrecoOutput(versao=nova, versao_encerrada_id=encerrada_id)


def _ultima_nao_revogada(
    versoes: list[ItemCatalogoVersao],
) -> ItemCatalogoVersao | None:
    candidatas = [v for v in versoes if v.vigencia.revogado_em is None]
    return max(candidatas, key=lambda v: v.versao_n, default=None)


# === corrigir_versao (D-PPS-8 — revoga+recria atômico) ===


@dataclass(frozen=True, slots=True)
class CorrigirVersaoInput:
    tenant_id: UUID
    item_id: UUID
    versao_id: UUID
    motivo: str  # ≥10 chars (INV-VIG-002) — auditoria da correção
    criado_por: UUID
    # None = preserva o valor da versão errada (corrige só o que mudou)
    preco_padrao: Decimal | None = None
    nome: str | None = None
    unidade_medida: str | None = None
    descricao: str | None = None
    categoria: str | None = None


@dataclass(frozen=True, slots=True)
class CorrigirVersaoOutput:
    versao_revogada_id: UUID
    versao: ItemCatalogoVersao  # substituta na MESMA janela


def corrigir_versao(
    inp: CorrigirVersaoInput, *, repo: ItemCatalogoRepository
) -> CorrigirVersaoOutput:
    """Correção de versão DIGITADA ERRADA (TL-PPS-03): revoga (one-shot,
    motivo) + recria substituta na MESMA janela — a revogada sai da exclusion
    (`WHERE revogado_em IS NULL`) e da resolução (lição M2). A ORDEM
    revoga→recria importa: o INSERT da substituta só passa na exclusion depois
    do UPDATE de revogação, na mesma transação do caller.
    """
    if len(inp.motivo.strip()) < 10:
        raise ValueError("correção exige motivo com ≥10 chars (INV-VIG-002).")
    repo.travar_item(tenant_id=inp.tenant_id, item_id=inp.item_id)
    if repo.obter(tenant_id=inp.tenant_id, item_id=inp.item_id) is None:
        raise ItemAusenteError(f"item {inp.item_id} inexistente no tenant.")
    versoes = repo.listar_versoes(tenant_id=inp.tenant_id, item_id=inp.item_id)
    alvo = next((v for v in versoes if v.id == inp.versao_id), None)
    if alvo is None:
        raise VersaoAusenteError(f"versão {inp.versao_id} inexistente no item.")
    if alvo.vigencia.revogado_em is not None:
        raise RuntimeError(f"versão {inp.versao_id} já revogada — nada a corrigir.")
    repo.revogar_versao(
        tenant_id=inp.tenant_id, versao_id=alvo.id, motivo=inp.motivo
    )
    substituta = ItemCatalogoVersao(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        item_id=inp.item_id,
        versao_n=proxima_versao_n(versoes),
        nome=inp.nome if inp.nome is not None else alvo.nome,
        unidade_medida=(
            inp.unidade_medida if inp.unidade_medida is not None else alvo.unidade_medida
        ),
        preco_padrao=(
            Preco(inp.preco_padrao) if inp.preco_padrao is not None else alvo.preco_padrao
        ),
        vigencia=JanelaVigencia(inicio=alvo.vigencia.inicio, fim=alvo.vigencia.fim),
        criado_por=inp.criado_por,
        descricao=inp.descricao if inp.descricao is not None else alvo.descricao,
        categoria=inp.categoria if inp.categoria is not None else alvo.categoria,
        motivo=f"correcao da v{alvo.versao_n}: {inp.motivo}",
    )
    repo.salvar_versao(substituta)
    return CorrigirVersaoOutput(versao_revogada_id=alvo.id, versao=substituta)


# === inativar_item (US-CAT-005 / ADR-0031) ===


@dataclass(frozen=True, slots=True)
class InativarItemInput:
    tenant_id: UUID
    item_id: UUID


def inativar_item(inp: InativarItemInput, *, repo: ItemCatalogoRepository) -> ItemCatalogo:
    """`status=inativo` (AC-CAT-005-1 — some de seleção/venda nova; histórico
    e versões ficam intactos). Já inativo → erro explícito (não no-op: evento
    duplicado sujaria a cadeia)."""
    item = repo.obter(tenant_id=inp.tenant_id, item_id=inp.item_id)
    if item is None:
        raise ItemAusenteError(f"item {inp.item_id} inexistente no tenant.")
    if item.status == StatusItem.INATIVO:
        raise ItemInativoError(f"item {inp.item_id} já está inativo.")
    inativado = replace(item, status=StatusItem.INATIVO)
    repo.salvar(inativado)
    return inativado


# === montar_kit (US-CAT-003) ===


@dataclass(frozen=True, slots=True)
class MontarKitInput:
    tenant_id: UUID
    kit_item_id: UUID
    componentes: tuple[tuple[UUID, Decimal], ...]  # (item_filho_id, quantidade)


def montar_kit(
    inp: MontarKitInput, *, repo: ItemCatalogoRepository
) -> list[KitComposicao]:
    """SUBSTITUI a composição do kit (idempotente por estado final).

    INV-PPS-KIT-SEM-CICLO: filho nunca é kit (1 nível); filho inativo/
    inexistente/repetido barra (validação no domínio). Preço de VENDA do kit é
    linha PRÓPRIA na tabela (TL-PPS-09) — montar não mexe em preço.
    """
    # P9 IDEMP-M1: serializa recomposições concorrentes do MESMO kit (o
    # DELETE+bulk_create do substituir_composicao não é atômico entre transações).
    repo.travar_item(tenant_id=inp.tenant_id, item_id=inp.kit_item_id)
    kit = repo.obter(tenant_id=inp.tenant_id, item_id=inp.kit_item_id)
    if kit is None:
        raise ItemAusenteError(f"item {inp.kit_item_id} inexistente no tenant.")
    if kit.status == StatusItem.INATIVO:
        raise ItemInativoError(f"kit {inp.kit_item_id} inativo — não recompõe.")
    composicao = [
        KitComposicao(
            kit_item_id=kit.id, item_filho_id=filho_id, quantidade=quantidade
        )
        for filho_id, quantidade in inp.componentes
    ]
    filhos = [
        f
        for filho_id, _ in inp.componentes
        if (f := repo.obter(tenant_id=inp.tenant_id, item_id=filho_id)) is not None
    ]
    validar_kit_sem_ciclo(kit=kit, filhos=filhos, composicao=composicao)
    repo.substituir_composicao(
        tenant_id=inp.tenant_id, kit_item_id=kit.id, composicao=composicao
    )
    return composicao
