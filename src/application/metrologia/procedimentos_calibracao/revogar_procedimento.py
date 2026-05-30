"""Use case `revogar_procedimento` — US-PROC-004 (M7 T-PROC-033).

Revogação one-shot (ADR-0031 soft-delete B): estado REVOGADO + `revogado_em` +
`motivo_revogacao` (≥10 chars canon ADR-0029). NUNCA DELETE físico (procedimento
sustenta certificado — retenção 25a cl. 8.4). Bloqueio prospectivo: a partir da
revogação o procedimento deixa de resolver; calibrações já configuradas sob ele
continuam defensáveis pelo snapshot congelado. Use case PURO (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.procedimentos_calibracao.enums import EstadoProcedimento
from src.domain.metrologia.procedimentos_calibracao.repository import (
    ProcedimentoRepository,
)
from src.domain.metrologia.procedimentos_calibracao.transicoes import (
    validar_motivo_revogacao,
)


class ProcedimentoNaoEncontradoError(Exception):
    def __init__(self, procedimento_id: UUID) -> None:
        super().__init__(f"Procedimento {procedimento_id} não encontrado neste tenant.")


class JaRevogadoError(Exception):
    def __init__(self) -> None:
        super().__init__("Procedimento já revogado (revogação é one-shot — ADR-0031).")


@dataclass(frozen=True, slots=True)
class RevogarProcedimentoInput:
    tenant_id: UUID
    procedimento_id: UUID
    motivo: str
    revogado_em: datetime

    def __post_init__(self) -> None:
        validar_motivo_revogacao(self.motivo)  # INV-PROC-003 / ADR-0030
        if self.revogado_em.tzinfo is None:
            raise ValueError("revogar_procedimento: revogado_em exige tz-aware.")


@dataclass(frozen=True, slots=True)
class RevogarProcedimentoOutput:
    procedimento_id: UUID


def executar(
    inp: RevogarProcedimentoInput, repo: ProcedimentoRepository
) -> RevogarProcedimentoOutput:
    atual = repo.obter_por_id(inp.procedimento_id)
    if atual is None or atual.tenant_id != inp.tenant_id:
        raise ProcedimentoNaoEncontradoError(inp.procedimento_id)
    if atual.estado is EstadoProcedimento.REVOGADO:
        raise JaRevogadoError
    if not repo.revogar(
        procedimento_id=inp.procedimento_id,
        revogado_em=inp.revogado_em,
        motivo=inp.motivo,
    ):
        raise JaRevogadoError
    return RevogarProcedimentoOutput(procedimento_id=inp.procedimento_id)
