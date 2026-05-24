"""T-OS-029 + T-OS-041 — Consumer `Orcamento.Aprovado`.

Substitui o placeholder Fase 4 pela invocacao real do use case
`abrir_os_via_orcamento` (Fase 5). Mantem `@consumer_idempotente`
(ADR-0033) — replay do mesmo envelope nao cria OS duplicada.

Fluxo:
1. `@consumer_idempotente` aplica INV-BUS-001 (causation_id+acao).
2. Parse envelope -> `AbrirOSInput`.
3. `transaction.atomic`: use case grava OS + AtividadeDaOS + EventoDeOS.
4. Loga sucesso + correlation_id.

NOTA Wave A: publicacao do evento bus `OS.Aberta` (audit cadeia + outbox)
via `audit.event_helpers.publicar_evento(...)` sera adicionada quando o
modulo Orcamentos (Wave A) existir e publicar `Orcamento.Aprovado` com
envelope canonico. Por ora, o use case ja grava `EventoDeOS` na timeline
local (visivel por `OSTimelineQueryService` Fase 6).

Erros do use case (`ErroAbrirOS`) sao re-erguidos — o decorator do bus
cuida do dead-letter via ADR-0033.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import transaction

from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ErroAbrirOS,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.bus.consumer_base import consumer_idempotente
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.consumer.orcamento_aprovado"


def _parse_input(envelope: dict[str, Any]) -> AbrirOSInput:
    """Parseia envelope `Orcamento.Aprovado` para `AbrirOSInput`.

    Envelope canonico esperado (estabilizado em Wave A pelo modulo Orcamentos):

        {
          "correlation_id": "<uuid>",
          "payload": {
            "orcamento_id": "<uuid>",
            "tenant_id": "<uuid>",
            "cliente_id": "<uuid>",
            "cliente_referencia_hash": "<sha256hex>",
            "cliente_key_id": "<kms-key-id>",
            "equipamento_id": "<uuid>",
            "equipamento_recebimento_id": "<uuid>|null",
            "analise_critica_id": "<uuid>",
            "analise_critica_snapshot_hash": "<sha256hex>",
            "regra_decisao_acordada": "default|binary|conditional|nao_aplicavel",
            "valor_total": "1234.56",
            "abertura_at": "2026-05-24T13:45:00+00:00",
            "criada_por_user_id": "<uuid>|null",
            "itens": [
              {"tipo": "calibracao", "sequencia": 1, "valor_unitario": "100.00",
               "requer_recebimento": true},
              ...
            ]
          }
        }

    Campos ausentes ou malformados levantam `KeyError` / `ValueError` — bus
    coloca o envelope em `dead_letter_events`.
    """
    payload = envelope["payload"]
    correlation_id = UUID(envelope["correlation_id"])

    itens_raw = payload["itens"]
    if not isinstance(itens_raw, list):
        raise ValueError("payload.itens deve ser lista.")

    itens = tuple(
        ItemOrcamento(
            tipo=TipoAtividade(it["tipo"]),
            sequencia=int(it["sequencia"]),
            valor_unitario=Decimal(str(it["valor_unitario"])),
            requer_recebimento=bool(it["requer_recebimento"]),
        )
        for it in itens_raw
    )

    return AbrirOSInput(
        orcamento_id=UUID(payload["orcamento_id"]),
        tenant_id=UUID(payload["tenant_id"]),
        cliente_id=UUID(payload["cliente_id"]),
        cliente_referencia_hash=str(payload["cliente_referencia_hash"]),
        cliente_key_id=str(payload["cliente_key_id"]),
        equipamento_id=UUID(payload["equipamento_id"]),
        equipamento_recebimento_id=(
            UUID(payload["equipamento_recebimento_id"])
            if payload.get("equipamento_recebimento_id")
            else None
        ),
        analise_critica_id=(
            UUID(payload["analise_critica_id"])
            if payload.get("analise_critica_id")
            else None
        ),
        analise_critica_snapshot_hash=str(payload.get("analise_critica_snapshot_hash", "")),
        regra_decisao_acordada=str(payload.get("regra_decisao_acordada", "")),
        valor_total=Decimal(str(payload["valor_total"])),
        itens=itens,
        correlation_id=correlation_id,
        abertura_at=datetime.fromisoformat(payload["abertura_at"]),
        criada_por_user_id=(
            UUID(payload["criada_por_user_id"])
            if payload.get("criada_por_user_id")
            else None
        ),
    )


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_orcamento_aprovado(envelope: dict[str, Any]) -> None:
    """Abre OS via use case `abrir_os_via_orcamento` (T-OS-041)."""
    correlation_id = envelope.get("correlation_id")
    try:
        os_input = _parse_input(envelope)
    except (KeyError, ValueError, TypeError) as exc:
        logger.error(
            "os.consumer.orcamento_aprovado: envelope invalido correlation_id=%s erro=%s",
            correlation_id,
            exc,
        )
        # Re-levanta — bus encaminha pra dead-letter (ADR-0033).
        raise

    repository = DjangoOSRepository()
    try:
        with transaction.atomic():
            resultado = abrir_os_via_orcamento(
                payload=os_input,
                repository=repository,
            )
    except ErroAbrirOS as exc:
        logger.warning(
            "os.consumer.orcamento_aprovado: regra violada correlation_id=%s codigo=%s http=%s",
            correlation_id,
            exc.codigo,
            exc.http_status,
        )
        raise

    logger.info(
        "os.consumer.orcamento_aprovado: OS aberta os_id=%s numero=%s "
        "atividades=%d correlation_id=%s",
        resultado.os_id,
        resultado.numero_os,
        len(resultado.atividades_planejadas),
        correlation_id,
    )
