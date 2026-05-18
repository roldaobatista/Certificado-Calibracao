"""EventBus Protocol + DomainEvent base.

Conforme ADR-0007 §4: bus explicito em vez de Django signals.

Implementacao concreta (Celery/Procrastinate) vive em
src/infrastructure/eventbus/. Codigo de dominio NUNCA importa
infrastructure — sempre Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Protocol, runtime_checkable
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base de todo evento de dominio.

    Campos obrigatorios em TODOS os eventos (alinhado com INV-INT-001/009 do
    REGRAS-INEGOCIAVEIS — envelope de bus inter-modulos).
    """

    event_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID | None = None
    causation_id: UUID | None = None


@runtime_checkable
class EventBus(Protocol):
    """Contrato do bus de eventos (implementado em infrastructure/eventbus/).

    `emit` publica um evento. `subscribe` registra um handler. Em runtime
    Django, o adapter Procrastinate enfileira o handler como task — handlers
    rodam em transacao separada, sem bloquear o use case.
    """

    def emit(self, event: DomainEvent) -> None: ...

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None: ...
