"""T-CAL-112 — ReclamacoesAbertasQueryService.

Lista reclamacoes em estado RECEBIDA/EM_ANALISE rankadas por proximidade
do prazo CDC art. 26 + AC-CAL-018-3 (15 dias uteis default).

Budget de performance: <= 300ms na implementacao Django (Fase 8).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    ReclamacaoCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import EstadoReclamacao

# Mesmo fator usado em alertar_reclamacao_vencendo (consistencia)
_FATOR_DIA_UTIL_PARA_CORRIDO = 1.40


@dataclass(frozen=True, slots=True)
class ItemReclamacaoAberta:
    """Linha da fila de reclamacoes abertas (ordem por urgencia)."""

    reclamacao_id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    aberta_em: datetime
    estado: EstadoReclamacao
    rt_atribuido_user_id_hash: str  # "" se sem RT
    dias_restantes: int  # negativo se ja vencida
    urgencia: str  # P1_VENCIDA | P2_PROXIMO | NORMAL


def _calcular_dias_restantes(
    snapshot: ReclamacaoCalibracaoSnapshot, agora: datetime
) -> int:
    dias_corridos = round(
        snapshot.prazo_resposta_dia_util * _FATOR_DIA_UTIL_PARA_CORRIDO
    )
    prazo_alvo = snapshot.aberta_em + timedelta(days=dias_corridos)
    delta = prazo_alvo - agora
    if delta.total_seconds() < 0:
        # ja vencida
        return -max(1, (-delta).days)
    return delta.days


def _urgencia(dias_restantes: int) -> str:
    if dias_restantes < 0:
        return "P1_VENCIDA"
    if dias_restantes <= 5:
        return "P2_PROXIMO"
    return "NORMAL"


def executar(
    *,
    reclamacoes: list[ReclamacaoCalibracaoSnapshot],
    agora: datetime,
    tenant_id: UUID | None = None,
) -> list[ItemReclamacaoAberta]:
    """Ranking de reclamacoes abertas por urgencia (mais urgente primeiro).

    Args:
      reclamacoes: snapshots ja carregados; caller pode pre-filtrar
        por tenant.
      agora: timestamp tz-aware.
      tenant_id: filtro adicional opcional (defesa).

    Returns:
      Lista ordenada por dias_restantes crescente (vencidas primeiro).
    """
    if agora.tzinfo is None:
        raise ValueError(
            "reclamacoes_abertas: agora exige datetime tz-aware (INV-VIG-004)"
        )

    itens: list[ItemReclamacaoAberta] = []
    for r in reclamacoes:
        if r.estado not in {
            EstadoReclamacao.RECEBIDA,
            EstadoReclamacao.EM_ANALISE,
        }:
            continue
        if tenant_id is not None and r.tenant_id != tenant_id:
            continue
        dias = _calcular_dias_restantes(r, agora)
        itens.append(
            ItemReclamacaoAberta(
                reclamacao_id=r.id,
                tenant_id=r.tenant_id,
                calibracao_id=r.calibracao_id,
                aberta_em=r.aberta_em,
                estado=r.estado,
                rt_atribuido_user_id_hash=r.rt_atribuido_user_id_hash,
                dias_restantes=dias,
                urgencia=_urgencia(dias),
            )
        )
    # Ordena: mais urgente primeiro (dias_restantes ASCENDENTE; vencidas
    # tem dias < 0, ficam no topo).
    itens.sort(key=lambda x: x.dias_restantes)
    return itens
