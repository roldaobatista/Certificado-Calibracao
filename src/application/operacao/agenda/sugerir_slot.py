"""Use case `sugerir_slot` — US-AG-006: RT substituto → competência → livre 7d.

Lógica interna (horizonte fixo 7d). RT substituto via STUB na Fatia 2;
adapter real na Fatia 3 (PLAN-AGE-01/RBC-AGE-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from src.domain.operacao.agenda.entities import EventoAgenda
from src.domain.operacao.agenda.jornada import EventoSimples, proximo_slot_valido
from src.domain.operacao.agenda.portas import (
    ColaboradorAgendaPort,
    EventoAgendaRepository,
    RTSubstitutoPort,
)
from src.domain.operacao.agenda.value_objects import Janela, RegimeJornadaResolvido


def _para_evento_simples(ev: EventoAgenda) -> EventoSimples:
    """Converte EventoAgenda → EventoSimples para algoritmo de sugestão de slot."""
    return EventoSimples(
        tipo=ev.tipo,
        janela=Janela(inicia_at=ev.inicia_at, termina_at=ev.termina_at),
    )

_HORIZONTE_DIAS = 7


@dataclass(frozen=True, slots=True)
class SugerirSlotInput:
    tenant_id: UUID
    tecnico_id: UUID
    duracao_minutos: int
    perfil_tenant: str  # server-side
    a_partir_de: datetime | None = None
    acordo_coletivo_12h: bool = False


@dataclass(frozen=True, slots=True)
class SugerirSlotOutput:
    slot_sugerido: datetime | None  # None = nenhum encontrado no horizonte 7d
    horizonte_fim: date


def executar(
    inp: SugerirSlotInput,
    *,
    repo: EventoAgendaRepository,
    colaborador_port: ColaboradorAgendaPort,
    rt_port: RTSubstitutoPort,
) -> SugerirSlotOutput:
    """Sugere próximo slot livre nos 7 dias seguintes."""
    agora = inp.a_partir_de or datetime.now(UTC)
    horizonte_fim = (agora + timedelta(days=_HORIZONTE_DIAS)).date()

    # Regime server-side (proximo_slot_valido é perfil-agnóstico)
    regime_resolvido: RegimeJornadaResolvido = colaborador_port.regime_jornada(
        tenant_id=inp.tenant_id,
        colaborador_id=inp.tecnico_id,
        na_data=agora.date(),
    )

    # Eventos no horizonte (para o algoritmo de busca de slot)
    eventos_horizonte_raw: list[EventoAgenda] = []
    for i in range(_HORIZONTE_DIAS + 1):
        dia = (agora + timedelta(days=i)).date()
        eventos_horizonte_raw.extend(
            repo.listar_por_tecnico_no_dia(
                tenant_id=inp.tenant_id,
                tecnico_id=inp.tecnico_id,
                data=dia,
            )
        )
    eventos_horizonte = [_para_evento_simples(ev) for ev in eventos_horizonte_raw]

    from src.domain.operacao.agenda.value_objects import TecnicoJornada

    tecnico_jornada = TecnicoJornada(
        tenant_id=inp.tenant_id,
        colaborador_id=inp.tecnico_id,
        is_tecnico_campo=True,
        aloca_em_umc=True,
    )

    slot = proximo_slot_valido(
        tecnico=tecnico_jornada,
        regime=regime_resolvido.regime,
        duracao_minutos=inp.duracao_minutos,
        eventos_existentes=eventos_horizonte,
        a_partir_de=agora,
        acordo_coletivo_12h=inp.acordo_coletivo_12h,
    )

    # Descarta slot fora do horizonte de 7d
    if slot is not None and slot.date() > horizonte_fim:
        slot = None

    return SugerirSlotOutput(slot_sugerido=slot, horizonte_fim=horizonte_fim)
