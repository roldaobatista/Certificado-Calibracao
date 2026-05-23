"""T-OS-031 — Consumers `Calibracao.Iniciada` / `Calibracao.Concluida`.

Modulo `metrologia/calibracao` (Marco 4) ainda nao existe. Consumers ja
ficam REGISTRADOS pra que producers tenham contrato pronto. Side-effect:
atualiza `AtividadeDaOS.link_modulo_tecnico_id` quando payload trouxer
referencia `atividade_id` + `calibracao_id`.

INV-OS-CAL-LINK-001 (janela watchdog) materializada pelo job
`os-calibracao-link-watchdog` (T-OS-090) — este consumer eh quem
PREENCHE o link; watchdog alerta quando demora alem da janela.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _atualizar_link(envelope: dict[str, Any], *, consumer_id: str) -> None:
    payload = envelope.get("payload", {})
    atividade_id_raw = payload.get("atividade_id")
    calibracao_id_raw = payload.get("calibracao_id")
    if atividade_id_raw is None or calibracao_id_raw is None:
        logger.info(
            "%s: payload sem atividade_id/calibracao_id — skip "
            "(modulo metrologia/calibracao ainda em Marco 4); correlation_id=%s",
            consumer_id,
            envelope.get("correlation_id"),
        )
        return
    try:
        atividade_uuid = UUID(str(atividade_id_raw))
        calibracao_uuid = UUID(str(calibracao_id_raw))
    except (ValueError, TypeError):
        logger.warning("%s: UUID invalido em payload — skip", consumer_id)
        return

    from src.infrastructure.ordens_servico.models import AtividadeDaOS

    afetadas = AtividadeDaOS.objects.filter(id=atividade_uuid).update(
        link_modulo_tecnico_id=calibracao_uuid,
    )
    logger.info(
        "%s: atividade=%s linkada a calibracao=%s (afetadas=%d)",
        consumer_id,
        atividade_uuid,
        calibracao_uuid,
        afetadas,
    )


CONSUMER_ID_INICIADA = "os.consumer.calibracao_iniciada"
CONSUMER_ID_CONCLUIDA = "os.consumer.calibracao_concluida"


@consumer_idempotente(consumer_id=CONSUMER_ID_INICIADA)
def handle_calibracao_iniciada(envelope: dict[str, Any]) -> None:
    _atualizar_link(envelope, consumer_id=CONSUMER_ID_INICIADA)


@consumer_idempotente(consumer_id=CONSUMER_ID_CONCLUIDA)
def handle_calibracao_concluida(envelope: dict[str, Any]) -> None:
    _atualizar_link(envelope, consumer_id=CONSUMER_ID_CONCLUIDA)
