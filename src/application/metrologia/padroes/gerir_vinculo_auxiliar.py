"""Use case `gerir_vinculo_auxiliar` — criar/revogar VinculoAuxiliar (US-PAD-007-4).

cl. 6.4.5 (C-8): o equipamento auxiliar (termo-higrometro de sala, banho
termostatico, fonte de tensao estavel) que afeta o resultado do padrao
principal e modelado como vinculo temporal N:N `VinculoAuxiliar` (ADR-0030).
Este use case e o caminho pelo qual o gestor CRIA e REVOGA esses vinculos —
sem ele, a barreira INV-PAD-007 (`padrao_bloqueado_para_uso` reavalia auxiliares
vigentes) nunca dispara em producao, pois nao havia como vincular.

Validacoes na CRIACAO:
  - principal e auxiliar existem (mesmo tenant — RLS + obter_por_id).
  - principal != auxiliar.
  - o `padrao_auxiliar` tem `subtipo.eh_auxiliar` True (cl. 6.4.5 — so AUXILIAR_*
    entra como auxiliar; um padrao PRINCIPAL nao vira auxiliar de outro).
  - nao existe vinculo vigente DUPLICADO do mesmo par principal->auxiliar.

Use case PURO (recebe Protocols por DI). Append-only na criacao; revogacao liga
`revogado_em` (ADR-0030 — soft-delete temporal, nunca DELETE fisico).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.padroes.entities import VinculoAuxiliarSnapshot
from src.domain.metrologia.padroes.repository import (
    PadraoRepository,
    VinculoAuxiliarRepository,
)
from src.domain.metrologia.value_objects import Grandeza

from .registrar_recal_envio import PadraoNaoEncontradoError


class AuxiliarInvalidoError(Exception):
    """O padrao indicado como auxiliar nao tem subtipo AUXILIAR_* (cl. 6.4.5)."""


class VinculoCircularError(Exception):
    """principal == auxiliar — um padrao nao pode ser auxiliar de si mesmo."""


class VinculoJaExisteError(Exception):
    """Ja existe vinculo vigente do mesmo par principal->auxiliar (idempotente)."""


class VinculoNaoEncontradoError(Exception):
    def __init__(self, vinculo_id: UUID) -> None:
        super().__init__(f"VinculoAuxiliar {vinculo_id} nao encontrado.")


class VinculoJaRevogadoError(Exception):
    """Vinculo ja revogado (revogado_em != NULL) — revogacao idempotente."""


@dataclass(frozen=True, slots=True)
class CriarVinculoInput:
    tenant_id: UUID
    padrao_principal_id: UUID
    padrao_auxiliar_id: UUID
    grandeza_influencia: Grandeza
    vigencia_inicio: datetime


@dataclass(frozen=True, slots=True)
class RevogarVinculoInput:
    tenant_id: UUID
    vinculo_id: UUID
    revogado_em: datetime


@dataclass(frozen=True, slots=True)
class VinculoOutput:
    vinculo: VinculoAuxiliarSnapshot


def criar(
    inp: CriarVinculoInput,
    repo_padrao: PadraoRepository,
    repo_vinculo: VinculoAuxiliarRepository,
) -> VinculoOutput:
    if inp.padrao_principal_id == inp.padrao_auxiliar_id:
        raise VinculoCircularError

    principal = repo_padrao.obter_por_id(inp.padrao_principal_id)
    if principal is None:
        raise PadraoNaoEncontradoError(inp.padrao_principal_id)
    auxiliar = repo_padrao.obter_por_id(inp.padrao_auxiliar_id)
    if auxiliar is None:
        raise PadraoNaoEncontradoError(inp.padrao_auxiliar_id)

    if not auxiliar.subtipo.eh_auxiliar:
        raise AuxiliarInvalidoError(
            f"padrao {inp.padrao_auxiliar_id} tem subtipo {auxiliar.subtipo.value} "
            "(esperado AUXILIAR_* — cl. 6.4.5)."
        )

    # Anti-duplicata: ja ha vinculo vigente desse par?
    for v in repo_vinculo.listar_auxiliares_vigentes_de(inp.padrao_principal_id):
        if v.padrao_auxiliar_id == inp.padrao_auxiliar_id:
            raise VinculoJaExisteError

    snapshot = VinculoAuxiliarSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        padrao_principal_id=inp.padrao_principal_id,
        padrao_auxiliar_id=inp.padrao_auxiliar_id,
        grandeza_influencia=inp.grandeza_influencia,
        vigencia_inicio=inp.vigencia_inicio,
        revogado_em=None,
    )
    repo_vinculo.salvar_novo(snapshot)
    return VinculoOutput(vinculo=snapshot)


def revogar(
    inp: RevogarVinculoInput, repo_vinculo: VinculoAuxiliarRepository
) -> VinculoOutput:
    atual = repo_vinculo.obter_por_id(inp.vinculo_id)
    if atual is None:
        raise VinculoNaoEncontradoError(inp.vinculo_id)
    if atual.revogado_em is not None:
        raise VinculoJaRevogadoError

    if not repo_vinculo.revogar(inp.vinculo_id, inp.revogado_em):
        # Corrida: outra transacao revogou entre o read e o update.
        raise VinculoJaRevogadoError
    return VinculoOutput(vinculo=replace(atual, revogado_em=inp.revogado_em))
