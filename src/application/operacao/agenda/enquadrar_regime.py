"""Use case `enquadrar_regime` — humano grava override RegimeJornadaColaborador (T-AGE-038 / D-AGE-15).

Apenas humano (RH/gerente/advogado) chama este use case. IA NUNCA chama automaticamente
(INV-AG-REGIME-001 / R6). INSERT-com-vigência (não update — histórico preservado).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.operacao.agenda.entities import RegimeJornadaColaborador
from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
from src.domain.operacao.agenda.portas import EventoAgendaRepository


@dataclass(frozen=True, slots=True)
class EnquadrarRegimeInput:
    """Payload de override de regime — NUNCA chamado por IA automaticamente (INV-AG-REGIME-001)."""

    tenant_id: UUID
    colaborador_id: UUID
    regime: RegimeJornada
    vigencia_inicio: date
    definido_por_usuario_id: UUID
    justificativa: str
    vigencia_fim: date | None = None


@dataclass(frozen=True, slots=True)
class EnquadrarRegimeOutput:
    override: RegimeJornadaColaborador


def executar(
    inp: EnquadrarRegimeInput,
    *,
    repo: EventoAgendaRepository,
) -> EnquadrarRegimeOutput:
    """Grava override de regime (INSERT-com-vigência). IA nunca chama isto (R6)."""
    if not inp.justificativa.strip():
        raise ValueError("Justificativa de enquadramento é obrigatória.")

    agora = datetime.now(UTC)

    override = RegimeJornadaColaborador(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        colaborador_id=inp.colaborador_id,
        regime=inp.regime,
        vigencia_inicio=inp.vigencia_inicio,
        vigencia_fim=inp.vigencia_fim,
        definido_por_usuario_id=inp.definido_por_usuario_id,
        fonte=FonteRegime.OVERRIDE_HUMANO,  # IA nunca grava override
        criado_em=agora,
        justificativa=inp.justificativa,
    )
    repo.salvar_regime_override(override)

    return EnquadrarRegimeOutput(override=override)
