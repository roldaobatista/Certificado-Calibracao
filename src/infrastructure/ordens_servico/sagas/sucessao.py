"""T-OS-038 — Saga "Reabertura cross-cliente M&A" (INV-OS-SUC-001).

Quando cliente sucedido (vendido / fundido / cindido) tem OS sendo
reaberta pelo cliente sucessor, exige `SucessaoSocietaria` aprovada
(documento + A3 admin).

Entidade `SucessaoSocietaria` ainda nao existe (GATE-OS-SUCESSAO-EVIDENCIA
Wave A). Ate la, saga apenas:
1. Aplica INV-BUS-001 (idempotencia).
2. Quando recebe `OS.ReaberturaSolicitada` com `cliente_id_sucessor != cliente_id_original`,
   LOGA + nega via re-publish `OS.ReaberturaBloqueada`.

Side-effect real (criacao de SucessaoSocietaria + validacao A3 admin)
fica em GATE pra Marco 3 dogfooding nao precisar dele (so o 1o tenant
externo). Drilldown: AC-OS-006-7 = bloqueio 412 quando cross-cliente sem
sucessao aprovada.
"""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID = "os.saga.reabertura_sucessao"


@consumer_idempotente(consumer_id=CONSUMER_ID)
def handle_reabertura_solicitada(envelope: dict[str, Any]) -> None:
    """STUB Marco 3 (GATE-OS-SUCESSAO-EVIDENCIA): apenas LOGA decisao.

    Bloqueio efetivo de reabertura cross-cliente acontece DENTRO do
    use case `reabrir_os` (operacoes_avancadas.py) — valida
    `sucessao_societaria_id` e raises `ErroReabrir(412)` se ausente.
    Este consumer eh OBSERVABILIDADE retroativa do evento via bus +
    GATE pra Wave A publicar `OS.ReaberturaBloqueada` em portal-cliente.
    Docstring agora reflete o corpo: LOGA + GATE.
    """
    payload = envelope.get("payload", {})
    cliente_original = payload.get("cliente_id_original")
    cliente_sucessor = payload.get("cliente_id_sucessor")
    sucessao_id = payload.get("sucessao_societaria_id")

    if cliente_original == cliente_sucessor:
        return  # mesma entidade — saga nao aplica.

    if sucessao_id is None:
        logger.warning(
            "os.saga.reabertura_sucessao: BLOQUEIA reabertura cross-cliente sem "
            "SucessaoSocietaria. tenant=%s original=%s sucessor=%s correlation_id=%s "
            "(INV-OS-SUC-001 + AC-OS-006-7 -> 412)",
            envelope.get("tenant_id"),
            cliente_original,
            cliente_sucessor,
            envelope.get("correlation_id"),
        )
        # TODO GATE-OS-SUCESSAO-EVIDENCIA: republicar OS.ReaberturaBloqueada
        # pra portal-cliente + OmniChannel.
        return

    logger.info(
        "os.saga.reabertura_sucessao: LIBERA reabertura cross-cliente — "
        "sucessao=%s original=%s sucessor=%s",
        sucessao_id,
        cliente_original,
        cliente_sucessor,
    )
