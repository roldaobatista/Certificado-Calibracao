"""Consumer `os.aberta` → fecha a saga orçamento→OS (T-ORC-035 / D-ORC-14).

Quando a OS publica ``os.aberta`` (ao abrir, via ``abrir_os_via_orcamento`` que
cruza ``OS.Aberta`` pro bus — INT-01), este consumer casa o ``orcamento_id`` do
payload e transiciona ``aprovado_pendente_os → convertido``, publicando
``orcamento.convertido`` (consumido por CRM/dashboard).

TL-ORC ALTO-1: a OS AVULSA (sem orçamento de origem) também publica ``os.aberta``,
porém sem ``orcamento_id`` no payload → este consumer faz **no-op** nesse caso.

Idempotência em 2 camadas:
  - ``@consumer_idempotente`` (event_id) — replay do mesmo evento é no-op.
  - ``converter_orcamento`` — estado != ``aprovado_pendente_os`` é no-op (ex.: já
    ``convertido`` por um 2º ``os.aberta``, ou orçamento de outro fluxo).

O ``os_id`` (UUID) NÃO vem no envelope de ``os.aberta`` (o ``causation_id`` é o id
do snapshot do evento, não da OS; o payload traz só ``numero_os``). Publicamos
``orcamento.convertido`` com ``numero_os`` — GATE-ORC-CONVERTIDO-OSID quando a OS
incluir ``os_id`` no payload de ``os.aberta`` (aditivo).

O worker entra em ``run_in_tenant_context`` antes de invocar; o decorator abre
``transaction.atomic`` — handler não abre nenhum dos dois (molde
``ordens_servico/consumers/cliente.py``).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.application.comercial.orcamentos.ciclo_vida import (
    ConverterOrcamentoInput,
    converter_orcamento,
)
from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "orcamento.consumer.os_aberta"


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_os_aberta(envelope: dict[str, Any]) -> None:
    """Casa `orcamento_id` de `os.aberta` e fecha a saga (aprovado_pendente_os→convertido)."""
    payload = envelope.get("payload", {})
    orcamento_id_raw = payload.get("orcamento_id")
    # OS avulsa publica os.aberta SEM orcamento_id -> no-op (TL-ORC ALTO-1).
    if not orcamento_id_raw or str(orcamento_id_raw).lower() == "none":
        return
    try:
        orcamento_id = UUID(str(orcamento_id_raw))
    except (ValueError, TypeError):
        logger.warning(
            "orcamento.consumer.os_aberta: orcamento_id invalido %r correlation_id=%s",
            orcamento_id_raw,
            envelope.get("correlation_id"),
        )
        return

    tenant_raw = envelope.get("tenant_id")
    if not tenant_raw:
        logger.warning(
            "orcamento.consumer.os_aberta: envelope sem tenant_id correlation_id=%s",
            envelope.get("correlation_id"),
        )
        return
    try:
        tenant_id = UUID(str(tenant_raw))
    except (ValueError, TypeError):
        logger.warning(
            "orcamento.consumer.os_aberta: tenant_id invalido %r correlation_id=%s",
            tenant_raw,
            envelope.get("correlation_id"),
        )
        return

    from src.infrastructure.orcamentos.repositories import DjangoOrcamentoRepository

    out = converter_orcamento(
        ConverterOrcamentoInput(
            tenant_id=tenant_id,
            orcamento_id=orcamento_id,
            agora=datetime.now(UTC),
        ),
        repo=DjangoOrcamentoRepository(),
    )
    # Inexistente no tenant / já convertido / estado inesperado -> no-op.
    if out is None or not out.convertido:
        logger.debug(
            "orcamento.consumer.os_aberta: no-op orcamento=%s (sem conversao)", orcamento_id
        )
        return

    # Saga fechada (D-ORC-14): publica orcamento.convertido (outbox; mesma tx do decorator).
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao="orcamento.convertido",
        payload={
            "orcamento_id": str(orcamento_id),
            "tenant_id": str(tenant_id),
            "numero_os": payload.get("numero_os"),
        },
        causation_id=orcamento_id,
        tenant_id=tenant_id,
        resource_summary=f"orcamento:{orcamento_id}",
        outbox=True,
    )
    logger.info(
        "orcamento.consumer.os_aberta: orcamento=%s convertido (numero_os=%s)",
        orcamento_id,
        payload.get("numero_os"),
    )
