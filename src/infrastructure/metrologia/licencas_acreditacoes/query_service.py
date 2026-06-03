"""Read-path / porta de cobertura do M9 licencas-acreditacoes (T-LIC-021).

`vigente_para_rbc(tenant_id, data)` é a API INTERNA do M9 (não consumida pelo M8
nesta frente — D-LIC-1/ADR-0079: o M8 lê o CACHE `Tenant.acreditacao_vigencia_fim`,
populado via `aplicar_evento_cgcre`). A porta existe para o hard-block de emissão
(GATE-LIC-EMISSAO-HARDBLOCK — Wave B) e para o teste de não-drift `cache == fonte`
(Fatia 3 / GATE-LIC-DRIFT). Fail-CLOSED: sem acreditação CGCRE vigente → `False`.

Defesa em profundidade (molde M5-M8): `tenant_id` EXPLÍCITO além da RLS.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from src.application.metrologia.licencas_acreditacoes.jobs.verificar_alertas_licencas import (
    DocumentoAlertaSnapshot,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    JANELAS_ALERTA_DIAS,
    TipoDocumentoRegulatorio,
)
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


def listar_documentos_para_alerta(
    *, tenant_id: UUID, agora: date, janela_maxima_dias: int = max(JANELAS_ALERTA_DIAS)
) -> list[DocumentoAlertaSnapshot]:
    """Snapshots dos documentos NÃO-revogados do tenant cuja `vigencia_fim` cai dentro
    da maior janela de alerta (`agora + janela_maxima_dias`) — inclui já vencidos
    (alerta crítico). Consumido pelo job `verificar_alertas_licencas` (T-LIC-051)."""
    limite = agora + timedelta(days=janela_maxima_dias)
    qs = DocumentoRegulatorioModel.objects.filter(
        tenant_id=tenant_id,
        revogado_em__isnull=True,
        vigencia_fim__lte=limite,
    ).values_list("id", "vigencia_fim", "responsavel_id")
    return [
        DocumentoAlertaSnapshot(
            documento_id=doc_id,
            tenant_id=tenant_id,
            vigencia_fim=vig_fim,
            revogado=False,
            responsavel_id=resp_id,
        )
        for doc_id, vig_fim, resp_id in qs
    ]


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
