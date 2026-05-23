"""T-OS-033 — Consumers `Tenant.Suspenso` / `Tenant.Encerrado`.

ADR-0035 (proposta) cravara matriz operacoes M3 x estado tenant
(operacional / suspenso / encerrado). Ate la (GATE-OS-TENANT-SUSPENSO),
consumer apenas:
1. Aplica INV-BUS-001 (idempotencia).
2. Loga evento com correlation_id.

Comportamento real (read-only / bloqueio total) eh APLICADO no
predicate `tenant_nao_suspenso` (clientes/predicates_authz.py) +
`pode_criar_os_produtiva_balancas` (este modulo) — predicates leem
`Tenant.status_lifecycle` DIRETO. Este consumer eh observabilidade
operacional do evento; estado vive em `tenant.status_lifecycle`.
"""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID_SUSPENSO = "os.consumer.tenant_suspenso"
CONSUMER_ID_ENCERRADO = "os.consumer.tenant_encerrado"


@consumer_idempotente(consumer_id=CONSUMER_ID_SUSPENSO)
def handle_tenant_suspenso(envelope: dict[str, Any]) -> None:
    payload = envelope.get("payload", {})
    logger.info(
        "os.consumer.tenant_suspenso: tenant=%s modo=%s motivo=%s correlation_id=%s",
        envelope.get("tenant_id"),
        payload.get("modo", "read_only"),
        payload.get("motivo_categoria", ""),
        envelope.get("correlation_id"),
    )
    # TODO ADR-0035: aplicar matriz de bloqueio por modo (read_only|bloqueado_total).


@consumer_idempotente(consumer_id=CONSUMER_ID_ENCERRADO)
def handle_tenant_encerrado(envelope: dict[str, Any]) -> None:
    logger.info(
        "os.consumer.tenant_encerrado: tenant=%s correlation_id=%s",
        envelope.get("tenant_id"),
        envelope.get("correlation_id"),
    )
    # TODO ADR-0035: tenant encerrado -> OS pendentes movem para arquivo morto
    # respeitando retencao Receita 5a / ISO 17025 25a (LGPD art. 16).
