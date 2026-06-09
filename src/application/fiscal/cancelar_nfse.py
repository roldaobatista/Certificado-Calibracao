"""Use case `cancelar_nfse` — US-FIS-003 (T-FIS-031). PURO (ADR-0007).

Cancela NFS-e AUTHORIZED dentro da janela de 24h, motivo ≥30ch (AC-FIS-003).
Transição AUTHORIZED→CANCELED (D-FIS-4) — registrada como nova transição + evento
append-only (publicado pela view). O advisory lock da view + o trigger one-shot
`cancelado_em` garantem que não cancela duas vezes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import InvoiceStatus
from src.domain.fiscal.portas import FiscalProvider
from src.domain.fiscal.repository import NotaFiscalServicoRepository
from src.domain.fiscal.transicoes import validar_motivo_cancelamento, validar_transicao

JANELA_CANCELAMENTO = timedelta(hours=24)


class NotaNaoEncontradaError(Exception):
    """NFS-e inexistente para (tenant, nfse_id) — 404."""

    reason = "NFSE_NAO_ENCONTRADA"


class PrazoCancelamentoExpiradoError(Exception):
    """Cancelamento > 24h da emissão (AC-FIS-003-2) — 422. Use ajuste extemporâneo
    (US-FIS-010, diferido)."""

    reason = "PRAZO_EXPIRADO"


@dataclass(frozen=True, slots=True)
class CancelarNfseInput:
    tenant_id: UUID
    nfse_id: UUID
    motivo: str
    agora: datetime

    def __post_init__(self) -> None:
        if self.agora.tzinfo is None:
            raise ValueError("cancelar_nfse: agora exige datetime tz-aware.")


def executar(
    inp: CancelarNfseInput,
    *,
    provider: FiscalProvider,
    repo: NotaFiscalServicoRepository,
) -> NotaFiscalServico:
    nota = repo.obter_por_id(tenant_id=inp.tenant_id, nfse_id=inp.nfse_id)
    if nota is None:
        raise NotaNaoEncontradaError(str(inp.nfse_id))

    validar_motivo_cancelamento(inp.motivo)
    # Transição válida só a partir de AUTHORIZED (D-FIS-3).
    validar_transicao(nota.status, InvoiceStatus.CANCELED)

    # Janela de 24h a partir da emissão (AC-FIS-003-2).
    if nota.emitido_em is not None and (inp.agora - nota.emitido_em) > JANELA_CANCELAMENTO:
        raise PrazoCancelamentoExpiradoError(str(inp.nfse_id))

    provider.cancel_invoice(nota.provider_invoice_id or "", inp.motivo)

    cancelada = replace(
        nota,
        status=InvoiceStatus.CANCELED,
        cancelado_em=inp.agora,
        motivo_cancelamento=inp.motivo,
    )
    repo.atualizar_status(tenant_id=inp.tenant_id, nfse_id=inp.nfse_id, nota=cancelada)
    return cancelada
