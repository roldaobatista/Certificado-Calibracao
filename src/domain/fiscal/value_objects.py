"""Value Objects AGNÓSTICOS de país/fornecedor da porta fiscal (Fatia 1a, T-FIS-010).

D-FIS-1: o Protocol `FiscalProvider` e estes VOs NÃO conhecem NFS-e/SEFAZ/chave-de-
acesso. Campos específicos do BR (`chave_acesso_44`, `numero`, `protocolo`,
`codigo_municipal`) moram em `metadata: dict` / `raw_response`, NUNCA atributo
nomeado. O VO NÃO valida formato BR (responsabilidade do `Cliente` a montante —
ADR-0017). A tradução BR fica no serializer de infra (borda), não no núcleo.

Todos frozen + slots (imutáveis). `metadata` usa `Mapping`/`field(default_factory)`
para evitar dict mutável compartilhado.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .enums import InvoiceStatus


@dataclass(frozen=True, slots=True)
class InvoicePayload:
    """Payload agnóstico enviado ao provider. Carrega PII CLARA do tomador
    (`customer_taxid`/`customer_name`) — base legal art. 7º II (obrigação fiscal),
    transmitida só a operador sob DPA (INV-FIS-009). Nunca confundir com o evento
    WORM, que leva só `cliente_referencia_hash`.
    """

    tenant_id: UUID
    issuer_taxid: str  # CNPJ/CUIT/RFC — string neutra, sem validação BR aqui
    customer_taxid: str
    customer_name: str
    service_description: str
    service_code: str  # código de serviço local (LC 116 BR / CFDI uso / etc.)
    amount: Decimal  # input do caller (orçamentos diferido — seam pronto)
    issue_date: datetime
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InvoiceResult:
    """Resultado agnóstico do provider. `chave_acesso_44`/`numero`/`protocolo`
    vivem em `metadata`/`raw_response` (D-FIS-1) — NÃO há atributo nomeado BR."""

    invoice_id: str  # id do documento no fornecedor
    status: InvoiceStatus
    authorization_code: str | None = None
    pdf_url: str | None = None
    xml_bytes: bytes | None = None
    rejection_reason: str | None = None
    raw_response: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StorageRef:
    """Referência do XML guardado em storage WORM próprio (B2 — diferido). O stub
    da Fatia 2 devolve um ref local; o adapter real pluga B2 Object Lock."""

    backend: str
    object_key: str
    sha256: str


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Saúde do provider — para circuit breaker e smoke trimestral (diferidos)."""

    healthy: bool
    detail: str = ""
