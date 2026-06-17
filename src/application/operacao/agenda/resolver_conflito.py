"""Use case `resolver_conflito` — resolução manual de conflito de agenda (T-AGE-034 / US-AG-011).

Opções: ``manter_novo``, ``manter_antigo``, ``reagendar_ambos``.
Razão ≥ 30 chars validada SERVER-SIDE.
Publica ``agenda.conflito.resolvido`` (via view no mesmo atomic).
"""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.operacao.agenda.entities import EventoAgenda, EventoAuditoriaAgenda
from src.domain.operacao.agenda.enums import AcaoAuditoria, EstadoEvento
from src.domain.operacao.agenda.erros import (
    EventoNaoEncontrado,
    JustificativaConflitoCurta,
)
from src.domain.operacao.agenda.portas import EventoAgendaRepository

logger = logging.getLogger(__name__)

_RAZAO_MIN_CHARS = 30


class OpcaoConflito(str, Enum):
    MANTER_NOVO = "manter_novo"
    MANTER_ANTIGO = "manter_antigo"
    REAGENDAR_AMBOS = "reagendar_ambos"


@dataclass(frozen=True, slots=True)
class ResolverConflitoInput:
    tenant_id: UUID
    evento_novo_id: UUID
    evento_antigo_id: UUID
    opcao: OpcaoConflito
    razao: str
    resolvido_por_usuario_id: UUID
    perfil_tenant: str  # server-side


@dataclass(frozen=True, slots=True)
class ResolverConflitoOutput:
    evento_mantido: EventoAgenda
    evento_cancelado: EventoAgenda | None


def executar(
    inp: ResolverConflitoInput,
    *,
    repo: EventoAgendaRepository,
) -> ResolverConflitoOutput:
    """Resolve conflito. Razão < 30 chars → JustificativaConflitoCurta (422)."""
    if len(inp.razao.strip()) < _RAZAO_MIN_CHARS:
        raise JustificativaConflitoCurta(
            f"Razão do conflito precisa ter ≥ {_RAZAO_MIN_CHARS} caracteres "
            f"(recebeu {len(inp.razao.strip())})."
        )

    agora = datetime.now(UTC)

    evento_novo = repo.obter_por_id(tenant_id=inp.tenant_id, evento_id=inp.evento_novo_id)
    if evento_novo is None:
        raise EventoNaoEncontrado(f"Evento novo {inp.evento_novo_id} não encontrado.")

    evento_antigo = repo.obter_por_id(tenant_id=inp.tenant_id, evento_id=inp.evento_antigo_id)
    if evento_antigo is None:
        raise EventoNaoEncontrado(f"Evento antigo {inp.evento_antigo_id} não encontrado.")

    evento_mantido: EventoAgenda
    evento_cancelado: EventoAgenda | None = None

    if inp.opcao == OpcaoConflito.MANTER_NOVO:
        evento_cancelado = dataclasses.replace(
            evento_antigo, estado=EstadoEvento.CANCELADO, atualizado_em=agora
        )
        repo.atualizar(tenant_id=inp.tenant_id, evento=evento_cancelado)
        evento_mantido = evento_novo

    elif inp.opcao == OpcaoConflito.MANTER_ANTIGO:
        evento_cancelado = dataclasses.replace(
            evento_novo, estado=EstadoEvento.CANCELADO, atualizado_em=agora
        )
        repo.atualizar(tenant_id=inp.tenant_id, evento=evento_cancelado)
        evento_mantido = evento_antigo

    else:  # REAGENDAR_AMBOS
        # Cancela o antigo; novo permanece; caller deve chamar reagendar_evento depois
        evento_cancelado = dataclasses.replace(
            evento_antigo, estado=EstadoEvento.CANCELADO, atualizado_em=agora
        )
        repo.atualizar(tenant_id=inp.tenant_id, evento=evento_cancelado)
        evento_mantido = evento_novo

    # Auditoria WORM para o evento que ficou
    payload_resumo = json.dumps(
        {
            "opcao": inp.opcao.value,
            "razao": inp.razao,
            "evento_cancelado_id": str(evento_cancelado.id) if evento_cancelado else None,
            "perfil_tenant": inp.perfil_tenant,
        },
        ensure_ascii=False,
    )
    auditoria = EventoAuditoriaAgenda(
        id=uuid4(),
        evento_id=evento_mantido.id,
        tenant_id=inp.tenant_id,
        acao=AcaoAuditoria.APROVADO,
        actor_usuario_id=inp.resolvido_por_usuario_id,
        occurred_at=agora,
        criado_em=agora,
        payload_resumo=payload_resumo,
    )
    repo.salvar_auditoria(auditoria)

    return ResolverConflitoOutput(
        evento_mantido=evento_mantido,
        evento_cancelado=evento_cancelado,
    )
