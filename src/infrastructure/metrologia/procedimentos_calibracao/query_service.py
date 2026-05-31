"""Porta `metrologia/procedimentos-calibracao` consumida por M4 (calibração) — ADR-0073.

Porta NOVA fail-CLOSED como FUNÇÃO DE MÓDULO sem estado (C-3 / TL-C-04 — molde
`escopos_cmc/query_service.py`, NÃO singleton). O use case de calibração chama
`vigente_em(...)` na CONFIGURAÇÃO (cl. 7.2.1): existe procedimento técnico
documentado PUBLICADO vigente que cobre a grandeza+faixa? Filtro `tenant_id`
EXPLÍCITO além da RLS (defesa em profundidade — molde M6). Qualquer erro ->
fail-CLOSED (None; nunca libera emissão RBC por engano).

Erro de domínio DISTINTO do escopo (RBC item 4): aqui o None vira 412
`ProcedimentoVigenteAusente` (lacuna de método cl. 7.2.1), NÃO `EscopoNaoCobreFaixa`.
"""

from __future__ import annotations

import datetime as _dt
import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db.models import Q, QuerySet

from src.domain.metrologia.faixa_cobertura import faixa_contida
from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import EstadoProcedimento
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.procedimentos_calibracao import mappers
from src.infrastructure.metrologia.procedimentos_calibracao.models import (
    ProcedimentoCalibracao,
)

log = logging.getLogger(__name__)


def _vigentes_publicados(
    tenant_id: UUID, grandeza_norm: str, data: _dt.datetime
) -> QuerySet[ProcedimentoCalibracao]:
    """QuerySet de procedimentos PUBLICADO + vigentes em `data` para a grandeza.

    Filtro tenant_id EXPLÍCITO (defesa em profundidade além da RLS).
    """
    return ProcedimentoCalibracao.objects.filter(
        tenant_id=tenant_id,
        grandeza=grandeza_norm,
        estado=EstadoProcedimento.PUBLICADO.value,
        revogado_em__isnull=True,
        vigencia_inicio__lte=data,
    ).filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=data))


def vigente_em(
    *,
    tenant_id: UUID,
    grandeza: str,
    faixa_min: Decimal | str,
    faixa_max: Decimal | str,
    unidade: str,
    data: _dt.datetime,
) -> ProcedimentoSnapshot | None:
    """Procedimento PUBLICADO vigente em `data` que CONTÉM a faixa solicitada
    (contenção total — INV-PROC-001 / geometria compartilhada). None se nenhum.

    Fail-CLOSED: qualquer erro -> None (caller bloqueia emissão RBC via 412
    `ProcedimentoVigenteAusente`). Retorna o SNAPSHOT (a Fatia 3 preenche o
    `procedimento_versao_snapshot` da calibração com ele).
    """
    try:
        grandeza_norm = Grandeza.from_string(grandeza).value
        solicitada = FaixaMedicao(Decimal(faixa_min), Decimal(faixa_max), unidade)
        for m in _vigentes_publicados(tenant_id, grandeza_norm, data):
            proc_faixa = FaixaMedicao(m.faixa_min, m.faixa_max, m.unidade)
            if faixa_contida(solicitada=solicitada, escopo=proc_faixa):
                return mappers.model_para_snapshot(m)
        return None
    except (ValueError, InvalidOperation, TypeError) as e:
        # entrada inválida (grandeza/unidade/faixa fora do contrato) -> fail-closed
        log.warning("procedimentos.vigente_em entrada invalida: %s", e)
        return None
    except Exception:
        log.exception("procedimentos.vigente_em erro inesperado — fail-closed")
        return None


def cobre_procedimento(
    *,
    tenant_id: UUID,
    grandeza: str,
    faixa_min: Decimal | str,
    faixa_max: Decimal | str,
    unidade: str,
    data: _dt.datetime,
) -> tuple[bool, dict[str, str] | None]:
    """Adapter da porta `CoberturaProcedimentoPort` (M4 `configurar_calibracao` —
    ADR-0073 / T-PROC-040). Resolve o procedimento vigente via `vigente_em` e
    devolve `(True, {procedimento_id, codigo, versao, numero_revisao, hash_anexo})`
    para o use case preencher o snapshot real; `(False, None)` se nenhum cobre
    (RBC -> 412). `numero_revisao` (cl. 8.3.2c) é distinto de `versao` (T-PROC-042).
    Fail-CLOSED (qualquer erro já vira None em `vigente_em` -> (False, None))."""
    snap = vigente_em(
        tenant_id=tenant_id,
        grandeza=grandeza,
        faixa_min=faixa_min,
        faixa_max=faixa_max,
        unidade=unidade,
        data=data,
    )
    if snap is None:
        return False, None
    return True, {
        "procedimento_id": str(snap.id),
        "codigo": snap.codigo,
        "versao": str(snap.versao),
        "numero_revisao": snap.numero_revisao,
        "hash_anexo": snap.anexo_pdf_sha256,
    }
