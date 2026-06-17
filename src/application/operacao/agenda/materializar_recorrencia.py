"""Use case `materializar_recorrencia` — job/command de materialização 90d (T-AGE-035 / D-AGE-8 / R10).

Idempotente por ``(recorrencia_id, ocorrencia_dt)`` via UNIQUE no banco.
IntegrityError por duplicata = skip (não é erro). Re-rodar o job é seguro.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from django.db import IntegrityError

from src.domain.operacao.agenda.entities import EventoAgenda, EventoAuditoriaAgenda
from src.domain.operacao.agenda.enums import AcaoAuditoria, EstadoEvento, TipoEvento
from src.domain.operacao.agenda.portas import EventoAgendaRepository
from src.domain.operacao.agenda.recorrencia import materializar_janela
from src.domain.operacao.agenda.value_objects import RegraRecorrencia

logger = logging.getLogger(__name__)

_HORIZONTE_DIAS = 90


@dataclass(frozen=True, slots=True)
class MaterializarRecorrenciaInput:
    tenant_id: UUID
    recorrencia_id: UUID
    rrule_str: str
    duracao_minutos: int
    tipo_evento: TipoEvento
    tecnico_id: UUID
    aloca_em_umc: bool
    criado_por_usuario_id: UUID
    perfil_tenant: str  # server-side
    atividade_id: UUID | None = None
    os_id: UUID | None = None
    descricao_publica: str = ""
    a_partir_de: datetime | None = None  # default = agora (injetável — débito Fatia 1a)


@dataclass(frozen=True, slots=True)
class MaterializarRecorrenciaOutput:
    criados: int
    skipped: int  # duplicatas (idempotência)


def executar(
    inp: MaterializarRecorrenciaInput,
    *,
    repo: EventoAgendaRepository,
) -> MaterializarRecorrenciaOutput:
    """Materializa janela 90d. Duplicatas são ignoradas (R10 / ADR-0033)."""
    agora = inp.a_partir_de or datetime.now(UTC)

    regra = RegraRecorrencia(
        rrule_str=inp.rrule_str,
        descricao_publica=inp.descricao_publica or inp.rrule_str,
    )
    ocorrencias = materializar_janela(
        regra=regra,
        inicio=agora,
        dias=_HORIZONTE_DIAS,
    )

    criados = 0
    skipped = 0

    for ocorrencia_dt in ocorrencias:
        termina_at = ocorrencia_dt + timedelta(minutes=inp.duracao_minutos)

        evento = EventoAgenda(
            id=uuid4(),
            tenant_id=inp.tenant_id,
            tecnico_id=inp.tecnico_id,
            tipo=inp.tipo_evento,
            estado=EstadoEvento.AGENDADO,
            inicia_at=ocorrencia_dt,
            termina_at=termina_at,
            aloca_em_umc=inp.aloca_em_umc,
            criado_por_usuario_id=inp.criado_por_usuario_id,
            criado_em=agora,
            atualizado_em=agora,
            revision=0,
            atividade_id=inp.atividade_id,
            os_id=inp.os_id,
            recorrencia_id=inp.recorrencia_id,
            ocorrencia_dt=ocorrencia_dt,
            descricao_publica=inp.descricao_publica,
        )

        try:
            repo.salvar_novo(evento)
        except IntegrityError:
            # UNIQUE (recorrencia_id, ocorrencia_dt) — duplicata OK (idempotente)
            skipped += 1
            continue

        payload_resumo = json.dumps(
            {
                "recorrencia_id": str(inp.recorrencia_id),
                "ocorrencia_dt": ocorrencia_dt.isoformat(),
                "perfil_tenant": inp.perfil_tenant,
            },
            ensure_ascii=False,
        )
        auditoria = EventoAuditoriaAgenda(
            id=uuid4(),
            evento_id=evento.id,
            tenant_id=inp.tenant_id,
            acao=AcaoAuditoria.CRIADO,
            actor_usuario_id=inp.criado_por_usuario_id,
            occurred_at=agora,
            criado_em=agora,
            payload_resumo=payload_resumo,
        )
        repo.salvar_auditoria(auditoria)
        criados += 1

    logger.info(
        "materializar_recorrencia: recorrencia=%s criados=%d skipped=%d",
        inp.recorrencia_id,
        criados,
        skipped,
        extra={"tenant_id": str(inp.tenant_id)},
    )

    return MaterializarRecorrenciaOutput(criados=criados, skipped=skipped)
