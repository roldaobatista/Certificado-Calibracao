"""Use case `reagendar_evento` — reagenda + enfileira aviso ao cliente (T-AGE-032 / US-AG-008).

Reagendar implica comunicação ao cliente (stub Wave A — GATE-AGE-OMNICHANNEL).
Revalida tudo (overlap + jornada + feriado + CNH) no novo slot.
Publica ``agenda.evento.reagendado`` (via view no mesmo atomic).
"""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from django.db import IntegrityError

from src.domain.operacao.agenda.entities import EventoAgenda, EventoAuditoriaAgenda
from src.domain.operacao.agenda.enums import AcaoAuditoria, EstadoEvento, RegimeJornada
from src.domain.operacao.agenda.erros import (
    ConflitoAgenda,
    EventoNaoEncontrado,
    FeriadoNaoConfirmado,
    JornadaUMCViolada,
    MotoristaSemCNH,
    TransicaoEventoProibida,
)
from src.domain.operacao.agenda.jornada import EventoSimples, validar_jornada_umc
from src.domain.operacao.agenda.portas import (
    ColaboradorAgendaPort,
    EventoAgendaRepository,
    NotificacaoClientePort,
)
from src.domain.operacao.agenda.value_objects import Janela, TecnicoJornada


def _para_evento_simples(ev: EventoAgenda) -> EventoSimples:
    """Converte EventoAgenda → EventoSimples para validação de jornada."""
    return EventoSimples(
        tipo=ev.tipo,
        janela=Janela(inicia_at=ev.inicia_at, termina_at=ev.termina_at),
    )

logger = logging.getLogger(__name__)

_ESTADOS_TERMINAIS = {EstadoEvento.CONCLUIDO, EstadoEvento.CANCELADO, EstadoEvento.NO_SHOW}


@dataclass(frozen=True, slots=True)
class ReagendarEventoInput:
    tenant_id: UUID
    evento_id: UUID
    nova_janela: Janela
    reagendado_por_usuario_id: UUID
    perfil_tenant: str  # server-side
    confirmar_feriado: bool = False
    acordo_coletivo_12h: bool = False
    motivo_reagendamento: str = ""
    # Opcional: ID do cliente para enfileirar aviso (stub Wave A)
    cliente_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ReagendarEventoOutput:
    evento: EventoAgenda
    aviso_enfileirado: bool


def executar(
    inp: ReagendarEventoInput,
    *,
    repo: EventoAgendaRepository,
    colaborador_port: ColaboradorAgendaPort,
    notificacao_port: NotificacaoClientePort,
) -> ReagendarEventoOutput:
    """Reagenda evento + enfileira aviso ao cliente (stub Wave A)."""
    agora = datetime.now(UTC)

    evento = repo.obter_por_id(tenant_id=inp.tenant_id, evento_id=inp.evento_id)
    if evento is None:
        raise EventoNaoEncontrado(f"Evento {inp.evento_id} não encontrado.")

    if evento.termina_at <= agora:
        raise TransicaoEventoProibida(
            f"Evento {inp.evento_id} já passou — não pode ser reagendado (D-AGE-3)."
        )
    if evento.estado in _ESTADOS_TERMINAIS:
        raise TransicaoEventoProibida(
            f"Evento {inp.evento_id} em estado terminal {evento.estado.value!r}."
        )

    data_novo_slot: date = inp.nova_janela.inicia_at.date()

    # Regime server-side
    regime_resolvido = colaborador_port.regime_jornada(
        tenant_id=inp.tenant_id,
        colaborador_id=evento.tecnico_id,
        na_data=data_novo_slot,
    )

    # CNH
    if evento.aloca_em_umc and regime_resolvido.regime == RegimeJornada.MOTORISTA_PROFISSIONAL:
        pendencia = colaborador_port.pendencia_cnh(
            tenant_id=inp.tenant_id,
            colaborador_id=evento.tecnico_id,
        )
        if pendencia:
            raise MotoristaSemCNH(
                f"Técnico {evento.tecnico_id} com pendência de CNH."
            )

    # Feriado
    if not inp.confirmar_feriado:
        feriados = repo.listar_feriados(
            tenant_id=inp.tenant_id,
            data_inicio=data_novo_slot,
            data_fim=data_novo_slot,
        )
        if feriados:
            descricoes = ", ".join(f.descricao for f in feriados)
            raise FeriadoNaoConfirmado(
                f"Data {data_novo_slot} é feriado ({descricoes}). "
                "Envie `confirmar_feriado=true` para reagendar mesmo assim."
            )

    # Jornada (excluindo o próprio evento)
    if evento.aloca_em_umc:
        eventos_dia = [
            ev
            for ev in repo.listar_por_tecnico_no_dia(
                tenant_id=inp.tenant_id,
                tecnico_id=evento.tecnico_id,
                data=data_novo_slot,
            )
            if ev.id != inp.evento_id
        ]
        tecnico_jornada = TecnicoJornada(
            tenant_id=inp.tenant_id,
            colaborador_id=evento.tecnico_id,
            is_tecnico_campo=True,
            aloca_em_umc=True,
        )
        resultado = validar_jornada_umc(
            tecnico=tecnico_jornada,
            regime=regime_resolvido.regime,
            janela=inp.nova_janela,
            eventos_existentes=[_para_evento_simples(ev) for ev in eventos_dia],
            acordo_coletivo_12h=inp.acordo_coletivo_12h,
        )
        if not resultado.ok and resultado.violacao is not None:
            raise JornadaUMCViolada(
                f"Jornada UMC violada na nova janela: {resultado.violacao}."
            )

    # Atualiza
    evento_atualizado = dataclasses.replace(
        evento,
        inicia_at=inp.nova_janela.inicia_at,
        termina_at=inp.nova_janela.termina_at,
        atualizado_em=agora,
    )
    try:
        repo.atualizar(tenant_id=inp.tenant_id, evento=evento_atualizado)
    except IntegrityError as exc:
        raise ConflitoAgenda(
            f"Conflito no novo slot {inp.nova_janela.inicia_at}-{inp.nova_janela.termina_at}."
        ) from exc

    # Auditoria WORM
    payload_resumo = json.dumps(
        {
            "inicia_at_anterior": evento.inicia_at.isoformat(),
            "termina_at_anterior": evento.termina_at.isoformat(),
            "inicia_at_nova": inp.nova_janela.inicia_at.isoformat(),
            "termina_at_nova": inp.nova_janela.termina_at.isoformat(),
            "motivo": inp.motivo_reagendamento,
            "perfil_tenant": inp.perfil_tenant,
        },
        ensure_ascii=False,
    )
    auditoria = EventoAuditoriaAgenda(
        id=uuid4(),
        evento_id=inp.evento_id,
        tenant_id=inp.tenant_id,
        acao=AcaoAuditoria.REAGENDADO,
        actor_usuario_id=inp.reagendado_por_usuario_id,
        occurred_at=agora,
        criado_em=agora,
        payload_resumo=payload_resumo,
    )
    repo.salvar_auditoria(auditoria)

    # Enfileira aviso ao cliente (stub Wave A — GATE-AGE-OMNICHANNEL)
    aviso_enfileirado = False
    if inp.cliente_id is not None:
        try:
            notificacao_port.enfileirar_aviso_reagendamento(
                tenant_id=inp.tenant_id,
                evento_id=inp.evento_id,
                cliente_id=inp.cliente_id,
                nova_janela_inicia=inp.nova_janela.inicia_at,
                nova_janela_termina=inp.nova_janela.termina_at,
            )
            aviso_enfileirado = True
        except Exception:
            logger.warning(
                "reagendar_evento: falha ao enfileirar aviso (stub OK — GATE-AGE-OMNICHANNEL)",
                exc_info=True,
                extra={"evento_id": str(inp.evento_id), "tenant_id": str(inp.tenant_id)},
            )

    return ReagendarEventoOutput(evento=evento_atualizado, aviso_enfileirado=aviso_enfileirado)
