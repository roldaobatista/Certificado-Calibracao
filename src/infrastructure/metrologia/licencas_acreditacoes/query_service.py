"""Read-path / porta de cobertura do M9 licencas-acreditacoes (T-LIC-021).

`vigente_para_rbc(tenant_id, data)` é a API INTERNA do M9 (não consumida pelo M8
nesta frente — D-LIC-1/ADR-0079: o M8 lê o CACHE `Tenant.acreditacao_vigencia_fim`,
populado via `aplicar_evento_cgcre`). A porta existe para o hard-block de emissão
(GATE-LIC-EMISSAO-HARDBLOCK — Wave B) e para o teste de não-drift `cache == fonte`
(Fatia 3 / GATE-LIC-DRIFT). Fail-CLOSED: sem acreditação CGCRE vigente → `False`.

Defesa em profundidade (molde M5-M8): `tenant_id` EXPLÍCITO além da RLS.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.metrologia.licencas_acreditacoes.enums import TipoDocumentoRegulatorio
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    DocumentoRegulatorio as DocumentoRegulatorioModel,
)


def vigente_para_rbc(*, tenant_id: UUID, data: date) -> bool:
    """`True` se existe acreditação CGCRE NÃO-revogada cobrindo `data`
    (`vigencia_inicio <= data <= vigencia_fim`). Fail-closed: ausência/vencimento →
    `False` (o caller — M8 via cache, ou hard-block — rebaixa/bloqueia)."""
    return DocumentoRegulatorioModel.objects.filter(
        tenant_id=tenant_id,
        tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE.value,
        revogado_em__isnull=True,
        vigencia_inicio__lte=data,
        vigencia_fim__gte=data,
    ).exists()


def vigencia_fim_acreditacao_cgcre(*, tenant_id: UUID) -> date | None:
    """Maior `vigencia_fim` entre as acreditações CGCRE não-revogadas do tenant
    (fonte rica — base do teste de não-drift `cache == fonte`, Fatia 3). `None` se
    não há acreditação CGCRE cadastrada."""
    return (
        DocumentoRegulatorioModel.objects.filter(
            tenant_id=tenant_id,
            tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE.value,
            revogado_em__isnull=True,
        )
        .order_by("-vigencia_fim")
        .values_list("vigencia_fim", flat=True)
        .first()
    )
