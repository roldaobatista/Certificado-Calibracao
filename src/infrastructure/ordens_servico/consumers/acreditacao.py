"""T-OS-035 — Consumers `Acreditacao.Vencida` / `Acreditacao.Suspensa`.

Modulo `licencas-acreditacoes` (Wave A) eh GATE-RBC-ESCOPO-1. Ate ele
existir, este consumer:
1. Aplica INV-BUS-001 (idempotencia).
2. Loga o evento + correlation_id.

Side-effect real (bloquear novas atividades calibracao/inmetro do escopo
vencido) viaja pelo predicate `tenant_dentro_escopo_acreditado` quando
ele deixar de ser STUB (T-OS-024) — predicate consulta tabela viva.
Este consumer eh observabilidade da transicao.

GATE-RBC-ESCOPO-1: implementacao real do consumer entra junto com modulo
licencas-acreditacoes e ADR de perfil RBC do tenant (A/B/C/D).
"""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID_VENCIDA = "os.consumer.acreditacao_vencida"
CONSUMER_ID_SUSPENSA = "os.consumer.acreditacao_suspensa"


def _logar(envelope: dict[str, Any], *, tipo: str, consumer_id: str) -> None:
    payload = envelope.get("payload", {})
    logger.info(
        "%s: tenant=%s grandeza=%s escopo=%s correlation_id=%s (%s)",
        consumer_id,
        envelope.get("tenant_id"),
        payload.get("grandeza", ""),
        payload.get("escopo_id", ""),
        envelope.get("correlation_id"),
        tipo,
    )


@consumer_idempotente(consumer_id=CONSUMER_ID_VENCIDA)
def handle_acreditacao_vencida(envelope: dict[str, Any]) -> None:
    _logar(envelope, tipo="vencida", consumer_id=CONSUMER_ID_VENCIDA)


@consumer_idempotente(consumer_id=CONSUMER_ID_SUSPENSA)
def handle_acreditacao_suspensa(envelope: dict[str, Any]) -> None:
    _logar(envelope, tipo="suspensa", consumer_id=CONSUMER_ID_SUSPENSA)
