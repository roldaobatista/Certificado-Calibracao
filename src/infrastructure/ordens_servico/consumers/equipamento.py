"""T-OS-034 + T-OS-036 + T-OSME-033 — Consumers de eventos do modulo `equipamentos`.

- `Equipamento.Baixado` / `Equipamento.Descartado` (T-OS-034 + T-OSME-033):
  INV-OS-EQP-001. Equipamento baixado/descartado bloqueia abertura de
  novas OS. Atividades JA pendentes (OS em curso) sao marcadas como
  cancelaveis — operador humano decide via use case `cancelar_os` /
  `cancelar_atividade` (Fase 5). Consumer apenas LOGA + grava evento
  pra timeline (saga humana decide o que fazer).

  T-OSME-033 (AC-OSME-004-1): deteccao agora usa `AtividadeDaOS.equipamento_id`
  (nao mais `OS.equipamento_id`) — cobre OS multi-equipamento onde OS.equipamento_id
  pode ser NULL. Usa o indice `atv_tenant_equip_est_idx` (TL-OSME-02) via
  `distinct().values_list("os_id")` em 1 query so (sem N+1).

- `EquipamentoRecebimento.Registrado` (T-OS-036): preenche
  `OS.equipamento_recebimento_id` quando recebimento tem `os_id` no
  payload (cl. 7.5 ISO 17025 / P-OS-R4). Estrutura de recebimento por
  atividade (GATE-OSME-RECEBIMENTO-7.5) fica para quando app equipamentos
  publicar `atividade_id` no payload.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _logar_equipamento_inutilizado(envelope: dict[str, Any], *, consumer_id: str) -> None:
    """T-OSME-033 (AC-OSME-004-1): detecta OSs afetadas via AtividadeDaOS.equipamento_id.

    Usa 1 query com indice atv_tenant_equip_est_idx (TL-OSME-02) — sem N+1.
    Mantém comportamento de APENAS LOGAR (nao cancela — saga humana decide).
    """
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

    from src.infrastructure.ordens_servico.models import AtividadeDaOS

    # AC-OSME-004-1: localiza OSs via AtividadeDaOS.equipamento_id (nao OS.equipamento_id).
    # Cobre OS multi-equip onde OS.equipamento_id = NULL. Indice atv_tenant_equip_est_idx
    # cobre (tenant_id, equipamento_id, estado) — 1 query, sem N+1.
    estados_ativos = ("pendente", "agendada", "em_execucao")
    os_ids_afetados = list(
        AtividadeDaOS.objects.filter(
            equipamento_id=equipamento_uuid,
            estado__in=estados_ativos,
        )
        .values_list("os_id", flat=True)
        .distinct()
    )
    pendentes = len(os_ids_afetados)
    logger.info(
        "%s: equipamento=%s — %d OS pendentes precisam de cancelamento humano "
        "(INV-OS-EQP-001 bloqueia ABERTURA de novas; pendentes ficam pra "
        "decisao do operador). OS ids: %s",
        consumer_id,
        equipamento_uuid,
        pendentes,
        os_ids_afetados[:10],  # log primeiros 10 p/ nao poluir
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
