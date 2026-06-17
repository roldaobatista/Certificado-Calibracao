"""Consumers de eventos de OS para a frente agenda (Fatia 3b — T-AGE-044).

Eventos consumidos:
  os.aberta           → agenda não faz nada (registro futuro para pro-ativo)
  os.cancelada        → cancela eventos de agenda vinculados à OS
  os.reaberta         → log (OS volta a RASCUNHO; slots permanecem)
  os.atividade_concluida → libera slot (evento vai para CONCLUIDO)
  os.atividade_cancelada → libera slot (evento vai para CANCELADO)

Regras críticas (plan §5 / R7 / R8):
  - Perfil lido do envelope (``envelope["perfil_no_evento"]``),
    NUNCA de ``obter_perfil_tenant_corrente()`` (R7 / RBC-CR-03).
  - ``perfil_no_evento IS NULL`` → fail-closed (log + return).
  - Fan-out aditivo: não engole consumers existentes de OS (R8).
  - Cada consumer usa ``@consumer_idempotente`` (ADR-0033 / INV-BUS-001).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _extrair_ids(
    envelope: dict[str, Any],
) -> tuple[UUID | None, str | None]:
    """Extrai (tenant_id, perfil_no_evento) do envelope com validação fail-safe."""
    raw_tenant = envelope.get("tenant_id")
    perfil = envelope.get("perfil_no_evento")
    tenant_id: UUID | None = None
    if raw_tenant:
        try:
            tenant_id = UUID(str(raw_tenant))
        except (ValueError, TypeError):
            logger.warning("agenda consumer: tenant_id inválido no envelope: %r", raw_tenant)
    return tenant_id, str(perfil) if perfil else None


def _cancelar_eventos_por_os(*, tenant_id: UUID, os_id: UUID) -> int:
    """Cancela todos os eventos de agenda vinculados à OS (helper compartilhado)."""
    from django.utils import timezone

    from src.domain.operacao.agenda.enums import EstadoEvento
    from src.infrastructure.agenda.models import EventoAgenda

    agendado = EstadoEvento.AGENDADO.value
    cancelado = EstadoEvento.CANCELADO.value

    atualizados = EventoAgenda.objects.filter(
        tenant_id=tenant_id,
        os_id=os_id,
        estado=agendado,
    ).update(
        estado=cancelado,
        atualizado_em=timezone.now(),
    )
    if atualizados:
        logger.info(
            "agenda consumer: %d evento(s) cancelado(s) para os_id=%s tenant=%s",
            atualizados,
            os_id,
            tenant_id,
        )
    return atualizados


@consumer_idempotente(consumer_id="agenda.consumer.os_aberta")
def handle_os_aberta(envelope: dict[str, Any]) -> None:
    """Consumer de os.aberta — agenda registra (sem ação imediata Wave A).

    Wave B: pode criar slot-reserva pro-ativo ao abrir OS.
    """
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        logger.warning("agenda.consumer.os_aberta: tenant_id ausente — no-op")
        return
    if not perfil:
        logger.warning("agenda.consumer.os_aberta: perfil_no_evento ausente (fail-closed) — no-op")
        return
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    logger.debug(
        "agenda.consumer.os_aberta: os_id=%s tenant=%s perfil=%s (no-op Wave A)",
        os_id_raw,
        tenant_id,
        perfil,
    )


@consumer_idempotente(consumer_id="agenda.consumer.os_cancelada")
def handle_os_cancelada(envelope: dict[str, Any]) -> None:
    """Consumer de os.cancelada — cancela slots agendados vinculados à OS."""
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        logger.warning("agenda.consumer.os_cancelada: tenant_id ausente — no-op")
        return
    if not perfil:
        logger.warning(
            "agenda.consumer.os_cancelada: perfil_no_evento ausente (fail-closed) — no-op"
        )
        return
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    if not os_id_raw:
        logger.warning("agenda.consumer.os_cancelada: os_id ausente no payload — no-op")
        return
    try:
        os_id = UUID(str(os_id_raw))
    except (ValueError, TypeError):
        logger.warning("agenda.consumer.os_cancelada: os_id inválido: %r", os_id_raw)
        return
    _cancelar_eventos_por_os(tenant_id=tenant_id, os_id=os_id)


@consumer_idempotente(consumer_id="agenda.consumer.os_reaberta")
def handle_os_reaberta(envelope: dict[str, Any]) -> None:
    """Consumer de os.reaberta — slots existentes permanecem; log apenas."""
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        return
    payload = envelope.get("payload", {})
    logger.info(
        "agenda.consumer.os_reaberta: os_id=%s tenant=%s — slots de agenda mantidos",
        payload.get("os_id"),
        tenant_id,
    )


@consumer_idempotente(consumer_id="agenda.consumer.os_atividade_concluida")
def handle_os_atividade_concluida(envelope: dict[str, Any]) -> None:
    """Consumer de os.atividade_concluida — transita slot para CONCLUIDO."""
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        return
    if not perfil:
        logger.warning(
            "agenda.consumer.os_atividade_concluida: perfil ausente (fail-closed) — no-op"
        )
        return
    payload = envelope.get("payload", {})
    atividade_id_raw = payload.get("atividade_id")
    if not atividade_id_raw:
        return
    try:
        atividade_id = UUID(str(atividade_id_raw))
    except (ValueError, TypeError):
        logger.warning(
            "agenda.consumer.os_atividade_concluida: atividade_id inválido: %r",
            atividade_id_raw,
        )
        return

    from django.utils import timezone

    from src.domain.operacao.agenda.enums import EstadoEvento
    from src.infrastructure.agenda.models import EventoAgenda

    atualizados = EventoAgenda.objects.filter(
        tenant_id=tenant_id,
        atividade_id=atividade_id,
        estado=EstadoEvento.AGENDADO.value,
    ).update(
        estado=EstadoEvento.CONCLUIDO.value,
        atualizado_em=timezone.now(),
    )
    logger.info(
        "agenda.consumer.os_atividade_concluida: %d evento(s) concluído(s) "
        "atividade=%s tenant=%s",
        atualizados,
        atividade_id,
        tenant_id,
    )


@consumer_idempotente(consumer_id="agenda.consumer.os_atividade_cancelada")
def handle_os_atividade_cancelada(envelope: dict[str, Any]) -> None:
    """Consumer de os.atividade_cancelada — cancela slot vinculado à atividade."""
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        return
    if not perfil:
        logger.warning(
            "agenda.consumer.os_atividade_cancelada: perfil ausente (fail-closed) — no-op"
        )
        return
    payload = envelope.get("payload", {})
    atividade_id_raw = payload.get("atividade_id")
    if not atividade_id_raw:
        return
    try:
        atividade_id = UUID(str(atividade_id_raw))
    except (ValueError, TypeError):
        return

    from django.utils import timezone

    from src.domain.operacao.agenda.enums import EstadoEvento
    from src.infrastructure.agenda.models import EventoAgenda

    atualizados = EventoAgenda.objects.filter(
        tenant_id=tenant_id,
        atividade_id=atividade_id,
        estado=EstadoEvento.AGENDADO.value,
    ).update(
        estado=EstadoEvento.CANCELADO.value,
        atualizado_em=timezone.now(),
    )
    logger.info(
        "agenda.consumer.os_atividade_cancelada: %d evento(s) cancelado(s) "
        "atividade=%s tenant=%s",
        atualizados,
        atividade_id,
        tenant_id,
    )
