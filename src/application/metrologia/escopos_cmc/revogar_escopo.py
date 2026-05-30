"""Use case `revogar_escopo` — US-ECMC-003 (M6 T-ECMC-023).

Revogação one-shot (ADR-0031 soft-delete B): estado REVOGADO + `revogado_em` +
`motivo_revogacao` (≥10 chars canon ADR-0029). NUNCA DELETE físico (escopo
sustenta certificado RBC — retenção 25a cl. 8.4). Bloqueio prospectivo: a partir
da revogação o escopo deixa de cobrir; certificados já emitidos sob ele continuam
defensáveis pelo snapshot congelado (RBC-NC-05). Use case PURO (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo
from src.domain.metrologia.escopos_cmc.repository import EscopoRepository
from src.domain.metrologia.escopos_cmc.transicoes import validar_motivo_revogacao


class EscopoNaoEncontradoError(Exception):
    def __init__(self, escopo_id: UUID) -> None:
        super().__init__(f"Escopo {escopo_id} não encontrado neste tenant.")


class JaRevogadoError(Exception):
    def __init__(self) -> None:
        super().__init__("Escopo já revogado (revogação é one-shot — ADR-0031).")


@dataclass(frozen=True, slots=True)
class RevogarEscopoInput:
    tenant_id: UUID
    escopo_id: UUID
    motivo: str
    revogado_em: datetime

    def __post_init__(self) -> None:
        # INV-ECMC-003 / ADR-0030 — motivo >=10 chars
        validar_motivo_revogacao(self.motivo)
        if self.revogado_em.tzinfo is None:
            raise ValueError("revogar_escopo: revogado_em exige tz-aware (INV-VIG-004).")


@dataclass(frozen=True, slots=True)
class RevogarEscopoOutput:
    escopo_id: UUID


def executar(inp: RevogarEscopoInput, repo: EscopoRepository) -> RevogarEscopoOutput:
    atual = repo.obter_por_id(inp.escopo_id)
    if atual is None or atual.tenant_id != inp.tenant_id:
        raise EscopoNaoEncontradoError(inp.escopo_id)
    if atual.estado is EstadoEscopo.REVOGADO:
        raise JaRevogadoError
    if not repo.revogar(
        escopo_id=inp.escopo_id, revogado_em=inp.revogado_em, motivo=inp.motivo
    ):
        raise JaRevogadoError
    return RevogarEscopoOutput(escopo_id=inp.escopo_id)
