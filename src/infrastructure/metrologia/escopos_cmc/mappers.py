"""Mappers model PG <-> snapshot de domínio (M6 — ADR-0007).

Diferente do M5 (VOs em JSONField), aqui as colunas são TIPADAS (D-ECMC-2), então
o mapeamento é campo-a-campo. `faixa_min/max/unidade` reconstroem o VO
`FaixaMedicao`; `grandeza`/`cmc_forma`/`estado`/`origem` reconstroem os enums. O
use case nunca conhece Django — só o `EscopoCMCSnapshot`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import (
    EstadoEscopo,
    FormaCMC,
    OrigemEscopo,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

if TYPE_CHECKING:
    from src.infrastructure.metrologia.escopos_cmc.models import EscopoCMC


def model_para_snapshot(m: EscopoCMC) -> EscopoCMCSnapshot:
    """Model PG -> snapshot de domínio (leitura)."""
    return EscopoCMCSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        grandeza=Grandeza.from_string(m.grandeza),
        faixa=FaixaMedicao(m.faixa_min, m.faixa_max, m.unidade),
        cmc_forma=FormaCMC(m.cmc_forma),
        cmc_valor=m.cmc_valor,
        cmc_unidade=m.cmc_unidade,
        cmc_coef_relativo=m.cmc_coef_relativo,
        rbc_acreditado=m.rbc_acreditado,
        numero_escopo_cgcre=m.numero_escopo_cgcre,
        procedimento_id=m.procedimento_id,
        documento_regulatorio_id=m.documento_regulatorio_id,
        versao=m.versao,
        vigente_a_partir=m.vigente_a_partir,
        estado=EstadoEscopo(m.estado),
        origem=OrigemEscopo(m.origem),
        revision=m.revision,
        vigencia_inicio=m.vigencia_inicio,
        vigencia_fim=m.vigencia_fim,
        correlation_id=m.correlation_id,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao,
    )


def snapshot_para_campos(s: EscopoCMCSnapshot) -> dict[str, Any]:
    """Snapshot -> kwargs do Model (escrita). `id`/`tenant_id` vão por fora."""
    return {
        "grandeza": s.grandeza.value,
        "faixa_min": s.faixa.inferior,
        "faixa_max": s.faixa.superior,
        "unidade": s.faixa.unidade,
        "cmc_forma": s.cmc_forma.value,
        "cmc_valor": s.cmc_valor,
        "cmc_unidade": s.cmc_unidade,
        "cmc_coef_relativo": s.cmc_coef_relativo,
        "rbc_acreditado": s.rbc_acreditado,
        "numero_escopo_cgcre": s.numero_escopo_cgcre,
        "procedimento_id": s.procedimento_id,
        "documento_regulatorio_id": s.documento_regulatorio_id,
        "versao": s.versao,
        "vigente_a_partir": s.vigente_a_partir,
        "estado": s.estado.value,
        "origem": s.origem.value,
        "revision": s.revision,
        "vigencia_inicio": s.vigencia_inicio,
        "vigencia_fim": s.vigencia_fim,
        "correlation_id": s.correlation_id,
        "revogado_em": s.revogado_em,
        "motivo_revogacao": s.motivo_revogacao,
    }
