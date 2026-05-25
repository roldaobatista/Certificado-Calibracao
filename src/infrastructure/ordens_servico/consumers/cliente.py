"""T-OS-030 — Consumer `Cliente.Anonimizado`.

Quando modulo `clientes` (Marco 1) anonimiza cliente (LGPD art. 18 V),
propaga em OS preservando `cliente_referencia_hash` e zerando `cliente_id`
(ADR-0032 + INV-OS-ANON-001).

Side-effect real: UPDATE em `ordens_servico` setando `cliente=NULL`
para todas OS do tenant cujo `cliente_id` bate o anonimizado.
`cliente_referencia_hash` ja foi gravado na abertura (snapshot
imutavel) — preserva audit pos-anonimizacao.

Bloqueio (INV-OS-ANON-001): se houver OS COM atividade pendente da
mesma OS anonimizada, anonimizacao NAO devia ter ocorrido em primeiro
lugar (predicate `cliente_tem_os_aberta` em Marco 1 deveria ter
bloqueado). Defesa em profundidade: se chegou aqui com OS aberta,
grava DLE manualmente e re-publica `Cliente.AnonimizacaoBloqueada`
(saga T-OS-037 fecha o loop).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.db.models import Q

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.consumer.cliente_anonimizado"


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_cliente_anonimizado(envelope: dict[str, Any]) -> None:
    """Propaga anonimizacao: cliente_id -> NULL em OS do tenant."""
    payload = envelope.get("payload", {})
    cliente_id_raw = payload.get("cliente_id")
    if cliente_id_raw is None:
        logger.warning(
            "os.consumer.cliente_anonimizado: envelope sem cliente_id no payload — "
            "correlation_id=%s",
            envelope.get("correlation_id"),
        )
        return

    try:
        cliente_uuid = UUID(str(cliente_id_raw))
    except (ValueError, TypeError):
        logger.warning(
            "os.consumer.cliente_anonimizado: cliente_id invalido %r", cliente_id_raw
        )
        return

    # Import tardio — apps loading
    from src.infrastructure.ordens_servico.models import OS

    # SEG-M3-OS-01 (P5 conserto): tenant_id explicito no WHERE como defesa
    # em profundidade — worker outbox ja entra em run_in_tenant_context
    # (RLS isola), mas filtro explicito protege contra: contexto vazado
    # em teste mal isolado, role bypass acidental, retrofit que perca
    # contexto. Extracao do envelope eh confiavel — `_validar_tenant_no_contexto`
    # do publicar_evento garantiu igualdade tenant_id == active.
    tenant_uuid_str = envelope.get("tenant_id")
    tenant_filter = (
        {"tenant_id": UUID(str(tenant_uuid_str))} if tenant_uuid_str else {}
    )

    # INV-OS-ANON-001 defesa em profundidade: se houver OS NAO-terminal
    # com este cliente, registra warning (Marco 1 nao devia ter
    # publicado Anonimizado nesse caso — saga T-OS-037 trata).
    estados_terminais = {"concluida", "cancelada", "faturada", "paga"}
    pendentes = OS.objects.filter(
        cliente_id=cliente_uuid, **tenant_filter,
    ).exclude(estado__in=estados_terminais)
    pendentes_count = pendentes.count()
    if pendentes_count > 0:
        logger.warning(
            "os.consumer.cliente_anonimizado: %d OS nao-terminais com cliente=%s — "
            "anonimizacao deveria ter sido bloqueada por cliente_tem_os_aberta "
            "(INV-OS-ANON-001). Saga os-anonimizacao-retry vai re-propagar "
            "quando OS concluir.",
            pendentes_count,
            cliente_uuid,
        )

    # Side-effect real: zera cliente_id em TODAS as OS do tenant (terminais
    # ou nao). cliente_referencia_hash preserva audit (ADR-0032).
    afetadas = (
        OS.objects.filter(Q(cliente_id=cliente_uuid), **tenant_filter).update(
            cliente_id=None
        )
    )
    logger.info(
        "os.consumer.cliente_anonimizado: %d OS atualizadas cliente=%s -> NULL",
        afetadas,
        cliente_uuid,
    )
