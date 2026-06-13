"""Use cases de aprovação de desconto (T-PRC-032 — US-PRC-003/004).

`solicitar_aprovacao`: gera fingerprint canônico ADR-0029 do cálculo + contexto
tipado; alçada DONO obrigatória para cortesia 100% (D-PRC-13).

`decidir_aprovacao`: one-shot SOLICITADO→APROVADO|NEGADO; decisor != solicitante
(INV-PRC-APROVACAO-INDEPENDENTE); predicate `alcada_cobre` verifica papel;
recusa se fingerprint divergir (D-PRC-14); grava `justificativa_hash` no WORM
+ texto cru em `JustificativaDecisaoDesconto` (D-PRC-15).

Molde: `src.application.produtos_pecas_servicos.item` (Input/Output frozen).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.precificacao.entities import PedidoAprovacaoDesconto
from src.domain.precificacao.enums import Alcada, ContextoTipo, EstadoPedido
from src.domain.precificacao.erros import (
    AlcadaInsuficiente,
    FingerprintDivergente,
)
from src.domain.precificacao.repository import FaixaRepository, PedidoRepository
from src.domain.precificacao.transicoes import (
    alcada_para_pct,
    fingerprint_calculo,
    validar_decisor_independente,
)
from src.domain.precificacao.value_objects import CalculoPrecoResultado, Percentual

# Tipo para callable de hash injetável pela view
HashJustificativaFn = Callable[[str, UUID], str]
"""Callable(texto, tenant_id) → hash_versionado (ADR-0029 + HMAC-tenant ADR-0064)."""

SalvarJustificativaFn = Callable[[UUID, UUID, str], None]
"""Callable(pedido_id, tenant_id, texto) → None (persiste em JustificativaDecisaoDesconto)."""

# Hierarquia de alçadas (LIVRE < GERENTE < DONO)
_HIERARQUIA_ALCADA: dict[Alcada, int] = {
    Alcada.LIVRE: 0,
    Alcada.GERENTE: 1,
    Alcada.DONO: 2,
}


class PedidoAusenteError(Exception):
    """Pedido inexistente no tenant (RLS cross-tenant seguro) — view mapeia 404."""


def _alcada_papel_cobre(papel_alcada: Alcada, alcada_exigida: Alcada) -> bool:
    """Predicate: papel do decisor cobre a alçada exigida.

    Hierarquia: LIVRE < GERENTE < DONO. Papel com alçada >= exigida = pode decidir.
    """
    return _HIERARQUIA_ALCADA[papel_alcada] >= _HIERARQUIA_ALCADA[alcada_exigida]


# ---------------------------------------------------------------------------
# solicitar_aprovacao (US-PRC-003 / AC-PRC-003-1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SolicitarAprovacaoInput:
    tenant_id: UUID
    resultado_calculo: CalculoPrecoResultado
    desconto_pct: Decimal  # pct solicitado (deve bater com resultado)
    contexto_tipo: ContextoTipo
    solicitante_id: UUID
    agora: datetime
    contexto_id: UUID | None = None  # FK aditiva quando módulo consumidor existir


@dataclass(frozen=True, slots=True)
class SolicitarAprovacaoOutput:
    pedido: PedidoAprovacaoDesconto


def solicitar_aprovacao(
    inp: SolicitarAprovacaoInput,
    *,
    repo_pedido: PedidoRepository,
    repo_faixa: FaixaRepository,
) -> SolicitarAprovacaoOutput:
    """Abre pedido de aprovação de desconto (US-PRC-003).

    Gera `fingerprint_calculo` canônico (D-PRC-14): hash ADR-0029 de
    (entradas + refs + pct). Alçada DONO obrigatória para cortesia 100%
    (D-PRC-13). Snapshot probatório embutido no pedido (eco das entradas
    para replay — AC-PRC-002-3).

    Args:
      inp: entradas do pedido.
      repo_pedido: repositório de pedidos.
      repo_faixa: repositório de faixas (para determinar alçada exigida).

    Returns:
      SolicitarAprovacaoOutput com o pedido persistido.
    """
    desconto = Percentual(inp.desconto_pct)
    cortesia = desconto.valor == Decimal("100")

    faixas = repo_faixa.listar(tenant_id=inp.tenant_id)

    if cortesia:
        alcada_exigida = Alcada.DONO
    else:
        alcada_exigida = alcada_para_pct(desconto, faixas)

    # Gera fingerprint canônico (D-PRC-14 / TL-PRC-08)
    eco = inp.resultado_calculo.eco_entradas
    refs = {
        "motor_versao": inp.resultado_calculo.motor_versao,
        "faixas_versao": inp.resultado_calculo.faixas_versao or "",
        "parametros_versao": str(inp.resultado_calculo.parametros_versao),
    }
    if inp.resultado_calculo.imposto_ref is not None:
        refs["imposto_id"] = str(inp.resultado_calculo.imposto_ref[0])
        refs["imposto_versao"] = str(inp.resultado_calculo.imposto_ref[1])

    fp = fingerprint_calculo(
        entradas=eco,
        refs=refs,
        desconto_pct=inp.desconto_pct,
    )

    # Snapshot probatório: eco das entradas + refs (sem valores comerciais — D-PRC-4)
    snapshot = json.dumps(
        {"entradas": eco, "refs": refs, "desconto_pct": str(inp.desconto_pct)},
        ensure_ascii=False,
        sort_keys=True,
    )

    pedido = PedidoAprovacaoDesconto(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        contexto_tipo=inp.contexto_tipo,
        contexto_id=inp.contexto_id,
        pct_solicitado=desconto,
        cortesia=cortesia,
        alcada_exigida=alcada_exigida,
        fingerprint_calculo=fp,
        estado=EstadoPedido.SOLICITADO,
        solicitante_id=inp.solicitante_id,
        snapshot_probatorio=snapshot,
        criado_em=inp.agora,
    )
    repo_pedido.salvar(pedido)
    return SolicitarAprovacaoOutput(pedido=pedido)


# ---------------------------------------------------------------------------
# decidir_aprovacao (US-PRC-004 / AC-PRC-004-1/3/4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DecidirAprovacaoInput:
    tenant_id: UUID
    pedido_id: UUID
    estado_novo: EstadoPedido  # APROVADO ou NEGADO
    decisor_id: UUID
    papel_decisor: Alcada  # papel do decisor no sistema
    justificativa: str  # texto cru → tabela-par; hash → WORM
    fingerprint_calculo_atual: str  # recalculado pelo caller no momento da decisão
    agora: datetime
    hash_justificativa_fn: HashJustificativaFn  # HMAC-tenant ADR-0029 injetado pela view


@dataclass(frozen=True, slots=True)
class DecidirAprovacaoOutput:
    pedido_id: UUID
    estado: EstadoPedido
    justificativa_hash: str


def decidir_aprovacao(
    inp: DecidirAprovacaoInput,
    *,
    repo_pedido: PedidoRepository,
    salvar_justificativa_fn: SalvarJustificativaFn,
) -> DecidirAprovacaoOutput:
    """Decide um pedido de aprovação de desconto (US-PRC-004).

    Regras:
    - One-shot: SOLICITADO → APROVADO|NEGADO (trigger garante no banco).
    - Independência: decisor != solicitante (INV-PRC-APROVACAO-INDEPENDENTE).
    - Alçada: papel_decisor deve cobrir alcada_exigida (predicate `alcada_cobre`).
    - Fingerprint: fingerprint_calculo_atual deve bater com o do pedido (D-PRC-14).
    - Justificativa: hash → WORM (`justificativa_hash`); texto cru → tabela-par.

    Args:
      inp: entradas da decisão.
      repo_pedido: repositório de pedidos.
      salvar_justificativa_fn: callable(pedido_id, tenant_id, texto) → None.

    Returns:
      DecidirAprovacaoOutput com estado final e hash.

    Raises:
      PedidoAusenteError: pedido inexistente no tenant → 404.
      DecisorNaoIndependente: decisor == solicitante → 422.
      AlcadaInsuficiente: papel não cobre a alçada exigida → 403.
      FingerprintDivergente: cálculo mudou desde a solicitação → 422.
      RuntimeError: pedido não está SOLICITADO (one-shot) → 409.
    """
    if inp.estado_novo not in (EstadoPedido.APROVADO, EstadoPedido.NEGADO):
        raise ValueError(
            f"estado_novo deve ser APROVADO ou NEGADO (recebeu {inp.estado_novo})."
        )

    pedido = repo_pedido.obter(tenant_id=inp.tenant_id, pedido_id=inp.pedido_id)
    if pedido is None:
        raise PedidoAusenteError(f"pedido {inp.pedido_id} inexistente no tenant.")

    # Independência: decisor != solicitante (INV-PRC-APROVACAO-INDEPENDENTE)
    validar_decisor_independente(
        decisor_id=inp.decisor_id, solicitante_id=pedido.solicitante_id
    )

    # Alçada: papel do decisor deve cobrir a exigida (predicate `alcada_cobre`)
    if not _alcada_papel_cobre(inp.papel_decisor, pedido.alcada_exigida):
        raise AlcadaInsuficiente(
            f"papel {inp.papel_decisor.value} não cobre alçada exigida "
            f"{pedido.alcada_exigida.value} — "
            "gerente não pode decidir faixa DONO (INV-PRC-APROVACAO-INDEPENDENTE / "
            "predicate alcada_cobre)."
        )

    # Fingerprint: cálculo não pode ter mudado desde a solicitação (D-PRC-14)
    if inp.fingerprint_calculo_atual != pedido.fingerprint_calculo:
        raise FingerprintDivergente(
            "fingerprint do cálculo vigente diverge do registrado na solicitação — "
            "o cálculo foi refeito com entradas diferentes (preço, faixas ou parâmetros "
            "mudaram). Refaça o cálculo e solicite nova aprovação (D-PRC-14)."
        )

    # Gera hash da justificativa (ADR-0029 + HMAC-tenant — D-PRC-15)
    justificativa_hash = inp.hash_justificativa_fn(inp.justificativa, inp.tenant_id)

    # One-shot: UPDATE escopado em SOLICITADO (trigger no banco garante)
    repo_pedido.decidir(
        tenant_id=inp.tenant_id,
        pedido_id=inp.pedido_id,
        estado=inp.estado_novo,
        decisor_id=inp.decisor_id,
        justificativa_hash=justificativa_hash,
        decidido_em=inp.agora,
    )

    # Texto cru em tabela-par mutável (AC-PRC-004-3 — vendedor lê justificativa)
    salvar_justificativa_fn(inp.pedido_id, inp.tenant_id, inp.justificativa)

    return DecidirAprovacaoOutput(
        pedido_id=inp.pedido_id,
        estado=inp.estado_novo,
        justificativa_hash=justificativa_hash,
    )
