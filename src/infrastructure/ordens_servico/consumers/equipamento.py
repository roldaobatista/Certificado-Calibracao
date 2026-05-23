"""T-OS-034 + T-OS-036 — Consumers de eventos do modulo `equipamentos`.

- `Equipamento.Baixado` / `Equipamento.Descartado` (T-OS-034):
  INV-OS-EQP-001. Equipamento baixado/descartado bloqueia abertura de
  novas OS. Atividades JA pendentes (OS em curso) sao marcadas como
  cancelaveis — operador humano decide via use case `cancelar_os` /
  `cancelar_atividade` (Fase 5). Consumer apenas LOGA + grava evento
  pra timeline (saga humana decide o que fazer).
- `EquipamentoRecebimento.Registrado` (T-OS-036): preenche
  `OS.equipamento_recebimento_id` quando recebimento tem `os_id` no
  payload (cl. 7.5 ISO 17025 / P-OS-R4).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _logar_equipamento_inutilizado(envelope: dict[str, Any], *, consumer_id: str) -> None:
    payload = envelope.get("payload", {})
    equipamento_id_raw = payload.get("equipamento_id")
    if equipamento_id_raw is None:
        logger.warning("%s: payload sem equipamento_id — skip", consumer_id)
        return
    try:
        equipamento_uuid = UUID(str(equipamento_id_raw))
    except (ValueError, TypeError):
        logger.warning("%s: equipamento_id invalido", consumer_id)
        return

    from src.infrastructure.ordens_servico.models import OS

    estados_pendentes = ("rascunho", "agendada", "em_execucao")
    pendentes = OS.objects.filter(
        equipamento_id=equipamento_uuid,
        estado__in=estados_pendentes,
    ).count()
    logger.info(
        "%s: equipamento=%s — %d OS pendentes precisam de cancelamento humano "
        "(INV-OS-EQP-001 bloqueia ABERTURA de novas; pendentes ficam pra "
        "decisao do operador)",
        consumer_id,
        equipamento_uuid,
        pendentes,
    )


CONSUMER_ID_BAIXADO = "os.consumer.equipamento_baixado"
CONSUMER_ID_DESCARTADO = "os.consumer.equipamento_descartado"
CONSUMER_ID_RECEBIMENTO = "os.consumer.equip_recebimento_registrado"


@consumer_idempotente(consumer_id=CONSUMER_ID_BAIXADO)
def handle_equipamento_baixado(envelope: dict[str, Any]) -> None:
    _logar_equipamento_inutilizado(envelope, consumer_id=CONSUMER_ID_BAIXADO)


@consumer_idempotente(consumer_id=CONSUMER_ID_DESCARTADO)
def handle_equipamento_descartado(envelope: dict[str, Any]) -> None:
    _logar_equipamento_inutilizado(envelope, consumer_id=CONSUMER_ID_DESCARTADO)


@consumer_idempotente(consumer_id=CONSUMER_ID_RECEBIMENTO)
def handle_equipamento_recebimento_registrado(envelope: dict[str, Any]) -> None:
    """T-OS-036 — Preenche OS.equipamento_recebimento_id (cl. 7.5)."""
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    recebimento_id_raw = payload.get("recebimento_id") or payload.get("equipamento_recebimento_id")
    if os_id_raw is None or recebimento_id_raw is None:
        logger.info(
            "%s: payload sem os_id/recebimento_id — skip (recebimento avulso, sem OS).",
            CONSUMER_ID_RECEBIMENTO,
        )
        return
    try:
        os_uuid = UUID(str(os_id_raw))
        recebimento_uuid = UUID(str(recebimento_id_raw))
    except (ValueError, TypeError):
        logger.warning("%s: UUID invalido em payload", CONSUMER_ID_RECEBIMENTO)
        return

    from src.infrastructure.ordens_servico.models import OS

    afetadas = OS.objects.filter(
        id=os_uuid,
        equipamento_recebimento_id__isnull=True,
    ).update(equipamento_recebimento_id=recebimento_uuid)
    if afetadas == 0:
        logger.warning(
            "%s: OS %s ja tem equipamento_recebimento_id OR nao existe — "
            "INV-OS-RCB-001 nao sobrescreve recebimento ja registrado",
            CONSUMER_ID_RECEBIMENTO,
            os_uuid,
        )
