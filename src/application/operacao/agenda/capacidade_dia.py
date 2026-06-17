"""Use case `capacidade_dia` — indicador de ocupação do dia (T-AGE-037 / D-AGE-11 / US-AG-010).

Retorna ``{horas_alocadas, horas_uteis, pct, alerta}`` onde alerta ∈ {None, 'atencao', 'critico'}.
Limites: 75% = atenção, 90% = crítico (D-AGE-11). Default 8h úteis se ``CapacidadeTecnico``
não cadastrada.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.domain.operacao.agenda.portas import EventoAgendaRepository

_HORAS_UTEIS_DEFAULT = 8.0
_LIMITE_ATENCAO = 0.75
_LIMITE_CRITICO = 0.90


@dataclass(frozen=True, slots=True)
class CapacidadeDiaInput:
    tenant_id: UUID
    tecnico_id: UUID
    data: date


@dataclass(frozen=True, slots=True)
class CapacidadeDiaOutput:
    horas_alocadas: float
    horas_uteis: float
    pct: float
    alerta: str | None  # None | 'atencao' | 'critico'


def executar(
    inp: CapacidadeDiaInput,
    *,
    repo: EventoAgendaRepository,
) -> CapacidadeDiaOutput:
    """Calcula ocupação do dia para o técnico."""
    eventos = repo.listar_por_tecnico_no_dia(
        tenant_id=inp.tenant_id,
        tecnico_id=inp.tecnico_id,
        data=inp.data,
    )

    minutos_alocados = sum(
        (ev.termina_at - ev.inicia_at).total_seconds() / 60
        for ev in eventos
        if ev.aloca_em_umc
    )
    horas_alocadas = minutos_alocados / 60.0

    # TODO Fatia 3: buscar CapacidadeTecnico real via repositório
    horas_uteis = _HORAS_UTEIS_DEFAULT

    pct = horas_alocadas / horas_uteis if horas_uteis > 0 else 0.0

    alerta: str | None = None
    if pct >= _LIMITE_CRITICO:
        alerta = "critico"
    elif pct >= _LIMITE_ATENCAO:
        alerta = "atencao"

    return CapacidadeDiaOutput(
        horas_alocadas=round(horas_alocadas, 2),
        horas_uteis=horas_uteis,
        pct=round(pct, 4),
        alerta=alerta,
    )
