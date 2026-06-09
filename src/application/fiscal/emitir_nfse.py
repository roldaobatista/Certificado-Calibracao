"""Use case `emitir_nfse` — US-FIS-001 (T-FIS-030). PURO (ADR-0007).

Fluxo (D-FIS-5): valida compatibilidade perfil × documento metrológico NO USE CASE
(não no DRF — ADR-0073), recebendo o `tipo_acreditacao_vinculo` já snapshotado pelo
M8 (INV-FIS-002 — nunca reconsulta vigência do Tenant) → monta `InvoicePayload` →
chama a porta `FiscalProvider` injetada → persiste `NotaFiscalServico` + snapshot
hash → (stub) `store_xml`. Idempotência de negócio por `(tenant, origem_id, versao)`
(D-FIS-2): se já existe nota para a origem, devolve a existente (não re-emite). O
evento WORM/outbox é publicado pela view (transação do caller).

`ProviderTimeoutError` (transporte — D-FIS-3) PROPAGA: nenhuma nota é persistida; a
view faz `falhar_chave` + 503. `network_timeout` ≠ estado da nota.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import (
    InvoiceStatus,
    PerfilRegulatorio,
    TipoAcreditacaoVinculo,
    TipoServico,
)
from src.domain.fiscal.perfil_documento import (
    documento_metrologico_obrigatorio_por_perfil,
)
from src.domain.fiscal.portas import FiscalProvider
from src.domain.fiscal.repository import NotaFiscalServicoRepository
from src.domain.fiscal.transicoes import snapshot_hash_nfse
from src.domain.fiscal.value_objects import InvoicePayload

VERSAO_NUCLEO = 1


@dataclass(frozen=True, slots=True)
class EmitirNfseInput:
    """Payload de emissão. `perfil` e `tipo_acreditacao_vinculo` vêm server-side
    (perfil via ContextVar; vínculo via snapshot do Certificado M8) — NUNCA do
    payload da request (INV-FIS-001/002)."""

    tenant_id: UUID
    origem_id: UUID
    tipo_servico: TipoServico
    perfil: PerfilRegulatorio
    amount_centavos: int
    issuer_taxid: str
    customer_taxid: str
    customer_name: str
    cliente_referencia_hash: str
    service_description: str
    service_code: str
    issue_date: datetime
    correlation_id: UUID
    certificado_id: UUID | None = None
    declaracao_id: UUID | None = None
    tipo_acreditacao_vinculo: TipoAcreditacaoVinculo | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.issue_date.tzinfo is None:
            raise ValueError("emitir_nfse: issue_date exige datetime tz-aware.")
        if self.amount_centavos <= 0:
            raise ValueError("emitir_nfse: amount_centavos deve ser > 0.")


@dataclass(frozen=True, slots=True)
class EmitirNfseOutput:
    nota: NotaFiscalServico
    ja_existia: bool


def executar(
    inp: EmitirNfseInput,
    *,
    provider: FiscalProvider,
    repo: NotaFiscalServicoRepository,
) -> EmitirNfseOutput:
    """Emite a NFS-e. Idempotente por origem; trava de perfil fail-closed."""
    # Idempotência de negócio (D-FIS-2): origem já tem nota? Devolve a existente.
    existente = repo.obter_por_origem(
        tenant_id=inp.tenant_id, origem_id=inp.origem_id, versao=VERSAO_NUCLEO
    )
    if existente is not None:
        return EmitirNfseOutput(nota=existente, ja_existia=True)

    # Trava metrológica por perfil (D-FIS-5 — fail-closed). Levanta erro de domínio.
    documento_metrologico_obrigatorio_por_perfil(
        perfil=inp.perfil,
        tipo_servico=inp.tipo_servico,
        tipo_acreditacao_certificado=inp.tipo_acreditacao_vinculo,
        tem_declaracao=inp.declaracao_id is not None,
    )

    payload = InvoicePayload(
        tenant_id=inp.tenant_id,
        issuer_taxid=inp.issuer_taxid,
        customer_taxid=inp.customer_taxid,
        customer_name=inp.customer_name,
        service_description=inp.service_description,
        service_code=inp.service_code,
        amount=Decimal(inp.amount_centavos) / Decimal(100),
        issue_date=inp.issue_date,
        metadata=inp.metadata,
    )
    # Pode levantar ProviderTimeoutError (transporte) — propaga, nada persistido.
    resultado = provider.emit_invoice(payload)

    nfse_id = uuid4()
    emitido_em = inp.issue_date if resultado.status is InvoiceStatus.AUTHORIZED else None
    snap_hash = snapshot_hash_nfse(
        tenant_id=str(inp.tenant_id),
        origem_id=str(inp.origem_id),
        versao=VERSAO_NUCLEO,
        tipo_servico=inp.tipo_servico.value,
        perfil_no_evento=inp.perfil.value,
        valor_centavos=inp.amount_centavos,
        cliente_referencia_hash=inp.cliente_referencia_hash,
        provider_invoice_id=resultado.invoice_id,
        certificado_id=str(inp.certificado_id) if inp.certificado_id else None,
        declaracao_id=str(inp.declaracao_id) if inp.declaracao_id else None,
        tipo_acreditacao_vinculo=(
            inp.tipo_acreditacao_vinculo.value if inp.tipo_acreditacao_vinculo else None
        ),
        status=resultado.status.value,
    )
    nota = NotaFiscalServico(
        nfse_id=nfse_id,
        tenant_id=inp.tenant_id,
        origem_id=inp.origem_id,
        versao=VERSAO_NUCLEO,
        status=resultado.status,
        tipo_servico=inp.tipo_servico,
        perfil_no_evento=inp.perfil,
        valor_centavos=inp.amount_centavos,
        cliente_referencia_hash=inp.cliente_referencia_hash,
        provider_invoice_id=resultado.invoice_id,
        certificado_id=inp.certificado_id,
        declaracao_id=inp.declaracao_id,
        tipo_acreditacao_vinculo=inp.tipo_acreditacao_vinculo,
        snapshot_hash=snap_hash,
        emitido_em=emitido_em,
        cancelado_em=None,
        motivo_cancelamento=None,
    )
    repo.salvar_nova(nota)

    # Stub store_xml (B2 diferido — GATE-FIS-B2-XML). Não falha a emissão.
    if resultado.xml_bytes:
        provider.store_xml(resultado.invoice_id, resultado.xml_bytes)

    return EmitirNfseOutput(nota=nota, ja_existia=False)
