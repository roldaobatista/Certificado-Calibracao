"""Consumer de `contas_receber.pago` → desbloqueio de cliente (Fatia 3c — T-CR-045 / D-CR-11).

CR publica `contas_receber.pago` ao baixar título (manual/webhook). Este consumer —
dono do `ClienteBloqueio` — encerra o bloqueio AUTOMÁTICO por inadimplência quando a
quitação zerou a dívida vencida do cliente, e publica `cliente.desbloqueado`
(INV-FIN-REATIV-001 / GATE-CLI-6). É CR quem publica o fato; é `clientes` quem decide
desbloquear (separação de donos — TL-CR-05 / R5).

Régua (D-CR-11):
  - cliente resolvido via CR (`cliente_atual_id_do_titulo`); anonimizado/inexistente → no-op.
  - ainda há título vencido em aberto (`tem_outra_vencida_em_aberto`) → mantém bloqueio
    (AC-CR-006-2: pagamento parcial com outra vencida NÃO desbloqueia).
  - SÓ encerra bloqueio `automatico_inadimplencia_90d`; bloqueio MANUAL (quebra de
    confiança / jurídico / outro) NÃO é desfeito por pagamento.
  - idempotente: replay do bus (`@consumer_idempotente`) + ausência de bloqueio ativo (no-op).

Roda DENTRO de `run_in_tenant_context` (worker) + `transaction.atomic` (decorator) —
não abre contexto de tenant. NÃO importa DRF nem SDK de gateway. Importa a query
read-only de CR localmente (clientes.infra → contas_receber.infra; sem ciclo — o
domínio de `clientes` não conhece CR).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID_CR_PAGO = "clientes.consumer.contas_receber_pago"
MOTIVO_DESBLOQUEIO_QUITACAO = "pagamento_quitou_inadimplencia"


def _titulo_e_tenant(envelope: dict[str, Any]) -> tuple[UUID, UUID] | None:
    """Extrai `titulo_id` (payload) + `tenant_id` (envelope). `None` → no-op."""
    payload = envelope.get("payload", {})
    titulo_raw = payload.get("titulo_id")
    tenant_raw = envelope.get("tenant_id")
    if not titulo_raw or not tenant_raw:
        logger.warning(
            "handle_contas_receber_pago: envelope sem titulo_id/tenant_id — no-op"
        )
        return None
    try:
        return UUID(str(titulo_raw)), UUID(str(tenant_raw))
    except (ValueError, TypeError):
        logger.warning("handle_contas_receber_pago: titulo_id/tenant_id inválido — no-op")
        return None


@consumer_idempotente(consumer_id=CONSUMER_ID_CR_PAGO)
def handle_contas_receber_pago(envelope: dict[str, Any]) -> None:
    """`contas_receber.pago` → encerra bloqueio automático se a quitação zerou a dívida."""
    from src.infrastructure.audit.event_helpers import publicar_evento
    from src.infrastructure.clientes.bloqueio import (
        MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
    )
    from src.infrastructure.clientes.models import ClienteBloqueio
    from src.infrastructure.contas_receber import queries_desbloqueio

    ids = _titulo_e_tenant(envelope)
    if ids is None:
        return
    titulo_id, tenant_id = ids

    cliente_id = queries_desbloqueio.cliente_atual_id_do_titulo(
        tenant_id=tenant_id, titulo_id=titulo_id
    )
    if cliente_id is None:
        # Título inexistente no tenant OU cliente anonimizado (LGPD) → sem bloqueio rastreável.
        logger.info(
            "handle_contas_receber_pago: título %s sem cliente atual — no-op", titulo_id
        )
        return

    # AC-CR-006-2: ainda há dívida vencida em aberto → mantém o bloqueio.
    if queries_desbloqueio.tem_outra_vencida_em_aberto(
        tenant_id=tenant_id, cliente_id=cliente_id
    ):
        logger.info(
            "handle_contas_receber_pago: cliente %s ainda tem vencida em aberto — "
            "mantém bloqueio (AC-CR-006-2)",
            cliente_id,
        )
        return

    # SÓ desbloqueia bloqueio AUTOMÁTICO por inadimplência (D-CR-11 — "bloqueado por
    # inadimplência"). Bloqueio MANUAL (quebra de confiança/jurídico) não cede a pagamento.
    ativo = (
        ClienteBloqueio.objects.filter(
            tenant_id=tenant_id,
            cliente_id=cliente_id,
            desbloqueado_em__isnull=True,
            motivo_categoria=MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
        )
        .select_for_update()
        .first()
    )
    if ativo is None:
        # Nunca bloqueado, já desbloqueado, ou só bloqueio manual ativo → idempotente no-op.
        logger.info(
            "handle_contas_receber_pago: cliente %s sem bloqueio automático ativo — no-op",
            cliente_id,
        )
        return

    ativo.desbloqueado_em = datetime.now(UTC)
    ativo.desbloqueado_por_usuario_id = None  # desbloqueio sistêmico (não há usuário)
    ativo.desbloqueado_motivo = MOTIVO_DESBLOQUEIO_QUITACAO
    ativo.save(
        update_fields=[
            "desbloqueado_em",
            "desbloqueado_por_usuario_id",
            "desbloqueado_motivo",
        ]
    )

    causation_id = UUID(str(envelope["event_id"]))
    publicar_evento(
        acao="cliente.desbloqueado",
        payload={
            "event_id": str(uuid4()),
            "cliente_id": str(cliente_id),
            "tenant_id": str(tenant_id),
            "bloqueio_id": str(ativo.id),
            "motivo": MOTIVO_DESBLOQUEIO_QUITACAO,
            "titulo_id_quitado": str(titulo_id),
            "automatico": True,
        },
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=None,
        resource_summary=str(cliente_id),
    )
    logger.info(
        "handle_contas_receber_pago: cliente %s desbloqueado (quitação título %s)",
        cliente_id,
        titulo_id,
    )
