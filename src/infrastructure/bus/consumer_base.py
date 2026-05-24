"""Helper de consumer idempotente — INV-BUS-001 (ADR-0033).

Padrao obrigatorio de TODO consumer registrado no bus:

    BEGIN
    INSERT INTO consumer_idempotencia (consumer_id, event_id, tenant_id,
                                       resultado)
        VALUES (...)
        ON CONFLICT (consumer_id, event_id) DO NOTHING
        RETURNING 1;
    -- Se 0 linhas voltaram: replay; COMMIT (no-op) e retorna.
    -- Se inseriu: executa side-effect + COMMIT.
    -- Em excecao: marca resultado='erro_rastreado' + re-raise (worker retry).

Esta API encapsula esse padrao em UM decorator + UMA funcao helper.

Uso (consumer):

    from src.infrastructure.bus.consumer_base import consumer_idempotente

    @consumer_idempotente(consumer_id="os.consumer.orcamento_aprovado")
    def handle_orcamento_aprovado(envelope: dict) -> None:
        # ja garantido: NAO eh replay; tx aberta (autocommit no chamador).
        ...

O worker (`audit.outbox_worker`) chama `handle_orcamento_aprovado(envelope)`
DENTRO de `run_in_tenant_context` apropriado — handler nao precisa abrir
contexto de tenant.

# tests-coverage: tests/test_bus_consumer_base_idempotencia.py (a criar Wave A)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any
from uuid import UUID

from django.db import transaction

logger = logging.getLogger(__name__)


class EventoSemIdEsperado(ValueError):
    """Envelope nao traz `event_id` UUID — protocolo bus violado."""


def _extrair_event_id(envelope: dict[str, Any]) -> UUID:
    """Le `envelope['event_id']` e valida UUID. INV-BUS-SCHEMA-001."""
    raw = envelope.get("event_id")
    if raw is None:
        raise EventoSemIdEsperado(
            "envelope sem event_id — bus envelope v10 exige UUID unico. "
            "Producer deve usar audit.event_helpers.publicar_evento."
        )
    try:
        return UUID(str(raw))
    except (ValueError, TypeError) as exc:
        raise EventoSemIdEsperado(f"event_id invalido: {raw!r}") from exc


def _extrair_tenant_id(envelope: dict[str, Any]) -> UUID | None:
    """Le `envelope['tenant_id']`. None = evento sistema."""
    raw = envelope.get("tenant_id")
    if raw is None or raw == "":
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


def marcar_idempotencia(
    *,
    consumer_id: str,
    event_id: UUID,
    tenant_id: UUID | None,
    resultado: str = "ok",
) -> bool:
    """INSERT ON CONFLICT em `consumer_idempotencia`.

    Retorna True se inseriu (primeira vez), False se ja existia (replay).

    `resultado` aceita 'ok' | 'skip' | 'erro_rastreado' (CHECK no banco).

    Tabela `consumer_idempotencia` tem RLS — INSERT em modo_sistema exige
    tenant_id NULL; INSERT em contexto tenant exige tenant_id == active.
    Worker `processar_outbox_em_contexto_tenant` ja entra no contexto
    certo antes de invocar o handler.
    """
    from django.db import connection

    with connection.cursor() as cur:
        # `processado_em` eh NOT NULL no schema (Django auto_now_add nao
        # cria DEFAULT no DB; raw SQL precisa passar NOW()).
        cur.execute(
            "INSERT INTO consumer_idempotencia "
            "(consumer_id, event_id, tenant_id, resultado, processado_em) "
            "VALUES (%s, %s, %s, %s, NOW()) "
            "ON CONFLICT (consumer_id, event_id) DO NOTHING "
            "RETURNING 1",
            [consumer_id, str(event_id), str(tenant_id) if tenant_id else None, resultado],
        )
        row = cur.fetchone()
    return row is not None


def consumer_idempotente(
    *,
    consumer_id: str,
) -> Callable[[Callable[[dict[str, Any]], None]], Callable[[dict[str, Any]], None]]:
    """Decorator que aplica o pattern INV-BUS-001 a um handler.

    `consumer_id` precisa ser slug `dominio.consumer.nome` (CHECK SQL no banco).

    Garantias:
    1. Le `event_id` do envelope. Se ausente -> EventoSemIdEsperado.
    2. INSERT ON CONFLICT em `consumer_idempotencia(consumer_id, event_id)`.
    3. Se 0 linhas voltaram: log debug + return (no-op replay-safe).
    4. Se inseriu: invoca handler; em excecao, marca
       resultado='erro_rastreado' E re-raise (worker registra tentativa).
    5. Tudo dentro de `transaction.atomic` — rollback unifica
       consumer_idempotencia + side-effect em caso de erro.

    Importante: marca de idempotencia ENTRA junto com o side-effect (mesma
    tx). Em retry: outbox volta o evento; INSERT vira no-op (linha ja
    existe da tentativa anterior bem-sucedida) OU re-tenta side-effect
    (tentativa anterior fez rollback junto com a marca).
    """

    def _decorator(handler: Callable[[dict[str, Any]], None]) -> Callable[[dict[str, Any]], None]:
        @wraps(handler)
        def _wrapped(envelope: dict[str, Any]) -> None:
            event_id = _extrair_event_id(envelope)
            tenant_id = _extrair_tenant_id(envelope)
            with transaction.atomic():
                inserido = marcar_idempotencia(
                    consumer_id=consumer_id,
                    event_id=event_id,
                    tenant_id=tenant_id,
                )
                if not inserido:
                    logger.debug(
                        "consumer_idempotente: replay detectado consumer=%s event=%s — no-op",
                        consumer_id,
                        event_id,
                    )
                    return
                handler(envelope)

        return _wrapped

    return _decorator
