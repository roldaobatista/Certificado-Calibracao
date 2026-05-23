"""T-OS-032 — Consumers `OS.Faturada` / `OS.Paga`.

Modulo `financeiro` (Wave A futuro) publicara estes eventos. Consumer
atualiza `OS.estado` aplicando transicao explicita (regra: concluida ->
faturada -> paga). Estados pulados nao sao permitidos — defesa em
profundidade contra producers fora do contrato.

INV-OS-ATIV-001: transicao de OS eh COMPUTADA a partir de atividades
(estado_da_os no domain.regras). Aqui apenas estado FINANCEIRO da OS
(faturada/paga) eh setado pelos eventos externos; outros estados
(rascunho/agendada/em_execucao/concluida) sao operacionais e nao chegam
por consumer financeiro.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)


def _transicao_financeira(
    envelope: dict[str, Any],
    *,
    consumer_id: str,
    estado_destino: str,
    estados_origem_validos: tuple[str, ...],
) -> None:
    payload = envelope.get("payload", {})
    os_id_raw = payload.get("os_id")
    if os_id_raw is None:
        logger.warning("%s: payload sem os_id — skip", consumer_id)
        return
    try:
        os_uuid = UUID(str(os_id_raw))
    except (ValueError, TypeError):
        logger.warning("%s: os_id invalido %r", consumer_id, os_id_raw)
        return

    from src.infrastructure.ordens_servico.models import OS

    qs = OS.objects.filter(id=os_uuid, estado__in=estados_origem_validos)
    afetadas = qs.update(estado=estado_destino)
    if afetadas == 0:
        logger.warning(
            "%s: nenhuma OS afetada (os_id=%s) — estado atual fora de %s "
            "(replay tardio OR producer fora de contrato)",
            consumer_id,
            os_uuid,
            estados_origem_validos,
        )


CONSUMER_ID_FATURADA = "os.consumer.os_faturada"
CONSUMER_ID_PAGA = "os.consumer.os_paga"


@consumer_idempotente(consumer_id=CONSUMER_ID_FATURADA)
def handle_os_faturada(envelope: dict[str, Any]) -> None:
    _transicao_financeira(
        envelope,
        consumer_id=CONSUMER_ID_FATURADA,
        estado_destino="faturada",
        estados_origem_validos=("concluida",),
    )


@consumer_idempotente(consumer_id=CONSUMER_ID_PAGA)
def handle_os_paga(envelope: dict[str, Any]) -> None:
    _transicao_financeira(
        envelope,
        consumer_id=CONSUMER_ID_PAGA,
        estado_destino="paga",
        estados_origem_validos=("faturada",),
    )
