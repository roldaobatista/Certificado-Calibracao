"""Consumer `cliente.dados_anonimizados` → propaga anonimização (T-ORC-036).

Quando o módulo `clientes` anonimiza um cliente (LGPD direito ao esquecimento),
este consumer encerra os orçamentos ativos desse cliente e revoga seus links
públicos (corta exposição de PII), preservando os documentos consolidados
(``cliente_referencia_hash`` mantém a trilha — ADR-0032 / D-ORC-4).

Estado-por-estado (ADV-ORC-06 / decisão Roldão 2026-06-15):
  - rascunho → cancelar + revogar link.
  - enviado  → EXPIRAR + revogar link (a máquina D-ORC-3 proíbe enviado→cancelado).
  - aprovado_pendente_os / convertido / terminais → preservar.

Nome canônico do evento: ``cliente.dados_anonimizados`` (``ACOES_CANONICAS``).
GATE-ANON-EVENTO-RECONCILIAR: o módulo `clientes` ainda NÃO publica anonimização
(fail-open lazy — só ``revogar_consentimento``/incidente hoje); este consumer fica
dormente até lá. O consumer de `ordens_servico` escuta ``cliente.anonimizado``
(divergente do canônico) — débito pré-existente a alinhar quando `clientes` publicar.

Worker entra em ``run_in_tenant_context``; ``@consumer_idempotente`` abre a tx.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.application.comercial.orcamentos.ciclo_vida import (
    AnonimizarClienteInput,
    anonimizar_cliente_em_orcamentos,
)
from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "orcamento.consumer.cliente_anonimizado"


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_cliente_anonimizado(envelope: dict[str, Any]) -> None:
    """Cancela rascunhos / expira enviados do cliente anonimizado; preserva o resto."""
    payload = envelope.get("payload", {})
    cliente_id_raw = payload.get("cliente_id")
    if not cliente_id_raw:
        logger.warning(
            "orcamento.consumer.cliente_anonimizado: envelope sem cliente_id correlation_id=%s",
            envelope.get("correlation_id"),
        )
        return
    try:
        cliente_id = UUID(str(cliente_id_raw))
    except (ValueError, TypeError):
        logger.warning(
            "orcamento.consumer.cliente_anonimizado: cliente_id invalido %r", cliente_id_raw
        )
        return

    tenant_raw = envelope.get("tenant_id")
    if not tenant_raw:
        logger.warning(
            "orcamento.consumer.cliente_anonimizado: envelope sem tenant_id correlation_id=%s",
            envelope.get("correlation_id"),
        )
        return
    try:
        tenant_id = UUID(str(tenant_raw))
    except (ValueError, TypeError):
        logger.warning(
            "orcamento.consumer.cliente_anonimizado: tenant_id invalido %r correlation_id=%s",
            tenant_raw,
            envelope.get("correlation_id"),
        )
        return

    from src.infrastructure.orcamentos.repositories import DjangoOrcamentoRepository

    resultado = anonimizar_cliente_em_orcamentos(
        AnonimizarClienteInput(
            tenant_id=tenant_id,
            cliente_id=cliente_id,
            agora=datetime.now(UTC),
        ),
        repo=DjangoOrcamentoRepository(),
    )
    logger.info(
        "orcamento.consumer.cliente_anonimizado: cliente=%s cancelados=%d expirados=%d",
        cliente_id,
        len(resultado.cancelados),
        len(resultado.expirados),
    )
