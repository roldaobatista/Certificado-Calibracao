"""Use cases de ciclo de vida do orçamento — T-ORC-032/034 (Fatia 2 / Onda 2b).

Transições D-ORC-3 que seguem o rascunho:
  - `enviar_orcamento`  : rascunho -> enviado (congela snapshot V1 + cria LinkPublico).
  - `recusar_orcamento` : enviado  -> recusado (revoga link).
  - `cancelar_orcamento`: rascunho -> cancelado (409 se convertido — terminal).
  - `expirar_orcamentos`: enviado  -> expirado (job idempotente por orcamento_id).

A publicação dos eventos de bus (`orcamento.enviado`/`.recusado`/`.expirado`,
outbox=True) é feita pela CAMADA DE INFRA (view/endpoint) dentro do mesmo
`transaction.atomic` (transactional outbox — molde precificacao); estes use cases
retornam os dados necessários e NÃO importam o publicador de eventos.

Token do LinkPublico = `secrets.token_urlsafe(32)` (256 bits >= 128, ADV-ORC-08a).
Expiração (job): comparação em UTC com `validade.fim` (TL-ORC MÉDIO-3 —
GATE-ORC-TIMEZONE-TENANT quando houver fuso por tenant).

Caller (view) abre `transaction.atomic`. Refs: spec §4/§6; D-ORC-3/7/8/19; AC-ORC-002/008;
INV-ORC-CONVERTIDO-TERMINAL / EXP-001.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.domain.comercial.orcamentos.calculo import montar_snapshot_versao
from src.domain.comercial.orcamentos.entities import (
    LinkPublico,
    Orcamento,
    VersaoOrcamento,
)
from src.domain.comercial.orcamentos.enums import EstadoOrcamento
from src.domain.comercial.orcamentos.erros import (
    EstadoInvalido,
    OrcamentoConvertido,
    OrcamentoSemItens,
)
from src.domain.comercial.orcamentos.repository import OrcamentoRepository
from src.domain.comercial.orcamentos.transicoes import validar_transicao

_DIAS_LINK_DEFAULT = 30
_TOKEN_NBYTES = 32  # secrets.token_urlsafe(32) -> 256 bits (>= 128, ADV-ORC-08a)
_LIMITE_EXPIRACAO_LOTE = 1000  # Wave A: lote por chamada do job (GATE-ORC-EXPIRY-JOB)


class OrcamentoNaoEncontrado(EstadoInvalido):
    """Orçamento inexistente no tenant (404 lógico)."""

    codigo = "orcamento_nao_encontrado"
    http_status = 404


def _carregar(orcamento_id: UUID, tenant_id: UUID, *, repo: OrcamentoRepository) -> Orcamento:
    orcamento = repo.get_by_id(orcamento_id, tenant_id=tenant_id)
    if orcamento is None:
        raise OrcamentoNaoEncontrado(
            f"orcamento {orcamento_id} inexistente neste tenant.",
            orcamento_id=str(orcamento_id),
        )
    return orcamento


def _revogar_link_ativo(
    orcamento_id: UUID, tenant_id: UUID, *, repo: OrcamentoRepository, agora: datetime, motivo: str
) -> None:
    link = repo.get_link_ativo(orcamento_id, tenant_id=tenant_id)
    if link is not None:
        repo.revogar_link(link.id, revogado_em=agora, motivo=motivo)


# =====================================================================
# enviar_orcamento (T-ORC-032)
# =====================================================================


@dataclass(frozen=True, slots=True)
class EnviarOrcamentoInput:
    tenant_id: UUID
    orcamento_id: UUID
    agora: datetime
    expira_em: datetime | None = None  # default: validade.fim, senão agora + 30 dias


@dataclass(frozen=True, slots=True)
class EnviarOrcamentoOutput:
    orcamento: Orcamento
    versao: VersaoOrcamento
    link: LinkPublico


def enviar_orcamento(
    inp: EnviarOrcamentoInput, *, repo: OrcamentoRepository
) -> EnviarOrcamentoOutput:
    """Congela a versão V1 + cria LinkPublico + transiciona rascunho->enviado (AC-ORC-002)."""
    orcamento = _carregar(inp.orcamento_id, inp.tenant_id, repo=repo)
    if orcamento.estado == EstadoOrcamento.CONVERTIDO:
        raise OrcamentoConvertido(
            f"orcamento {inp.orcamento_id} ja convertido (INV-ORC-CONVERTIDO-TERMINAL).",
            orcamento_id=str(inp.orcamento_id),
        )
    validar_transicao(orcamento.estado, EstadoOrcamento.ENVIADO)

    versao = repo.get_versao_ativa(inp.orcamento_id, tenant_id=inp.tenant_id)
    if versao is None:
        raise EstadoInvalido(
            f"orcamento {inp.orcamento_id} sem versao corrente — estado inconsistente.",
            orcamento_id=str(inp.orcamento_id),
        )
    itens = repo.listar_itens_versao(versao.id, tenant_id=inp.tenant_id)
    if not itens:
        raise OrcamentoSemItens(
            f"orcamento {inp.orcamento_id} sem itens — nada a propor (AC-ORC-002).",
            orcamento_id=str(inp.orcamento_id),
        )

    snapshot = montar_snapshot_versao(orcamento, itens)
    versao = repo.congelar_versao(versao.id, tenant_id=inp.tenant_id, snapshot=snapshot)

    expira_em = (
        inp.expira_em or orcamento.validade.fim or (inp.agora + timedelta(days=_DIAS_LINK_DEFAULT))
    )
    link = repo.salvar_link(
        LinkPublico(
            id=uuid4(),
            orcamento_id=inp.orcamento_id,
            tenant_id=inp.tenant_id,
            token=secrets.token_urlsafe(_TOKEN_NBYTES),
            expira_em=expira_em,
            criado_em=inp.agora,
        )
    )

    orcamento = repo.atualizar_estado(
        inp.orcamento_id, tenant_id=inp.tenant_id, novo_estado=EstadoOrcamento.ENVIADO
    )
    return EnviarOrcamentoOutput(orcamento=orcamento, versao=versao, link=link)


# =====================================================================
# recusar_orcamento (T-ORC-034)
# =====================================================================


@dataclass(frozen=True, slots=True)
class RecusarOrcamentoInput:
    tenant_id: UUID
    orcamento_id: UUID
    motivo: str
    agora: datetime


def recusar_orcamento(inp: RecusarOrcamentoInput, *, repo: OrcamentoRepository) -> Orcamento:
    """enviado -> recusado; revoga o LinkPublico ativo (AC-ORC-008)."""
    orcamento = _carregar(inp.orcamento_id, inp.tenant_id, repo=repo)
    if orcamento.estado == EstadoOrcamento.CONVERTIDO:
        raise OrcamentoConvertido(
            f"orcamento {inp.orcamento_id} ja convertido (INV-ORC-CONVERTIDO-TERMINAL).",
            orcamento_id=str(inp.orcamento_id),
        )
    validar_transicao(orcamento.estado, EstadoOrcamento.RECUSADO)
    _revogar_link_ativo(
        inp.orcamento_id, inp.tenant_id, repo=repo, agora=inp.agora, motivo="orcamento recusado"
    )
    return repo.atualizar_estado(
        inp.orcamento_id, tenant_id=inp.tenant_id, novo_estado=EstadoOrcamento.RECUSADO
    )


# =====================================================================
# cancelar_orcamento (T-ORC-034)
# =====================================================================


@dataclass(frozen=True, slots=True)
class CancelarOrcamentoInput:
    tenant_id: UUID
    orcamento_id: UUID
    agora: datetime
    motivo: str | None = None


def cancelar_orcamento(inp: CancelarOrcamentoInput, *, repo: OrcamentoRepository) -> Orcamento:
    """rascunho -> cancelado; 409 se já convertido (INV-ORC-CONVERTIDO-TERMINAL / AC-ORC-008)."""
    orcamento = _carregar(inp.orcamento_id, inp.tenant_id, repo=repo)
    if orcamento.estado == EstadoOrcamento.CONVERTIDO:
        raise OrcamentoConvertido(
            f"orcamento {inp.orcamento_id} ja convertido — nao pode ser cancelado.",
            orcamento_id=str(inp.orcamento_id),
        )
    validar_transicao(orcamento.estado, EstadoOrcamento.CANCELADO)
    _revogar_link_ativo(
        inp.orcamento_id, inp.tenant_id, repo=repo, agora=inp.agora, motivo="orcamento cancelado"
    )
    return repo.atualizar_estado(
        inp.orcamento_id, tenant_id=inp.tenant_id, novo_estado=EstadoOrcamento.CANCELADO
    )


# =====================================================================
# expirar_orcamentos (T-ORC-034 — job idempotente)
# =====================================================================


@dataclass(frozen=True, slots=True)
class ExpirarOrcamentosInput:
    tenant_id: UUID
    agora: datetime  # tz-aware (UTC) — comparação com validade.fim


@dataclass(frozen=True, slots=True)
class OrcamentoExpirado:
    orcamento_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str


def expirar_orcamentos(
    inp: ExpirarOrcamentosInput, *, repo: OrcamentoRepository
) -> list[OrcamentoExpirado]:
    """Expira orçamentos ENVIADOS com validade vencida (INV-ORC-EXP-001).

    Idempotente: só processa estado ENVIADO; já-expirados ficam fora do filtro.
    Comparação em UTC (TL-ORC MÉDIO-3 / GATE-ORC-TIMEZONE-TENANT).
    """
    enviados = repo.listar(
        tenant_id=inp.tenant_id,
        estado=EstadoOrcamento.ENVIADO,
        limit=_LIMITE_EXPIRACAO_LOTE,
    )
    expirados: list[OrcamentoExpirado] = []
    for o in enviados:
        if o.validade.fim is None or o.validade.fim > inp.agora:
            continue  # sem expiração automática ou ainda vigente
        validar_transicao(o.estado, EstadoOrcamento.EXPIRADO)
        _revogar_link_ativo(
            o.id, inp.tenant_id, repo=repo, agora=inp.agora, motivo="orcamento expirado"
        )
        repo.atualizar_estado(o.id, tenant_id=inp.tenant_id, novo_estado=EstadoOrcamento.EXPIRADO)
        expirados.append(
            OrcamentoExpirado(
                orcamento_id=o.id,
                cliente_referencia_hash=o.cliente_referencia_hash,
                cliente_key_id=o.cliente_key_id,
            )
        )
    return expirados
