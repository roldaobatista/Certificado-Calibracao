"""Use case `consultar_status_nfse` — US-FIS-001 consulta (T-FIS-031). PURO.

Resolve notas que ficaram PENDING: consulta a porta `FiscalProvider.query_status` e
aplica a transição PENDING→AUTHORIZED|REJECTED (D-FIS-3 — único caminho que resolve
o PENDING). Em estados terminais é no-op idempotente (devolve a nota como está).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import InvoiceStatus
from src.domain.fiscal.portas import FiscalProvider
from src.domain.fiscal.repository import NotaFiscalServicoRepository
from src.domain.fiscal.transicoes import validar_transicao

from .cancelar_nfse import NotaNaoEncontradaError


@dataclass(frozen=True, slots=True)
class ConsultarStatusInput:
    tenant_id: UUID
    nfse_id: UUID
    agora: datetime

    def __post_init__(self) -> None:
        if self.agora.tzinfo is None:
            raise ValueError("consultar_status_nfse: agora exige datetime tz-aware.")


def executar(
    inp: ConsultarStatusInput,
    *,
    provider: FiscalProvider,
    repo: NotaFiscalServicoRepository,
) -> NotaFiscalServico:
    nota = repo.obter_por_id(tenant_id=inp.tenant_id, nfse_id=inp.nfse_id)
    if nota is None:
        raise NotaNaoEncontradaError(str(inp.nfse_id))

    # Só PENDING consulta o provider; terminal = no-op idempotente.
    if nota.status is not InvoiceStatus.PENDING:
        return nota

    novo_status = provider.query_status(nota.provider_invoice_id or "")
    if novo_status is InvoiceStatus.PENDING:
        return nota  # ainda pendente — sem transição

    validar_transicao(nota.status, novo_status)
    emitido_em = inp.agora if novo_status is InvoiceStatus.AUTHORIZED else nota.emitido_em
    resolvida = replace(nota, status=novo_status, emitido_em=emitido_em)
    repo.atualizar_status(tenant_id=inp.tenant_id, nfse_id=inp.nfse_id, nota=resolvida)
    return resolvida
