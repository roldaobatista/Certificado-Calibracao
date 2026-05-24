"""Timeline de eventos da OS — T-OS-088 (INV-OS-AUD-001).

Retorna eventos sanitizados (sem PII cru — hashes apenas) pro portal-cliente.
Atravessa `repository.listar_eventos_por_os` em ordem cronologica decrescente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.operacao.os.repository import OSRepository


@dataclass(frozen=True, slots=True)
class EventoTimeline:
    evento_id: UUID
    tipo: str
    atividade_id: UUID | None
    payload_data: dict[str, object]  # ja sanitizado em escrita
    correlation_id: UUID
    occurred_at: datetime


def timeline_da_os(
    os_id: UUID,
    repository: OSRepository,
    *,
    limit: int = 100,
) -> list[EventoTimeline]:
    """Retorna timeline de eventos da OS, ordenada do mais recente."""
    if limit < 1 or limit > 500:
        raise ValueError("limit deve estar entre 1 e 500")
    snaps = repository.listar_eventos_por_os(os_id, limit=limit)
    return [
        EventoTimeline(
            evento_id=s.id,
            tipo=s.tipo.value,
            atividade_id=s.atividade_id,
            payload_data=dict(s.payload_data),
            correlation_id=s.correlation_id,
            occurred_at=s.occurred_at,
        )
        for s in snaps
    ]
