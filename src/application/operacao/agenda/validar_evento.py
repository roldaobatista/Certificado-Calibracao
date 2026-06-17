"""Use case `validar_evento` — dry-run pré-save (T-AGE-030 / US-AG-002 / R9).

POST /agenda/validar — executa overlap + jornada + CNH SEM gravar.
Retorna ``{ok: bool, violacoes: list[dict]}`` com uma entrada por dimensão que
falhar. Nunca persiste nada (dry-run garantido).

Molde: `contas_receber/criar_titulo_manual.py` (use case fino, frozen+slots).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.domain.operacao.agenda.entities import EventoAgenda
from src.domain.operacao.agenda.enums import RegimeJornada
from src.domain.operacao.agenda.jornada import EventoSimples, validar_jornada_umc
from src.domain.operacao.agenda.portas import (
    ColaboradorAgendaPort,
    EventoAgendaRepository,
    RTSubstitutoPort,
)
from src.domain.operacao.agenda.value_objects import Janela, TecnicoJornada


def _para_evento_simples(ev: EventoAgenda) -> EventoSimples:
    """Converte EventoAgenda → EventoSimples para validação de jornada."""
    return EventoSimples(
        tipo=ev.tipo,
        janela=Janela(inicia_at=ev.inicia_at, termina_at=ev.termina_at),
    )


@dataclass(frozen=True, slots=True)
class ValidarEventoInput:
    """Payload do dry-run de validação.

    ``perfil_tenant`` vem resolvido server-side pelo caller (INV-AG-PERFIL-001).
    ``regime_jornada`` NUNCA vem do payload — resolvido via porta (INV-AG-REGIME-001).
    """

    tenant_id: UUID
    tecnico_id: UUID
    janela: Janela
    aloca_em_umc: bool
    perfil_tenant: str  # A/B/C/D — server-side
    acordo_coletivo_12h: bool = False


@dataclass(frozen=True, slots=True)
class ValidarEventoOutput:
    ok: bool
    violacoes: list[dict[str, object]] = field(default_factory=list)


def executar(
    inp: ValidarEventoInput,
    *,
    repo: EventoAgendaRepository,
    colaborador_port: ColaboradorAgendaPort,
    rt_port: RTSubstitutoPort,
) -> ValidarEventoOutput:
    """Dry-run: valida sem gravar. Retorna todas as violações encontradas (R9).

    Dimensões validadas:
    1. Overlap com eventos existentes do técnico no dia.
    2. Jornada UMC (regime via porta — perfil-agnóstico, D-AGE-4).
    3. CNH do motorista (quando ``aloca_em_umc=True`` e regime motorista).
    """
    violacoes: list[dict[str, object]] = []

    data_slot: date = inp.janela.inicia_at.date()

    # 1. Overlap: listar eventos do técnico no dia e verificar sobreposição
    eventos_dia = repo.listar_por_tecnico_no_dia(
        tenant_id=inp.tenant_id,
        tecnico_id=inp.tecnico_id,
        data=data_slot,
    )

    for ev in eventos_dia:
        janela_ev = Janela(inicia_at=ev.inicia_at, termina_at=ev.termina_at)
        if janela_ev.sobrepoe(inp.janela):
            violacoes.append(
                {
                    "dimensao": "overlap",
                    "codigo": "CONFLITO_AGENDA",
                    "detalhe": (
                        f"Técnico já tem evento {ev.id} das "
                        f"{ev.inicia_at.strftime('%H:%M')} às "
                        f"{ev.termina_at.strftime('%H:%M')}."
                    ),
                    "evento_id": str(ev.id),
                }
            )

    # 2. Jornada UMC (só se aloca_em_umc)
    if inp.aloca_em_umc:
        regime_resolvido = colaborador_port.regime_jornada(
            tenant_id=inp.tenant_id,
            colaborador_id=inp.tecnico_id,
            na_data=data_slot,
        )
        tecnico_jornada = TecnicoJornada(
            tenant_id=inp.tenant_id,
            colaborador_id=inp.tecnico_id,
            is_tecnico_campo=True,
            aloca_em_umc=True,
        )
        resultado = validar_jornada_umc(
            tecnico=tecnico_jornada,
            regime=regime_resolvido.regime,
            janela=inp.janela,
            eventos_existentes=[_para_evento_simples(ev) for ev in eventos_dia],
            acordo_coletivo_12h=inp.acordo_coletivo_12h,
        )
        if not resultado.ok and resultado.violacao is not None:
            violacoes.append(
                {
                    "dimensao": "jornada_umc",
                    "codigo": "JORNADA_UMC_VIOLADA",
                    "detalhe": resultado.violacao,
                    "faltante_min": resultado.faltante_min,
                    "proximo_slot": (
                        resultado.proximo_slot.isoformat() if resultado.proximo_slot else None
                    ),
                }
            )

        # 3. CNH (apenas motorista + aloca_em_umc)
        if regime_resolvido.regime == RegimeJornada.MOTORISTA_PROFISSIONAL:
            pendencia = colaborador_port.pendencia_cnh(
                tenant_id=inp.tenant_id,
                colaborador_id=inp.tecnico_id,
            )
            if pendencia:
                violacoes.append(
                    {
                        "dimensao": "cnh",
                        "codigo": "MOTORISTA_SEM_CNH",
                        "detalhe": "Técnico com pendência de CNH (INV-AG-CNH-001).",
                    }
                )

    return ValidarEventoOutput(ok=len(violacoes) == 0, violacoes=violacoes)
