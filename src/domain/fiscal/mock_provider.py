"""`MockFiscalProvider` — implementação determinística da porta para testes
(Fatia 1a, T-FIS-012). Vive no DOMÍNIO (D-FIS-8): sem I/O, sem SDK, sem rede;
é a implementação de referência do Protocol `FiscalProvider`.

4 modos (ADR-0008 §2 "MockFiscalProvider"):
  - `always_authorize`     → AUTHORIZED + `authorization_code`.
  - `always_reject`        → REJECTED + `rejection_reason`.
  - `pending_then_authorize` → 1ª `emit` devolve PENDING; `query_status` subsequente
                               devolve AUTHORIZED (resolução do PENDING — D-FIS-3).
  - `network_timeout`      → levanta `ProviderTimeoutError` (transporte — nenhuma
                               persistência da nota).

`invoice_id` é DETERMINÍSTICO por payload (mesmo payload → mesmo id) para testes
reproduzíveis. A derivação usa `zlib.crc32` (checksum não-criptográfico) sobre SÓ
campos não-PII (`tenant_id`/`service_code`/`amount`/`issue_date`) — NÃO inclui
`customer_taxid`/`customer_name` (não é hash de PII; é só um id estável de mock).
"""

from __future__ import annotations

import hashlib
import zlib
from enum import Enum

from .enums import InvoiceStatus
from .erros import ProviderTimeoutError
from .value_objects import HealthStatus, InvoicePayload, InvoiceResult, StorageRef


class ModoMock(str, Enum):
    """Modos determinísticos do mock."""

    ALWAYS_AUTHORIZE = "always_authorize"
    ALWAYS_REJECT = "always_reject"
    PENDING_THEN_AUTHORIZE = "pending_then_authorize"
    NETWORK_TIMEOUT = "network_timeout"


def _id_deterministico(payload: InvoicePayload) -> str:
    """id estável por payload, derivado SÓ de campos não-PII (sem tomador).

    `zlib.crc32` (não-cripto) é suficiente para um id de mock e evita qualquer
    ambiguidade com hash de PII — não há dado do tomador na derivação."""
    base = (
        f"{payload.tenant_id}|{payload.service_code}|"
        f"{payload.amount}|{payload.issue_date.isoformat()}"
    )
    return f"MOCK-{zlib.crc32(base.encode('utf-8')) & 0xFFFFFFFF:08x}"


class MockFiscalProvider:
    """Provider de teste — satisfaz `FiscalProvider` estruturalmente."""

    def __init__(self, modo: ModoMock = ModoMock.ALWAYS_AUTHORIZE) -> None:
        self.modo = modo
        # invoice_ids emitidos em PENDING aguardando resolução por query_status
        self._pendentes: set[str] = set()

    def emit_invoice(self, payload: InvoicePayload) -> InvoiceResult:
        invoice_id = _id_deterministico(payload)

        if self.modo is ModoMock.NETWORK_TIMEOUT:
            raise ProviderTimeoutError("mock: timeout de rede simulado")

        if self.modo is ModoMock.ALWAYS_REJECT:
            return InvoiceResult(
                invoice_id=invoice_id,
                status=InvoiceStatus.REJECTED,
                rejection_reason="mock: rejeição determinística",
                raw_response={"mock_modo": self.modo.value},
            )

        if self.modo is ModoMock.PENDING_THEN_AUTHORIZE:
            self._pendentes.add(invoice_id)
            return InvoiceResult(
                invoice_id=invoice_id,
                status=InvoiceStatus.PENDING,
                raw_response={"mock_modo": self.modo.value},
            )

        # ALWAYS_AUTHORIZE
        return InvoiceResult(
            invoice_id=invoice_id,
            status=InvoiceStatus.AUTHORIZED,
            authorization_code="MOCK-AUTH-" + invoice_id[-8:],
            pdf_url=f"mock://pdf/{invoice_id}",
            xml_bytes=b"<mock-nfse/>",
            raw_response={"mock_modo": self.modo.value},
            metadata={"chave_acesso_44": "0" * 44, "numero": invoice_id[-8:]},
        )

    def cancel_invoice(self, invoice_id: str, reason: str) -> InvoiceResult:
        self._pendentes.discard(invoice_id)
        return InvoiceResult(
            invoice_id=invoice_id,
            status=InvoiceStatus.CANCELED,
            raw_response={"mock_cancelamento_motivo": reason},
        )

    def query_status(self, invoice_id: str) -> InvoiceStatus:
        if invoice_id in self._pendentes:
            # resolve o PENDING → AUTHORIZED (modo pending_then_authorize)
            self._pendentes.discard(invoice_id)
            return InvoiceStatus.AUTHORIZED
        if self.modo is ModoMock.ALWAYS_REJECT:
            return InvoiceStatus.REJECTED
        return InvoiceStatus.AUTHORIZED

    def store_xml(self, invoice_id: str, xml: bytes) -> StorageRef:
        sha = hashlib.sha256(xml).hexdigest()  # audit-pii-salt: skip -- integridade do XML, nao e PII
        return StorageRef(backend="mock", object_key=f"mock/{invoice_id}.xml", sha256=sha)

    def supported_countries(self) -> list[str]:
        return ["BR"]

    def health_check(self) -> HealthStatus:
        healthy = self.modo is not ModoMock.NETWORK_TIMEOUT
        return HealthStatus(healthy=healthy, detail=f"mock modo={self.modo.value}")
