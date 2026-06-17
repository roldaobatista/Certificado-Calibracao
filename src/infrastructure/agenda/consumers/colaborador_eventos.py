"""Consumers de eventos de colaborador para a frente agenda (Fatia 3b — T-AGE-044).

Eventos consumidos:
  colaborador.desligado   → cancela toda agenda futura do técnico
  colaborador.papel_atribuido → log (regime pode mudar; sem ação imediata)
  colaborador.papel_revogado  → log (regime pode mudar; sem ação imediata)

Regras críticas (R7):
  - Perfil lido do envelope, NUNCA de obter_perfil_tenant_corrente().
  - perfil_no_evento IS NULL → fail-closed (log + return).
  - @consumer_idempotente em cada handler (ADR-0033 / INV-BUS-001).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _extrair_ids(envelope: dict[str, Any]) -> tuple[UUID | None, str | None]:
    raw_tenant = envelope.get("tenant_id")
    perfil = envelope.get("perfil_no_evento")
    tenant_id: UUID | None = None
    if raw_tenant:
        try:
            tenant_id = UUID(str(raw_tenant))
        except (ValueError, TypeError):
            pass
    return tenant_id, str(perfil) if perfil else None


@consumer_idempotente(consumer_id="agenda.consumer.colaborador_desligado")
def handle_colaborador_desligado(envelope: dict[str, Any]) -> None:
    """Consumer de colaborador.desligado — cancela toda agenda FUTURA do técnico.

    Cancela apenas eventos no estado AGENDADO com inicia_at > agora.
    Eventos em EM_EXECUCAO ou passados não são alterados.
    """
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        logger.warning("agenda.consumer.colaborador_desligado: tenant_id ausente — no-op")
        return
    if not perfil:
        logger.warning(
            "agenda.consumer.colaborador_desligado: perfil ausente (fail-closed) — no-op"
        )
        return

    payload = envelope.get("payload", {})
    colaborador_id_raw = payload.get("colaborador_id")
    if not colaborador_id_raw:
        logger.warning("agenda.consumer.colaborador_desligado: colaborador_id ausente")
        return
    try:
        colaborador_id = UUID(str(colaborador_id_raw))
    except (ValueError, TypeError):
        logger.warning(
            "agenda.consumer.colaborador_desligado: colaborador_id inválido: %r",
            colaborador_id_raw,
        )
        return

    from django.utils import timezone

    from src.domain.operacao.agenda.enums import EstadoEvento
    from src.infrastructure.agenda.models import EventoAgenda

    agora = timezone.now()
    atualizados = EventoAgenda.objects.filter(
        tenant_id=tenant_id,
        tecnico_id=colaborador_id,
        estado=EstadoEvento.AGENDADO.value,
        inicia_at__gt=agora,
    ).update(
        estado=EstadoEvento.CANCELADO.value,
        atualizado_em=agora,
    )
    logger.info(
        "agenda.consumer.colaborador_desligado: %d evento(s) futuro(s) cancelado(s) "
        "colaborador=%s tenant=%s",
        atualizados,
        colaborador_id,
        tenant_id,
    )


@consumer_idempotente(consumer_id="agenda.consumer.papel_atribuido")
def handle_papel_atribuido(envelope: dict[str, Any]) -> None:
    """Consumer de colaborador.papel_atribuido — log; regime pode mudar.

    Wave A: sem ação automática (IA não grava override — INV-AG-REGIME-001).
    Wave B: pode recalcular regime derivado se papel mudar.
    """
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        return
    payload = envelope.get("payload", {})
    logger.info(
        "agenda.consumer.papel_atribuido: colaborador=%s papel=%s tenant=%s — "
        "regime pode ter mudado; override humano necessário se aplicável (INV-AG-REGIME-001)",
        payload.get("colaborador_id"),
        payload.get("papel"),
        tenant_id,
    )


@consumer_idempotente(consumer_id="agenda.consumer.papel_revogado")
def handle_papel_revogado(envelope: dict[str, Any]) -> None:
    """Consumer de colaborador.papel_revogado — log; regime pode mudar.

    Wave A: sem ação automática (IA não grava override — INV-AG-REGIME-001).
    """
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        return
    payload = envelope.get("payload", {})
    logger.info(
        "agenda.consumer.papel_revogado: colaborador=%s papel=%s tenant=%s — "
        "regime pode ter mudado; override humano necessário se aplicável",
        payload.get("colaborador_id"),
        payload.get("papel"),
        tenant_id,
    )
