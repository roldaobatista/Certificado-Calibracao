"""Entidade persistível do domínio fiscal (Fatia 1a — T-FIS-013).

`NotaFiscalServico` é um snapshot WORM (frozen + slots): a tabela física é
append-only (WORM Padrão B — INV-FIS-004), mas o `status` é mutável SÓ pelas
transições válidas da máquina de estados (D-FIS-4: a linha reflete o estado atual;
a imutabilidade probatória vem do evento append-only na cadeia hash + do
`snapshot_hash` canonicalizado, não de proibir o UPDATE da coluna `status`).

A LÓGICA vive aqui (domínio puro, ADR-0007/0072); a TABELA física e os triggers
vivem em `infrastructure/fiscal/` (Fatia 1b).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .enums import InvoiceStatus, PerfilRegulatorio, TipoAcreditacaoVinculo, TipoServico


@dataclass(frozen=True, slots=True)
class NotaFiscalServico:
    """Documento fiscal de serviço emitido (ou em emissão). WORM.

    Idempotência de NEGÓCIO por `(tenant_id, origem_id, versao)` (D-FIS-2 /
    INV-FIS-005): dois POSTs `emitir` da mesma origem → a mesma nota (não
    re-emite). `cliente_referencia_hash` = pseudônimo do tomador para a trilha
    (PII clara só no `InvoicePayload` ao provider — INV-FIS-009).
    """

    nfse_id: UUID
    tenant_id: UUID
    origem_id: UUID  # Certificado ou OS que disparou a emissão
    versao: int
    status: InvoiceStatus
    tipo_servico: TipoServico
    perfil_no_evento: PerfilRegulatorio  # snapshot do perfil (ADR-0067 §3)
    valor_centavos: int
    cliente_referencia_hash: str
    provider_invoice_id: str | None  # id no fornecedor (None enquanto não emitido)
    certificado_id: UUID | None
    declaracao_id: UUID | None
    tipo_acreditacao_vinculo: TipoAcreditacaoVinculo | None  # snapshot M8 (INV-FIS-002)
    snapshot_hash: str  # hash versionado canonicalizado (ADR-0029/0064)
    emitido_em: datetime | None
    cancelado_em: datetime | None
    motivo_cancelamento: str | None

    @property
    def valor_decimal(self) -> Decimal:
        """Valor em unidade monetária (centavos → Decimal)."""
        return Decimal(self.valor_centavos) / Decimal(100)

    @property
    def e_terminal(self) -> bool:
        """REJECTED e CANCELED são terminais (D-FIS-3)."""
        return self.status in (InvoiceStatus.REJECTED, InvoiceStatus.CANCELED)
