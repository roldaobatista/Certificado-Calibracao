"""Use cases de regra de formação de preço (T-PRC-030 — US-PRC-001).

`publicar_regra`: consulta `CustoProvider`; COST_PLUS sob stub → 422
`CustoRealIndisponivel` (D-PRC-6 / INV-PRC-COSTPLUS-STUB); anti-retroativa
de vigência; encerra anterior na MESMA transação (lock 880_404 — caller
embrulha em `transaction.atomic`).

`revogar_regra`: one-shot `revogado_em` + motivo. Correção = revogar + recriar.

Molde: `src.application.produtos_pecas_servicos.item` (Input/Output frozen
dataclasses + repo Protocol injetado + advisory lock no repo Django).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.precificacao.entities import RegraFormacaoPreco
from src.domain.precificacao.enums import ModoFormacaoPreco
from src.domain.precificacao.erros import CustoRealIndisponivel
from src.domain.precificacao.portas import CustoProvider
from src.domain.precificacao.repository import RegraRepository
from src.domain.precificacao.transicoes import validar_vigencia_nao_retroativa
from src.domain.precificacao.value_objects import Percentual
from src.domain.shared.value_objects import JanelaVigencia


class RegraAusenteError(Exception):
    """Regra inexistente no tenant (RLS cobre cross-tenant) — view mapeia 404."""


# ---------------------------------------------------------------------------
# publicar_regra (US-PRC-001 / AC-PRC-001-3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PublicarRegraInput:
    tenant_id: UUID
    item_id: UUID
    modo: ModoFormacaoPreco
    criado_por: UUID
    agora: datetime  # tz-aware — injetado pela view (determinismo em testes)
    vigencia_inicio: datetime | None = None  # None = agora
    preco_fixo: Decimal | None = None
    custo_manual_declarado: Decimal | None = None
    custo_referencia_em: datetime | None = None
    margem_alvo_pct: Decimal | None = None
    margem_piso_pct: Decimal | None = None


@dataclass(frozen=True, slots=True)
class PublicarRegraOutput:
    regra: RegraFormacaoPreco
    regra_encerrada_id: UUID | None  # anterior cuja vigência foi fechada


def publicar_regra(
    inp: PublicarRegraInput,
    *,
    repo: RegraRepository,
    custo_provider: CustoProvider,
) -> PublicarRegraOutput:
    """Publica nova versão de regra de formação de preço (US-PRC-001).

    Anti-cost-plus-sob-stub (D-PRC-6 / INV-PRC-COSTPLUS-STUB): COST_PLUS
    exige `custo_provider.disponivel()` — stub retorna False → 422.

    Anti-retroativa (D-PRC-7): `vigencia_inicio >= max(agora, inicio_vigente)`.
    Encerra anterior na MESMA transação (caller DEVE usar `transaction.atomic`).
    Advisory lock (namespace 880_404) é chamado pelo repo Django ANTES da leitura
    — densidade `versao_n = max+1` fica serializada.

    Args:
      inp: dados da nova regra.
      repo: repositório Django (injeta advisory lock — chamar DENTRO de atomic).
      custo_provider: CustoProvider real ou StubCustoProvider.

    Raises:
      CustoRealIndisponivel: COST_PLUS sob stub (INV-PRC-COSTPLUS-STUB → 422).
      ValueError: vigência retroativa ou dados obrigatórios ausentes.
    """
    # Normaliza modo para enum (view pode passar string ou enum — robustez)
    modo = ModoFormacaoPreco(inp.modo) if isinstance(inp.modo, str) else inp.modo

    # Anti-cost-plus-sob-stub (D-PRC-6) — gate em tempo de CONFIGURAÇÃO
    if modo == ModoFormacaoPreco.COST_PLUS and not custo_provider.disponivel():
        raise CustoRealIndisponivel(
            "COST_PLUS exige provider de custo real disponível — stub ativo "
            "(INV-PRC-COSTPLUS-STUB / D-PRC-6). Provider real chega em "
            "GATE-PRC-CUSTEIO-REAL (módulo custeio-real N7)."
        )

    # Validação de campos obrigatórios por modo
    if modo == ModoFormacaoPreco.PRECO_FIXO and inp.preco_fixo is None:
        raise ValueError("modo PRECO_FIXO exige preco_fixo declarado.")
    if modo == ModoFormacaoPreco.MARGEM_ALVO:
        if inp.custo_manual_declarado is None:
            raise ValueError(
                "modo MARGEM_ALVO exige custo_manual_declarado (fonte Wave A — D-PRC-5)."
            )
        if inp.custo_referencia_em is None:
            raise ValueError(
                "modo MARGEM_ALVO exige custo_referencia_em (staleness — TL-PRC-07)."
            )

    # Advisory lock por (tenant, item) — serializa versao_n + encerramento (D-PRC-7)
    repo.travar_item(tenant_id=inp.tenant_id, item_id=inp.item_id)

    inicio = inp.vigencia_inicio if inp.vigencia_inicio is not None else inp.agora

    # Verifica vigente atual e valida não-retroatividade
    vigente_atual = repo.obter_vigente(
        tenant_id=inp.tenant_id, item_id=inp.item_id, em=inp.agora
    )
    validar_vigencia_nao_retroativa(
        inicio_nova=inicio, vigente_atual=vigente_atual, agora=inp.agora
    )

    # Calcula versao_n densa (max+1 sob lock)
    todas = repo.listar_por_item(tenant_id=inp.tenant_id, item_id=inp.item_id)
    versao_n = max((r.versao_n for r in todas), default=0) + 1

    regra = RegraFormacaoPreco(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        item_id=inp.item_id,
        modo=modo,
        vigencia=JanelaVigencia(inicio=inicio),
        versao_n=versao_n,
        criado_por=inp.criado_por,
        preco_fixo=inp.preco_fixo,
        custo_manual_declarado=inp.custo_manual_declarado,
        custo_referencia_em=inp.custo_referencia_em,
        margem_alvo_pct=Percentual(inp.margem_alvo_pct) if inp.margem_alvo_pct is not None else None,
        margem_piso_pct=Percentual(inp.margem_piso_pct) if inp.margem_piso_pct is not None else None,
    )

    # Encerra vigente anterior na MESMA transação (D-PRC-7)
    encerrada_id: UUID | None = None
    if vigente_atual is not None and vigente_atual.vigencia.fim is None:
        repo.encerrar_vigencia(
            tenant_id=inp.tenant_id, regra_id=vigente_atual.id, fim=inicio
        )
        encerrada_id = vigente_atual.id

    repo.salvar(regra)
    return PublicarRegraOutput(regra=regra, regra_encerrada_id=encerrada_id)


# ---------------------------------------------------------------------------
# revogar_regra (D-PRC-7 — correção = revogar + recriar)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RevogarRegraInput:
    tenant_id: UUID
    regra_id: UUID
    motivo: str  # ≥10 chars (INV-VIG-002 adaptada — auditoria obrigatória)
    revogado_por: UUID
    agora: datetime


def revogar_regra(inp: RevogarRegraInput, *, repo: RegraRepository) -> RegraFormacaoPreco:
    """One-shot `revogado_em` + motivo (D-PRC-7 / INV-PRC-REGRA-IMUTAVEL).

    Correção de regra errada = revogar (this) + publicar_regra (nova substituta).
    Regra revogada sai da exclusion btree_gist e nunca mais resolve.

    Raises:
      RegraAusenteError: regra inexistente no tenant (RLS cross-tenant seguro).
      ValueError: motivo < 10 chars.
      RuntimeError: regra já revogada.
    """
    if len(inp.motivo.strip()) < 10:
        raise ValueError("revogação exige motivo com ≥10 chars (INV-VIG-002).")

    regra = repo.obter(tenant_id=inp.tenant_id, regra_id=inp.regra_id)
    if regra is None:
        raise RegraAusenteError(f"regra {inp.regra_id} inexistente no tenant.")

    repo.revogar(
        tenant_id=inp.tenant_id,
        regra_id=inp.regra_id,
        revogado_em=inp.agora,
        motivo=inp.motivo,
    )
    return regra
