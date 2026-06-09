"""Mapper model PG ↔ entidade de domínio fiscal (Fatia 1b, T-FIS-022 — ADR-0007).

Colunas tipadas → mapeamento campo-a-campo. O use case nunca conhece Django — só
a entidade `NotaFiscalServico` do domínio. Enums reconstruídos a partir do `.value`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import (
    InvoiceStatus,
    PerfilRegulatorio,
    TipoAcreditacaoVinculo,
    TipoServico,
)

if TYPE_CHECKING:
    from src.infrastructure.fiscal.models import NotaFiscalServico as NotaFiscalServicoModel


def _vinculo(valor: str) -> TipoAcreditacaoVinculo | None:
    return TipoAcreditacaoVinculo(valor) if valor else None


def model_para_entidade(m: NotaFiscalServicoModel) -> NotaFiscalServico:
    """Model PG → entidade de domínio (leitura)."""
    return NotaFiscalServico(
        nfse_id=m.id,
        tenant_id=m.tenant_id,
        origem_id=m.origem_id,
        versao=m.versao,
        status=InvoiceStatus(m.status),
        tipo_servico=TipoServico(m.tipo_servico),
        perfil_no_evento=PerfilRegulatorio(m.perfil_no_evento),
        valor_centavos=m.valor_centavos,
        cliente_referencia_hash=m.cliente_referencia_hash,
        provider_invoice_id=m.provider_invoice_id or None,
        certificado_id=m.certificado_id,
        declaracao_id=m.declaracao_id,
        tipo_acreditacao_vinculo=_vinculo(m.tipo_acreditacao_vinculo),
        snapshot_hash=m.snapshot_hash,
        emitido_em=m.emitido_em,
        cancelado_em=m.cancelado_em,
        motivo_cancelamento=m.motivo_cancelamento or None,
    )


def entidade_para_campos(e: NotaFiscalServico) -> dict[str, Any]:
    """Entidade → kwargs do Model (escrita). `id`/`tenant_id` vão por fora."""
    return {
        "origem_id": e.origem_id,
        "versao": e.versao,
        "status": e.status.value,
        "tipo_servico": e.tipo_servico.value,
        "perfil_no_evento": e.perfil_no_evento.value,
        "valor_centavos": e.valor_centavos,
        "cliente_referencia_hash": e.cliente_referencia_hash,
        "provider_invoice_id": e.provider_invoice_id or "",
        "certificado_id": e.certificado_id,
        "declaracao_id": e.declaracao_id,
        "tipo_acreditacao_vinculo": (
            e.tipo_acreditacao_vinculo.value if e.tipo_acreditacao_vinculo else ""
        ),
        "snapshot_hash": e.snapshot_hash,
        "emitido_em": e.emitido_em,
        "cancelado_em": e.cancelado_em,
        "motivo_cancelamento": e.motivo_cancelamento or "",
    }
