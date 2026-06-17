"""Consumers de eventos de RT para a frente agenda (Fatia 3b — T-AGE-044).

Eventos consumidos:
  tenant.rt.trocado           → revisa atribuições futuras (log + advisory Wave A)

DÉBITO DOCUMENTADO (RBC-AGE-04):
  tenant.rt.substituicao_declarada / tenant.rt.substituicao_encerrada
  NÃO EXISTEM no catálogo canônico (acoes_canonicas.py / ACOES_RT).
  Esses eventos pressupõem o modelo RTSubstituicao (ADR-0068 §2.2)
  que NÃO foi criado em Wave A.
  GATE-RTSUBSTITUICAO-FORMAL: quando RTSubstituicao existir:
  1. Adicionar os slugs a ACOES_RT em acoes_canonicas.py.
  2. Criar consumers handle_rt_substituicao_declarada /
     handle_rt_substituicao_encerrada aqui.
  3. Registrar em apps.py:ready() com try/except ValueError.
  Por ora, APENAS tenant.rt.trocado é consumido (existe no catálogo).

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


@consumer_idempotente(consumer_id="agenda.consumer.tenant_rt_trocado")
def handle_tenant_rt_trocado(envelope: dict[str, Any]) -> None:
    """Consumer de tenant.rt.trocado — revisa atribuições futuras (RBC-AGE-04).

    Quando o RT é trocado, eventos de agenda para tipo=OS que dependem de
    competência de RT precisam ser revisados.

    Wave A (advisory): loga os eventos futuros que podem ser afetados.
    Não cancela automaticamente — a agenda é CONSULTIVA (PLAN-AGE-02).
    O gate duro de NC vive na EMISSÃO (D-AGE-6 / R15).

    Wave B: implementar notificação ativa ao gestor para revisar slots
    impactados pela troca de RT.
    """
    tenant_id, perfil = _extrair_ids(envelope)
    if not tenant_id:
        logger.warning("agenda.consumer.tenant_rt_trocado: tenant_id ausente — no-op")
        return
    if not perfil:
        logger.warning("agenda.consumer.tenant_rt_trocado: perfil ausente (fail-closed) — no-op")
        return

    payload = envelope.get("payload", {})
    rt_novo_id = payload.get("rt_novo_id")
    data_efetivacao = payload.get("data_efetivacao")

    # Conta eventos futuros de tipo=os que podem ser afetados
    from django.utils import timezone

    from src.domain.operacao.agenda.enums import EstadoEvento, TipoEvento
    from src.infrastructure.agenda.models import EventoAgenda

    agora = timezone.now()
    n_afetados = EventoAgenda.objects.filter(
        tenant_id=tenant_id,
        tipo=TipoEvento.OS.value,
        estado=EstadoEvento.AGENDADO.value,
        inicia_at__gt=agora,
    ).count()

    logger.warning(
        "agenda.consumer.tenant_rt_trocado: RT novo=%s efetivacao=%s — "
        "%d evento(s) OS futuro(s) podem precisar revisão de competência RT. "
        "Agenda é CONSULTIVA (D-AGE-6 / R15); gate duro na emissão. "
        "tenant=%s perfil=%s",
        rt_novo_id,
        data_efetivacao,
        n_afetados,
        tenant_id,
        perfil,
    )
    # GATE-RTSUBSTITUICAO-FORMAL: quando RTSubstituicao existir, verificar
    # competência projetada por slot e notificar gestor para os afetados.
