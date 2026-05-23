"""T-OS-039 — Saga "Sync mobile" (ADR-0027 + INV-OS-SYNC-001).

App-tecnico mobile (Wave A, depende de ADR-0003) opera offline-first.
Quando volta online, sincroniza:
- Atividades modificadas: merge LWW POR atividade (atividade_id).
- Fotos: APPEND-ONLY (`EvidenciaFotoAtividade` nunca eh UPDATE — sempre
  INSERT mesmo em conflito).

Esta saga consome eventos `Sync.AtividadeRecebida` / `Sync.FotoRecebida`
publicados pelo endpoint de sync (Fase 8 / view set mobile). Side-effect:
1. LWW: aplica patch da atividade se `payload.modificado_em` >
   `atividade.atualizada_em_servidor`.
2. Foto: simplesmente INSERT em `EvidenciaFotoAtividade` (FK polimorfica
   evita conflito; `tipo_evidencia=foto` cobre todos os casos).

INV-OS-SYNC-001: foto NUNCA perde. Sync que detecta conflito de foto
GRAVA AMBAS (uma vence "principal" via timestamp; outra vai pra evidencia
auxiliar com tipo_evidencia=auxiliar).
"""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.bus.consumer_base import consumer_idempotente

logger = logging.getLogger(__name__)

CONSUMER_ID_ATIVIDADE = "os.saga.sync_atividade"
CONSUMER_ID_FOTO = "os.saga.sync_foto"


@consumer_idempotente(consumer_id=CONSUMER_ID_ATIVIDADE)
def handle_sync_atividade(envelope: dict[str, Any]) -> None:
    """LWW por atividade — TODO Wave A app-tecnico mobile."""
    payload = envelope.get("payload", {})
    logger.info(
        "os.saga.sync_atividade: TODO ADR-0027 merge LWW atividade=%s modificado_em=%s",
        payload.get("atividade_id"),
        payload.get("modificado_em"),
    )


@consumer_idempotente(consumer_id=CONSUMER_ID_FOTO)
def handle_sync_foto(envelope: dict[str, Any]) -> None:
    """Foto append-only — INV-OS-SYNC-001."""
    payload = envelope.get("payload", {})
    logger.info(
        "os.saga.sync_foto: TODO ADR-0027 append-only foto atividade=%s hash=%s",
        payload.get("atividade_id"),
        payload.get("foto_sha256", "")[:16],
    )
