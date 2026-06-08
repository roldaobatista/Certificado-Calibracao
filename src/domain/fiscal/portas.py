"""Porta `FiscalProvider` (Protocol) — contrato AGNÓSTICO de país/fornecedor
(ADR-0008 §1, Fatia 1a — T-FIS-011).

INV-FIS-003: domínio/use case NUNCA importam SDK de fornecedor; toda emissão passa
por este Protocol. O use case sempre recebe um `FiscalProvider` injetado (D-FIS-8)
— agnóstico de qual implementação (mock no domínio, adapter real ou circuit breaker
na infra). `import plugnotas*`/`focus*`/`pybreaker` só em `infrastructure/fiscal/`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .enums import InvoiceStatus
from .value_objects import HealthStatus, InvoicePayload, InvoiceResult, StorageRef


@runtime_checkable
class FiscalProvider(Protocol):
    """Emissor de documento fiscal de serviço. Síncrono — o adapter real cuida de
    retry interno. `emit_invoice` pode levantar `ProviderTimeoutError` (transporte):
    nesse caso nenhuma nota é persistida (D-FIS-3)."""

    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult:
        """Emite o documento. PENDING (assíncrono no fornecedor), AUTHORIZED ou
        REJECTED. Timeout de rede → `ProviderTimeoutError`."""
        ...

    def cancel_invoice(self, invoice_id: str, reason: str) -> InvoiceResult:
        """Cancela documento emitido. Janela/regras dependem da legislação local
        (validadas a montante no use case — janela 24h, motivo ≥30ch)."""
        ...

    def query_status(self, invoice_id: str) -> InvoiceStatus:
        """Consulta status — resolve notas que ficaram PENDING (único caminho
        PENDING→terminal, D-FIS-3)."""
        ...

    def store_xml(self, invoice_id: str, xml: bytes) -> StorageRef:
        """Garante cópia do XML/JSON probatório no nosso storage WORM (B2 —
        diferido; stub na Fatia 2)."""
        ...

    def supported_countries(self) -> list[str]:
        """Códigos de país cobertos (ISO 3166-1 alpha-2). Mock = ['BR']."""
        ...

    def health_check(self) -> HealthStatus:
        """Para circuit breaker e smoke trimestral (diferidos)."""
        ...
