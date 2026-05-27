"""T-CAL-111 — SubcontratacaoStatusQueryService.

Painel de subcontratacao (cl. 6.6 + INV-CAL-SUBC-001..006):

- Lista laboratorios subcontratados ativos.
- Marca avaliacoes periodicas (P-CAL-R5) vencendo nos proximos 30d
  e ja vencidas.

Budget de performance: <= 300ms na implementacao Django (Fase 8).

`LaboratorioSubcontratado` ainda nao tem snapshot canonico em entities.py
(use case `subcontratar` US-CAL-017 entregue em Fase 5 Batch posterior);
declaramos dataclass local.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    AvaliacaoPeriodicaSubcontratadoSnapshot,
)


@dataclass(frozen=True, slots=True)
class LaboratorioSubcontratadoSnapshot:
    """Snapshot enxuto pra painel de status (cl. 6.6 + INV-CAL-SUBC-005)."""

    id: UUID
    tenant_id: UUID
    nome_legal: str
    pais: str  # "BR" / "US" / ...
    score_avaliacao_atual: Decimal | None  # 0-10
    proxima_avaliacao_periodica_em: datetime | None
    vigencia_inicio: datetime
    vigencia_fim: datetime | None  # None => contrato ativo
    deletado_em: datetime | None  # Padrao C ADR-0031 soft-delete


@dataclass(frozen=True, slots=True)
class ItemSubcontratacaoStatus:
    """Linha do painel de subcontratacao."""

    laboratorio_id: UUID
    tenant_id: UUID
    nome_legal: str
    pais: str
    score_avaliacao_atual: Decimal | None
    proxima_avaliacao_em: datetime | None
    dias_ate_avaliacao: int | None  # negativo => vencida
    status_avaliacao: str  # 'VENCIDA' | 'PROXIMA_30D' | 'OK' | 'SEM_AVALIACAO'
    qtde_avaliacoes_historico: int


def _classificar_avaliacao(
    *, proxima_em: datetime | None, agora: datetime, alerta_dias: int = 30
) -> tuple[int | None, str]:
    if proxima_em is None:
        return None, "SEM_AVALIACAO"
    delta = proxima_em - agora
    dias = delta.days  # int truncado (negativo se ja vencida)
    if delta.total_seconds() < 0:
        return dias, "VENCIDA"
    if dias <= alerta_dias:
        return dias, "PROXIMA_30D"
    return dias, "OK"


def executar(
    *,
    laboratorios: list[LaboratorioSubcontratadoSnapshot],
    avaliacoes: list[AvaliacaoPeriodicaSubcontratadoSnapshot] | None = None,
    agora: datetime,
    tenant_id: UUID | None = None,
    pais: str | None = None,
    incluir_inativos: bool = False,
    alerta_dias: int = 30,
) -> list[ItemSubcontratacaoStatus]:
    """Status de cada laboratorio + alerta avaliacao periodica.

    Args:
      laboratorios: snapshots de laboratorios.
      avaliacoes: snapshots de avaliacoes (1:N) — opcional, usado pra contar
        historico por laboratorio.
      agora: datetime tz-aware (data de referencia).
      tenant_id: filtro defensivo.
      pais: codigo ISO; None => qualquer.
      incluir_inativos: True => inclui contratos vencidos + soft-deleted.
      alerta_dias: limiar PROXIMA_30D (default 30).

    Returns:
      Lista ordenada por status_avaliacao (VENCIDA < PROXIMA_30D < OK <
      SEM_AVALIACAO) e depois por dias_ate_avaliacao ASC.
    """
    if agora.tzinfo is None:
        raise ValueError("subcontratacao: agora exige datetime tz-aware (INV-VIG-004)")
    if alerta_dias < 0:
        raise ValueError("subcontratacao: alerta_dias deve ser >= 0")

    avaliacoes = avaliacoes or []

    # Conta historico por laboratorio (tenant-aware)
    historico_por_lab: dict[UUID, int] = {}
    for av in avaliacoes:
        if tenant_id is not None and av.tenant_id != tenant_id:
            continue
        historico_por_lab[av.laboratorio_id] = (
            historico_por_lab.get(av.laboratorio_id, 0) + 1
        )

    itens: list[ItemSubcontratacaoStatus] = []
    pais_norm = pais.upper().strip() if pais else None
    for lab in laboratorios:
        if tenant_id is not None and lab.tenant_id != tenant_id:
            continue
        if pais_norm is not None and lab.pais.upper() != pais_norm:
            continue
        if not incluir_inativos:
            if lab.deletado_em is not None:
                continue
            if lab.vigencia_fim is not None and lab.vigencia_fim < agora:
                continue

        dias, status = _classificar_avaliacao(
            proxima_em=lab.proxima_avaliacao_periodica_em,
            agora=agora,
            alerta_dias=alerta_dias,
        )

        itens.append(
            ItemSubcontratacaoStatus(
                laboratorio_id=lab.id,
                tenant_id=lab.tenant_id,
                nome_legal=lab.nome_legal,
                pais=lab.pais,
                score_avaliacao_atual=lab.score_avaliacao_atual,
                proxima_avaliacao_em=lab.proxima_avaliacao_periodica_em,
                dias_ate_avaliacao=dias,
                status_avaliacao=status,
                qtde_avaliacoes_historico=historico_por_lab.get(lab.id, 0),
            )
        )

    _STATUS_ORDEM = {
        "VENCIDA": 0,
        "PROXIMA_30D": 1,
        "OK": 2,
        "SEM_AVALIACAO": 3,
    }
    itens.sort(
        key=lambda x: (
            _STATUS_ORDEM[x.status_avaliacao],
            x.dias_ate_avaliacao if x.dias_ate_avaliacao is not None else 999999,
        )
    )
    return itens


__all__ = [
    "ItemSubcontratacaoStatus",
    "LaboratorioSubcontratadoSnapshot",
    "executar",
]
