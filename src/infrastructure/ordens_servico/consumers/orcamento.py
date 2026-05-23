"""T-OS-029 — Consumer `Orcamento.Aprovado`.

Quando o modulo `comercial/orcamentos` (Wave A) publica orcamento aprovado,
este consumer dispara abertura de OS via use case `abrir_os_via_orcamento`
(T-OS-041 / Fase 5).

NOTA Fase 4 (P4): use case `abrir_os_via_orcamento` ainda nao existe
(Fase 5). Por enquanto o consumer:
1. Aplica INV-BUS-001 (idempotencia).
2. Grava EventoDeOS tipo='os_aberta' (placeholder operacional).
3. Loga TODO Fase 5 + correlation_id pra rastreabilidade.

Quando Fase 5 chegar: substituir o placeholder pela invocacao do
`abrir_os_via_orcamento(orcamento_payload)` mantendo o decorator e a
gravacao do EventoDeOS no mesmo `transaction.atomic`.
"""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.consumer.orcamento_aprovado"


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_orcamento_aprovado(envelope: dict[str, Any]) -> None:
    """Placeholder: TODO Fase 5 (T-OS-041) invocar use case real."""
    payload = envelope.get("payload", {})
    correlation_id = envelope.get("correlation_id")
    logger.info(
        "os.consumer.orcamento_aprovado: TODO T-OS-041 abrir OS — "
        "orcamento_id=%s correlation_id=%s",
        payload.get("orcamento_id"),
        correlation_id,
    )
