"""Use case `criar_bloqueio` — EventoAgenda(tipo=bloqueio) (T-AGE-031 / US-AG-004).

Cria bloqueio de agenda (férias, treinamento, atestado, outro).
Não valida jornada UMC (bloqueios são justamente ausências legítimas).
Publica ``agenda.bloqueio.criado`` (via view no mesmo atomic).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from django.db import IntegrityError

from src.domain.operacao.agenda.entities import EventoAgenda, EventoAuditoriaAgenda
from src.domain.operacao.agenda.enums import (
    AcaoAuditoria,
    EstadoEvento,
    MotivoBloqueio,
    TipoEvento,
)
from src.domain.operacao.agenda.erros import ConflitoAgenda
from src.domain.operacao.agenda.portas import EventoAgendaRepository
from src.domain.operacao.agenda.value_objects import Janela


@dataclass(frozen=True, slots=True)
class CriarBloqueioInput:
    """Payload de criação de bloqueio.

    ``perfil_tenant`` vem server-side (INV-AG-PERFIL-001).
    """

    tenant_id: UUID
    tecnico_id: UUID
    janela: Janela
    motivo: MotivoBloqueio
    criado_por_usuario_id: UUID
    perfil_tenant: str  # A/B/C/D — server-side
    descricao_publica: str = ""


@dataclass(frozen=True, slots=True)
class CriarBloqueioOutput:
    evento: EventoAgenda


def executar(
    inp: CriarBloqueioInput,
    *,
    repo: EventoAgendaRepository,
) -> CriarBloqueioOutput:
    """Cria bloqueio. IntegrityError do EXCLUDE GIST → ConflitoAgenda 409."""
    agora = datetime.now(UTC)

    evento = EventoAgenda(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tecnico_id=inp.tecnico_id,
        tipo=TipoEvento.BLOQUEIO,
        estado=EstadoEvento.AGENDADO,
        inicia_at=inp.janela.inicia_at,
        termina_at=inp.janela.termina_at,
        aloca_em_umc=False,
        criado_por_usuario_id=inp.criado_por_usuario_id,
        criado_em=agora,
        atualizado_em=agora,
        revision=0,
        motivo_bloqueio=inp.motivo,
        descricao_publica=inp.descricao_publica,
    )

    try:
        repo.salvar_novo(evento)
    except IntegrityError as exc:
        raise ConflitoAgenda(
            f"Conflito de agenda para técnico {inp.tecnico_id} "
            f"no slot {inp.janela.inicia_at}-{inp.janela.termina_at}."
        ) from exc

    payload_resumo = json.dumps(
        {
            "motivo": inp.motivo.value,
            "inicia_at": inp.janela.inicia_at.isoformat(),
            "termina_at": inp.janela.termina_at.isoformat(),
            "perfil_tenant": inp.perfil_tenant,
        },
        ensure_ascii=False,
    )
    auditoria = EventoAuditoriaAgenda(
        id=uuid4(),
        evento_id=evento.id,
        tenant_id=inp.tenant_id,
        acao=AcaoAuditoria.BLOQUEADO,
        actor_usuario_id=inp.criado_por_usuario_id,
        occurred_at=agora,
        criado_em=agora,
        payload_resumo=payload_resumo,
    )
    repo.salvar_auditoria(auditoria)

    return CriarBloqueioOutput(evento=evento)
