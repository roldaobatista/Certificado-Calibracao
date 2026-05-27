"""Job `verificar_avaliacoes_subcontratados_vencendo` (T-CAL-115).

ISO 17025 cl. 6.6.2 + P-CAL-R5 RBC — laboratorio subcontratado deve ser
avaliado periodicamente (anualmente padrao). Quando `proxima_avaliacao_em`
se aproxima (30 dias antes), o sistema gera alerta P2 (gerente qualidade).
Apos vencido (proxima_avaliacao_em < agora), gera alerta P1 (subcontratado
NAO pode receber novas atribuicoes ate avaliacao).

INV-CAL-SUBC-005: usar subcontratado com avaliacao vencida = fraude
regulatoria. O subcontratar_calibracao use case eh quem bloqueia em runtime;
este job antecipa o problema 30d antes pra dar tempo de agendar.

Funcao PURA — recebe lista de "avaliacao mais recente" por
LaboratorioSubcontratado (caller faz a query agregada
`DISTINCT ON (laboratorio_id) ORDER BY avaliado_em DESC`).

Severidade:
  P2_ALERTA — 0 < dias_restantes <= 30 (vence em ate 30 dias).
  P1_VENCIDA — dias_restantes < 0 (ja vencida).
  NONE — dias_restantes > 30 (normal).

Idempotente: chamadas multiplas no mesmo dia retornam alertas
identicos. Caller deduplica via correlation_id da avaliacao.

Frequencia recomendada (Wave A): semanal (e.g. domingo 03:00 BRT).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    AvaliacaoPeriodicaSubcontratadoSnapshot,
)
from src.domain.metrologia.calibracao.enums import DecisaoAvaliacaoSubcontratado

_DIAS_ALERTA_ANTES = 30


@dataclass(frozen=True, slots=True)
class AlertaAvaliacaoSubcontratado:
    """Alerta a publicar (caller emite Subcontratacao.AvaliacaoVencendo|Vencida)."""

    laboratorio_id: UUID
    tenant_id: UUID
    avaliacao_id: UUID  # FK da ultima avaliacao
    avaliado_em_anterior: datetime
    proxima_avaliacao_em: datetime
    dias_restantes: int  # negativo se ja vencida
    decisao_anterior: DecisaoAvaliacaoSubcontratado
    severidade: str  # P2_ALERTA | P1_VENCIDA
    correlation_id: UUID  # herdado da avaliacao anterior


def _classificar(dias_restantes: int) -> str:
    if dias_restantes < 0:
        return "P1_VENCIDA"
    if dias_restantes <= _DIAS_ALERTA_ANTES:
        return "P2_ALERTA"
    return "NONE"


def executar(
    *,
    ultimas_avaliacoes: list[AvaliacaoPeriodicaSubcontratadoSnapshot],
    agora: datetime,
) -> list[AlertaAvaliacaoSubcontratado]:
    """Filtra avaliacoes proximas do vencimento ou vencidas.

    Args:
      ultimas_avaliacoes: snapshots ja filtrados pelo caller — UMA por
        LaboratorioSubcontratado (DISTINCT ON laboratorio_id ORDER BY
        avaliado_em DESC).
      agora: timestamp atual (tz-aware).

    Returns:
      Lista de AlertaAvaliacaoSubcontratado para severidade != NONE.

    Levanta:
      ValueError se agora nao for tz-aware.
    """
    if agora.tzinfo is None:
        raise ValueError(
            "verificar_avaliacoes_subcontratados_vencendo: agora exige "
            "datetime tz-aware (INV-VIG-004)"
        )

    alertas: list[AlertaAvaliacaoSubcontratado] = []
    for snapshot in ultimas_avaliacoes:
        # Subcontratado ja DESCREDENCIADO nao precisa alertar (foi removido
        # do pool operacional; subcontratar_calibracao runtime ja bloqueia).
        if snapshot.decisao == DecisaoAvaliacaoSubcontratado.DESCREDENCIAR:
            continue
        delta = snapshot.proxima_avaliacao_em - agora
        # `delta.days` faz floor: 30d23h vira 30; -1h vira -1.
        # Para vencida usamos `< 0`; para alerta antecipado `<= 30`.
        if delta.total_seconds() < 0:
            # Vencida — calcula dias negativos
            dias = -((abs(delta).days) + (1 if abs(delta).seconds > 0 else 0))
            # Equivalente a `math.ceil(-delta.days)` — sempre <= -1.
            if dias == 0:
                dias = -1
        else:
            dias = delta.days
        severidade = _classificar(dias)
        if severidade == "NONE":
            continue
        alertas.append(
            AlertaAvaliacaoSubcontratado(
                laboratorio_id=snapshot.laboratorio_id,
                tenant_id=snapshot.tenant_id,
                avaliacao_id=snapshot.id,
                avaliado_em_anterior=snapshot.avaliado_em,
                proxima_avaliacao_em=snapshot.proxima_avaliacao_em,
                dias_restantes=dias,
                decisao_anterior=snapshot.decisao,
                severidade=severidade,
                correlation_id=snapshot.correlation_id,
            )
        )
    return alertas
