"""Mappers model PG <-> snapshot de domínio (M7 — ADR-0007).

Colunas TIPADAS (molde M6): mapeamento campo-a-campo. `faixa_min/max/unidade`
reconstroem o VO `FaixaMedicao`; `grandeza`/`tipo_metodo`/`estado` reconstroem os
enums. O use case nunca conhece Django — só o `ProcedimentoSnapshot`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

if TYPE_CHECKING:
    from src.infrastructure.metrologia.procedimentos_calibracao.models import (
        ProcedimentoCalibracao,
    )


def model_para_snapshot(m: ProcedimentoCalibracao) -> ProcedimentoSnapshot:
    """Model PG -> snapshot de domínio (leitura)."""
    return ProcedimentoSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        codigo=m.codigo,
        titulo=m.titulo,
        grandeza=Grandeza.from_string(m.grandeza),
        faixa=FaixaMedicao(m.faixa_min, m.faixa_max, m.unidade),
        metodo_norma=m.metodo_norma,
        tipo_metodo=TipoMetodo(m.tipo_metodo),
        registro_validacao_id=m.registro_validacao_id,
        numero_revisao=m.numero_revisao,
        aprovado_em=m.aprovado_em,
        aprovado_por_id=m.aprovado_por_id,
        aprovado_por_nome_snapshot=m.aprovado_por_nome_snapshot,
        anexo_pdf_storage_key=m.anexo_pdf_storage_key,
        anexo_pdf_sha256=m.anexo_pdf_sha256,
        versao=m.versao,
        vigente_a_partir=m.vigente_a_partir,
        estado=EstadoProcedimento(m.estado),
        revision=m.revision,
        vigencia_inicio=m.vigencia_inicio,
        vigencia_fim=m.vigencia_fim,
        correlation_id=m.correlation_id,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao,
    )


def snapshot_para_campos(s: ProcedimentoSnapshot) -> dict[str, Any]:
    """Snapshot -> kwargs do Model (escrita). `id`/`tenant_id` vão por fora."""
    return {
        "codigo": s.codigo,
        "titulo": s.titulo,
        "grandeza": s.grandeza.value,
        "faixa_min": s.faixa.inferior,
        "faixa_max": s.faixa.superior,
        "unidade": s.faixa.unidade,
        "metodo_norma": s.metodo_norma,
        "tipo_metodo": s.tipo_metodo.value,
        "registro_validacao_id": s.registro_validacao_id,
        "numero_revisao": s.numero_revisao,
        "aprovado_em": s.aprovado_em,
        "aprovado_por_id": s.aprovado_por_id,
        "aprovado_por_nome_snapshot": s.aprovado_por_nome_snapshot,
        "anexo_pdf_storage_key": s.anexo_pdf_storage_key,
        "anexo_pdf_sha256": s.anexo_pdf_sha256,
        "versao": s.versao,
        "vigente_a_partir": s.vigente_a_partir,
        "estado": s.estado.value,
        "revision": s.revision,
        "vigencia_inicio": s.vigencia_inicio,
        "vigencia_fim": s.vigencia_fim,
        "correlation_id": s.correlation_id,
        "revogado_em": s.revogado_em,
        "motivo_revogacao": s.motivo_revogacao,
    }
