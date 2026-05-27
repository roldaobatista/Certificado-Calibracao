"""T-CAL-109 — EscopoCMCQueryService.

Filtra Escopos CMC (NIT-DICLA-021 + INV-CAL-CMC-001) por grandeza
+ faixa de medicao. Caller carrega dimensoes do escopo via Django.

Budget de performance: <= 200ms na implementacao Django (Fase 8).

Como `Escopo` ainda nao tem snapshot canonico em entities.py
(use case `gerenciarEscopoCMC` US-CAL-015 nao foi implementado
no Batch C/D), declaramos dataclass local. Migra pra entities.py
quando o use case nascer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EscopoCMCSnapshot:
    """Snapshot enxuto de Escopo CMC para filtro de leitura."""

    id: UUID
    tenant_id: UUID
    grandeza: str  # "massa", "comprimento", "temperatura", ...
    faixa_min: Decimal
    faixa_max: Decimal
    unidade: str
    cmc_valor: Decimal  # incerteza minima alcancavel (CMC)
    cmc_unidade: str
    procedimento_id: UUID | None
    rbc_acreditado: bool  # true => requer match estrito
    vigencia_inicio: datetime  # JanelaVigencia (ADR-0030)
    vigencia_fim: datetime | None  # None => aberta


@dataclass(frozen=True, slots=True)
class ItemEscopoCMC:
    """Linha do resultado da consulta (sem campos auditoria)."""

    escopo_id: UUID
    tenant_id: UUID
    grandeza: str
    faixa_min: Decimal
    faixa_max: Decimal
    unidade: str
    cmc_valor: Decimal
    cmc_unidade: str
    rbc_acreditado: bool


def _faixa_intersecta(
    *,
    escopo_min: Decimal,
    escopo_max: Decimal,
    consulta_min: Decimal | None,
    consulta_max: Decimal | None,
) -> bool:
    """True se faixa de consulta interseca faixa do escopo.

    Sem limites na consulta => sempre intersecta. Limites parciais
    aplicam-se um lado de cada vez.
    """
    if consulta_min is not None and consulta_min > escopo_max:
        return False
    if consulta_max is not None and consulta_max < escopo_min:
        return False
    return True


def _esta_vigente(escopo: EscopoCMCSnapshot, em: datetime) -> bool:
    if em < escopo.vigencia_inicio:
        return False
    if escopo.vigencia_fim is not None and em > escopo.vigencia_fim:
        return False
    return True


def executar(
    *,
    escopos: list[EscopoCMCSnapshot],
    em: datetime,
    grandeza: str | None = None,
    faixa_min: Decimal | None = None,
    faixa_max: Decimal | None = None,
    apenas_rbc: bool = False,
    tenant_id: UUID | None = None,
) -> list[ItemEscopoCMC]:
    """Filtra escopos por (grandeza, faixa, RBC, vigencia em `em`).

    Args:
      escopos: snapshots ja carregados (caller pode pre-filtrar).
      em: datetime tz-aware (data de referencia para vigencia).
      grandeza: caso-insensitivo. None => qualquer.
      faixa_min, faixa_max: limites da consulta (intersecta com escopo).
      apenas_rbc: True => somente acreditados pela CGCRE.
      tenant_id: filtro adicional defensivo.

    Returns:
      Lista ordenada por (grandeza ASC, faixa_min ASC).
    """
    if em.tzinfo is None:
        raise ValueError("escopo: em exige datetime tz-aware (INV-VIG-004)")

    grandeza_norm = grandeza.lower().strip() if grandeza else None

    filtrados = [
        e
        for e in escopos
        if (tenant_id is None or e.tenant_id == tenant_id)
        and _esta_vigente(e, em)
        and (grandeza_norm is None or e.grandeza.lower() == grandeza_norm)
        and (not apenas_rbc or e.rbc_acreditado)
        and _faixa_intersecta(
            escopo_min=e.faixa_min,
            escopo_max=e.faixa_max,
            consulta_min=faixa_min,
            consulta_max=faixa_max,
        )
    ]
    filtrados.sort(key=lambda e: (e.grandeza.lower(), e.faixa_min))

    return [
        ItemEscopoCMC(
            escopo_id=e.id,
            tenant_id=e.tenant_id,
            grandeza=e.grandeza,
            faixa_min=e.faixa_min,
            faixa_max=e.faixa_max,
            unidade=e.unidade,
            cmc_valor=e.cmc_valor,
            cmc_unidade=e.cmc_unidade,
            rbc_acreditado=e.rbc_acreditado,
        )
        for e in filtrados
    ]
