"""Porta `metrologia/escopos-cmc` consumida por M4 (calibração) — ADR-0073.

Porta NOVA fail-CLOSED como FUNÇÕES DE MÓDULO sem estado (TL-C-04 — molde
`padroes/query_service.py`, NÃO singleton). O use case de calibração chama
`cobre(...)` na CONFIGURAÇÃO (ADR-0074 cond. 1 — contenção de faixa) e
`cmc_para(...)` na EMISSÃO (cond. 2 — U ≥ CMC). Filtro `tenant_id` EXPLÍCITO
além da RLS (defesa em profundidade — molde M5). Qualquer erro -> fail-CLOSED
(nunca libera emissão RBC por engano).
"""

from __future__ import annotations

import datetime as _dt
import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db.models import Q, QuerySet

from src.domain.metrologia.escopos_cmc import cobertura
from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.escopos_cmc import mappers
from src.infrastructure.metrologia.escopos_cmc.models import EscopoCMC

log = logging.getLogger(__name__)


def _vigentes_confirmados(
    tenant_id: UUID, grandeza_norm: str, data: _dt.datetime
) -> QuerySet[EscopoCMC]:
    """QuerySet de escopos CONFIRMADO + vigentes em `data` para a grandeza.

    Filtro tenant_id EXPLÍCITO (defesa em profundidade além da RLS).
    """
    return EscopoCMC.objects.filter(
        tenant_id=tenant_id,
        grandeza=grandeza_norm,
        estado=EstadoEscopo.CONFIRMADO.value,
        revogado_em__isnull=True,
        vigencia_inicio__lte=data,
    ).filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=data))


def cobre(
    *,
    tenant_id: UUID,
    grandeza: str,
    faixa_min: Decimal | str,
    faixa_max: Decimal | str,
    unidade: str,
    data: _dt.datetime,
) -> tuple[bool, str]:
    """(True, '') se ≥1 escopo CONFIRMADO vigente em `data` CONTÉM a faixa
    solicitada (contenção total — ADR-0074 cond. 1 / INV-ECMC-005). Senão
    (False, reason). Fail-CLOSED: qualquer erro -> (False, 'erro_interno').

    `reason` estável: '' | 'cmc_fora_do_escopo' | 'erro_interno'.
    """
    try:
        grandeza_norm = Grandeza.from_string(grandeza).value
        solicitada = FaixaMedicao(Decimal(faixa_min), Decimal(faixa_max), unidade)
        for m in _vigentes_confirmados(tenant_id, grandeza_norm, data):
            esc_faixa = FaixaMedicao(m.faixa_min, m.faixa_max, m.unidade)
            if cobertura.faixa_contida(solicitada=solicitada, escopo=esc_faixa):
                return True, cobertura.REASON_OK
        return False, cobertura.REASON_FORA_DO_ESCOPO
    except (ValueError, InvalidOperation, TypeError) as e:
        # entrada inválida (grandeza/unidade/faixa fora do contrato) -> fail-closed
        log.warning("escopos_cmc.cobre entrada invalida: %s", e)
        return False, "erro_interno"
    except Exception:
        log.exception("escopos_cmc.cobre erro inesperado — fail-closed")
        return False, "erro_interno"


def cmc_para(
    *,
    tenant_id: UUID,
    grandeza: str,
    ponto: Decimal | str,
    data: _dt.datetime,
) -> Decimal | None:
    """Menor CMC vigente NO PONTO entre os escopos CONFIRMADOS que o contêm
    (RBC-NC-03 / NIT-DICLA-012). None se nenhum cobre. Usada na EMISSÃO para
    `U ≥ CMC` (ADR-0074 cond. 2 / INV-ECMC-009). Fail-safe: erro -> None
    (caller trata None como 'sem cobertura' = bloqueia emissão RBC).
    """
    try:
        grandeza_norm = Grandeza.from_string(grandeza).value
        ponto_d = Decimal(ponto)
        qs = _vigentes_confirmados(tenant_id, grandeza_norm, data).filter(
            faixa_min__lte=ponto_d, faixa_max__gte=ponto_d
        )
        escopos = [mappers.model_para_snapshot(m) for m in qs]
        return cobertura.menor_cmc_por_faixa(escopos, ponto=ponto_d)
    except (ValueError, InvalidOperation, TypeError) as e:
        log.warning("escopos_cmc.cmc_para entrada invalida: %s", e)
        return None
    except Exception:
        log.exception("escopos_cmc.cmc_para erro inesperado — fail-safe None")
        return None
