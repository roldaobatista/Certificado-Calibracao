"""Mapper model PG ↔ entidade de domínio agenda (Fatia 1b, T-AGE-021 — ADR-0007).

Colunas tipadas → mapeamento campo-a-campo. O use case nunca conhece Django — só
as entidades de domínio. Enums reconstruídos a partir do ``.value``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.operacao.agenda.entities import (
    CapacidadeTecnico,
    EventoAgenda,
    EventoAuditoriaAgenda,
    Feriado,
    RegimeJornadaColaborador,
    RegistroNoShow,
)
from src.domain.operacao.agenda.entities import (
    Recorrencia as RecorrenciaDominio,
)
from src.domain.operacao.agenda.enums import (
    AcaoAuditoria,
    EstadoEvento,
    FonteRegime,
    MotivoBloqueio,
    RegimeJornada,
    TipoEvento,
)

if TYPE_CHECKING:
    from src.infrastructure.agenda.models import CapacidadeTecnico as CapacidadeTecnicoModel
    from src.infrastructure.agenda.models import EventoAgenda as EventoAgendaModel
    from src.infrastructure.agenda.models import (
        EventoAuditoriaAgenda as EventoAuditoriaAgendaModel,
    )
    from src.infrastructure.agenda.models import Feriado as FeriadoModel
    from src.infrastructure.agenda.models import RecorrenciaAgenda as RecorrenciaAgendaModel
    from src.infrastructure.agenda.models import (
        RegimeJornadaColaborador as RegimeJornadaColaboradorModel,
    )
    from src.infrastructure.agenda.models import RegistroNoShow as RegistroNoShowModel


def model_para_evento(m: EventoAgendaModel) -> EventoAgenda:
    """Model PG → entidade de domínio ``EventoAgenda`` (leitura)."""
    return EventoAgenda(
        id=m.id,
        tenant_id=m.tenant_id,
        tecnico_id=m.tecnico_id,
        tipo=TipoEvento(m.tipo),
        estado=EstadoEvento(m.estado),
        inicia_at=m.inicia_at,
        termina_at=m.termina_at,
        aloca_em_umc=m.aloca_em_umc,
        criado_por_usuario_id=m.criado_por_usuario_id,
        criado_em=m.criado_em,
        atualizado_em=m.atualizado_em,
        revision=m.revision,
        atividade_id=m.atividade_id,
        os_id=m.os_id,
        motivo_bloqueio=MotivoBloqueio(m.motivo_bloqueio) if m.motivo_bloqueio else None,
        descricao_publica=m.descricao_publica or "",
        recorrencia_id=m.recorrencia_id,
        ocorrencia_dt=m.ocorrencia_dt,
        confirmar_feriado=m.confirmar_feriado,
    )


def evento_para_campos(e: EventoAgenda) -> dict[str, Any]:
    """Entidade ``EventoAgenda`` → kwargs do Model (escrita). ``id``/``tenant_id`` por fora."""
    return {
        "tecnico_id": e.tecnico_id,
        "tipo": e.tipo.value,
        "estado": e.estado.value,
        "inicia_at": e.inicia_at,
        "termina_at": e.termina_at,
        "aloca_em_umc": e.aloca_em_umc,
        "criado_por_usuario_id": e.criado_por_usuario_id,
        "atividade_id": e.atividade_id,
        "os_id": e.os_id,
        "motivo_bloqueio": e.motivo_bloqueio.value if e.motivo_bloqueio else "",
        "descricao_publica": e.descricao_publica,
        "recorrencia_id": e.recorrencia_id,
        "ocorrencia_dt": e.ocorrencia_dt,
        "confirmar_feriado": e.confirmar_feriado,
    }


def model_para_auditoria(m: EventoAuditoriaAgendaModel) -> EventoAuditoriaAgenda:
    """Model PG → entidade ``EventoAuditoriaAgenda`` (leitura)."""
    return EventoAuditoriaAgenda(
        id=m.id,
        tenant_id=m.tenant_id,
        evento_id=m.evento_id,
        acao=AcaoAuditoria(m.acao),
        actor_usuario_id=m.actor_usuario_id,
        occurred_at=m.occurred_at,
        criado_em=m.criado_em,
        payload_resumo=m.payload_resumo or "",
    )


def model_para_no_show(m: RegistroNoShowModel) -> RegistroNoShow:
    """Model PG → entidade ``RegistroNoShow`` (leitura)."""
    return RegistroNoShow(
        id=m.id,
        tenant_id=m.tenant_id,
        evento_id=m.evento_id,
        tecnico_id=m.tecnico_id,
        ocorrido_em=m.ocorrido_em,
        custo_estimado=m.custo_estimado,
        cobrar_cliente=m.cobrar_cliente,
        registrado_por_usuario_id=m.registrado_por_usuario_id,
        criado_em=m.criado_em,
        observacao=m.observacao or "",
    )


def model_para_feriado(m: FeriadoModel) -> Feriado:
    """Model PG → entidade ``Feriado`` (leitura)."""
    return Feriado(
        id=m.id,
        data=m.data,
        descricao=m.descricao,
        nacional=m.nacional,
        tenant_id=m.tenant_id,
        criado_em=m.criado_em,
        ativo=m.ativo,
    )


def model_para_capacidade(m: CapacidadeTecnicoModel) -> CapacidadeTecnico:
    """Model PG → entidade ``CapacidadeTecnico`` (leitura)."""
    # Decodifica bitmask → frozenset[int]
    bitmask = m.dias_trabalho
    dias = frozenset(i for i in range(7) if bitmask & (1 << i))
    return CapacidadeTecnico(
        id=m.id,
        tenant_id=m.tenant_id,
        colaborador_id=m.colaborador_id,
        horas_uteis_dia=m.horas_uteis_dia,
        dias_trabalho=dias,
        hora_inicio=m.hora_inicio,
        hora_fim=m.hora_fim,
        vigencia_inicio=m.vigencia_inicio,
        criado_por_usuario_id=m.criado_por_usuario_id,
        criado_em=m.criado_em,
        atualizado_em=m.atualizado_em,
        vigencia_fim=m.vigencia_fim,
    )


def model_para_regime(m: RegimeJornadaColaboradorModel) -> RegimeJornadaColaborador:
    """Model PG → entidade ``RegimeJornadaColaborador`` (leitura)."""
    return RegimeJornadaColaborador(
        id=m.id,
        tenant_id=m.tenant_id,
        colaborador_id=m.colaborador_id,
        regime=RegimeJornada(m.regime),
        vigencia_inicio=m.vigencia_inicio,
        definido_por_usuario_id=m.definido_por_usuario_id,
        fonte=FonteRegime(m.fonte),
        criado_em=m.criado_em,
        vigencia_fim=m.vigencia_fim,
        justificativa=m.justificativa or "",
    )


def model_para_recorrencia(m: RecorrenciaAgendaModel) -> RecorrenciaDominio:
    """Model PG → entidade ``Recorrencia`` (leitura)."""
    return RecorrenciaDominio(
        id=m.id,
        tenant_id=m.tenant_id,
        tecnico_id=m.tecnico_id,
        rrule_str=m.rrule_str,
        inicia_em=m.inicia_em,
        duracao_minutos=m.duracao_minutos,
        ativo=m.ativo,
        tipo=TipoEvento(m.tipo),
        criado_por_usuario_id=m.criado_por_usuario_id,
        criado_em=m.criado_em,
        atualizado_em=m.atualizado_em,
        atividade_id=m.atividade_id,
        os_id=m.os_id,
        aloca_em_umc=m.aloca_em_umc,
    )
