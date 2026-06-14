"""T-OS-029 + T-OS-041 — Consumer `Orcamento.Aprovado` + T-OSME-030 (Fatia 2).

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

T-OSME-030 (AC-OSME-002 / AC-OSME-004):
- `_parse_input`: `equipamento_id` por ITEM (header vira legado/fallback).
  Item com equipamento_id -> atividade tecnica; sem -> ItemComercialOS (D-OSME-3).
- Pre-check itera TODOS os equipamentos distintos dos itens (nao so 1 do header):
  422 `EquipamentoBaixadoEmOS` se QUALQUER estiver SUCATA/EXTRAVIADO.
  1 query so (filter id__in=...) — sem N+1 (AC-OSME-004-2).

Envelope canonico atualizado (v2 — Wave A com modulo Orcamentos):

    {
      "correlation_id": "<uuid>",
      "payload": {
        "orcamento_id": "<uuid>",
        "tenant_id": "<uuid>",
        "cliente_id": "<uuid>",
        "cliente_referencia_hash": "<sha256hex>",
        "cliente_key_id": "<kms-key-id>",
        "equipamento_id": "<uuid>|null",           <- LEGADO: fallback se item nao traz equip
        "equipamento_recebimento_id": "<uuid>|null",
        "analise_critica_id": "<uuid>",
        "analise_critica_snapshot_hash": "<sha256hex>",
        "regra_decisao_acordada": "default|binary|conditional|nao_aplicavel",
        "valor_total": "1234.56",
        "abertura_at": "2026-05-24T13:45:00+00:00",
        "criada_por_user_id": "<uuid>|null",
        "itens": [
          {
            "tipo": "calibracao",
            "sequencia": 1,
            "valor_unitario": "100.00",
            "requer_recebimento": true,
            "equipamento_id": "<uuid>|null"        <- POR ITEM (v2). None => ItemComercialOS
          },
          ...
        ]
      }
    }

Compatibilidade legada: se item nao traz `equipamento_id` (v1 envelope), o
campo `payload.equipamento_id` do header serve como fallback para TODOS os itens
sem equipamento proprio. Isso garante que envelopes v1 (1 item, 1 equipamento)
continuem gerando atividades tecnicas sem mudanca de contrato.
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

# Onda PRE-A.4: import publicar_evento_bus removido — repository.publicar_evento agora cruza pro bus via INT-01.
from src.infrastructure.bus.consumer_base import consumer_idempotente
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

# T-OS-044 / AC-OS-001-5 (INV-OS-EQP-001) — equipamento em estado terminal
# bloqueia abertura de OS. Pre-check do consumer (use case eh puro).
_ESTADOS_EQUIPAMENTO_BLOQUEIAM_OS: frozenset[str] = frozenset(
    {
        EquipamentoStatus.SUCATA,
        EquipamentoStatus.EXTRAVIADO,
    }
)


class EquipamentoBaixadoEmOSError(Exception):
    """Levantada pelo consumer quando equipamento.status bloqueia abertura."""

    def __init__(self, equipamento_id: UUID, status: str) -> None:
        super().__init__(
            f"EquipamentoBaixadoEmOS: status={status} para equipamento={equipamento_id}"
        )
        self.codigo = "EquipamentoBaixadoEmOS"
        self.http_status = 422
        self.equipamento_id = equipamento_id
        self.status = status

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.consumer.orcamento_aprovado"


def _parse_input(envelope: dict[str, Any]) -> AbrirOSInput:
    """Parseia envelope `Orcamento.Aprovado` para `AbrirOSInput`.

    T-OSME-030: equipamento_id agora e POR ITEM (v2 envelope). O campo
    `payload.equipamento_id` do header e LEGADO/FALLBACK: se o item nao traz
    `equipamento_id` proprio, usa o do header (garante compatibilidade com
    envelopes v1 de 1 equipamento). Se item traz `equipamento_id` proprio, usa ele.
    Item sem equipamento em nenhum dos dois -> ItemComercialOS (None).

    Campos ausentes ou malformados levantam `KeyError` / `ValueError` — bus
    coloca o envelope em `dead_letter_events`.
    """
    payload = envelope["payload"]
    correlation_id = UUID(envelope["correlation_id"])

    itens_raw = payload["itens"]
    if not isinstance(itens_raw, list):
        raise ValueError("payload.itens deve ser lista.")

    # equipamento_id do header: fallback legado para itens sem equipamento proprio (v1).
    header_equipamento_raw = payload.get("equipamento_id")
    header_equipamento_id: UUID | None = (
        UUID(str(header_equipamento_raw)) if header_equipamento_raw else None
    )

    itens = tuple(
        ItemOrcamento(
            tipo=TipoAtividade(it["tipo"]),
            sequencia=int(it["sequencia"]),
            valor_unitario=Decimal(str(it["valor_unitario"])),
            requer_recebimento=bool(it["requer_recebimento"]),
            # v2: equipamento_id por item. v1 legado: fallback para header_equipamento_id.
            # None em ambos -> item comercial (D-OSME-3 / AC-OSME-006-3).
            equipamento_id=(
                UUID(str(it["equipamento_id"]))
                if it.get("equipamento_id")
                else header_equipamento_id
            ),
        )
        for it in itens_raw
    )

    return AbrirOSInput(
        orcamento_id=UUID(payload["orcamento_id"]),
        tenant_id=UUID(payload["tenant_id"]),
        cliente_id=UUID(payload["cliente_id"]),
        cliente_referencia_hash=str(payload["cliente_referencia_hash"]),
        cliente_key_id=str(payload["cliente_key_id"]),
        equipamento_id=header_equipamento_id,
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
        with run_in_tenant_context(os_input.tenant_id), transaction.atomic():
            # T-OSME-030 / AC-OSME-004-2 (INV-OS-EQP-001): pre-check itera TODOS os
            # equipamentos distintos dos itens. 1 query (sem N+1). Rejeita 422 se QUALQUER
            # estiver SUCATA/EXTRAVIADO.
            equip_ids_itens = {
                item.equipamento_id
                for item in os_input.itens
                if item.equipamento_id is not None
            }
            if equip_ids_itens:
                bloqueados = list(
                    Equipamento.all_objects.filter(
                        id__in=equip_ids_itens,
                        status__in=_ESTADOS_EQUIPAMENTO_BLOQUEIAM_OS,
                    ).values_list("id", "status")
                )
                if bloqueados:
                    # Reporta o primeiro bloqueado encontrado.
                    equip_id_bloq, status_bloq = bloqueados[0]
                    raise EquipamentoBaixadoEmOSError(
                        equipamento_id=equip_id_bloq,
                        status=status_bloq,
                    )

            resultado = abrir_os_via_orcamento(
                payload=os_input,
                repository=repository,
            )
            # INT-01 Onda PRE-A.4 (auditoria 10 lentes pré-Wave A): publicar_evento_bus
            # redundante removido — agora `repository.publicar_evento(OS_ABERTA)` dentro
            # do use case `abrir_os_via_orcamento` ja cruza pro bus_outbox via mapa
            # MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS (`os.aberta` -> bus). Mantinha aqui
            # produzia duplicacao (2 linhas em bus_outbox por OS aberta).
    except (ErroAbrirOS, EquipamentoBaixadoEmOSError) as exc:
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
