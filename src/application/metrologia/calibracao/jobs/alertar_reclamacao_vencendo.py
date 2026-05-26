"""Job `alertar_reclamacao_vencendo` (T-CAL-116) — AC-CAL-018-3.

ISO 17025 cl. 7.9 + CDC art. 26 — toda reclamacao aberta tem prazo
default de 15 DIAS UTEIS pra resposta. Quando o prazo eh excedido,
gerar alerta P1 (gerente qualidade + DPO).

Funcao PURA — recebe snapshots de ReclamacaoCalibracao em estado
RECEBIDA ou EM_ANALISE + `agora`. Retorna lista de alertas a emitir.
Caller (adapter Django) consulta DB, chama essa funcao, publica
alertas via bus.

Logica dias uteis (simplificada Wave A):
  prazo_alvo = aberta_em + N dias corridos (onde N = prazo_resposta_dia_util
                                            * 1.40 — fator conservador
                                            que aproxima 5d uteis ≈ 7d
                                            corridos sem feriados).
Refinamento V2: calendario brasileiro com feriados via biblioteca
(workalendar / holidays) — diferido. Por enquanto, fator 1.40 cobre
fins-de-semana sem feriado nacional. Falsos negativos (alerta tarde)
em semanas com feriados sao aceitos como debito de Wave A.

INV-RECL-PRAZO-001 (deriva AC-CAL-018-3): reclamacao com
(aberta_em + dias_uteis) < agora E estado IN (RECEBIDA, EM_ANALISE)
gera alerta. Idempotente: alertas duplicados sao deduplicados pelo
caller via `correlation_id` no bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    ReclamacaoCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import EstadoReclamacao

# Fator que aproxima dias uteis em dias corridos sem feriados.
# 5 dias uteis ≈ 7 dias corridos (1.40); 15 dias uteis ≈ 21 dias corridos.
_FATOR_DIA_UTIL_PARA_CORRIDO = 1.40


@dataclass(frozen=True, slots=True)
class AlertaReclamacaoVencendo:
    """Alerta que adapter Django publica via bus (Calibracao.ReclamacaoSLAEstourado)."""

    reclamacao_id: UUID
    tenant_id: UUID
    aberta_em: datetime
    prazo_resposta_dia_util: int
    dias_atrasada: int  # > 0 sempre
    estado_atual: EstadoReclamacao  # RECEBIDA ou EM_ANALISE
    correlation_id: UUID  # herdado da reclamacao


def _prazo_estourou(
    snapshot: ReclamacaoCalibracaoSnapshot, agora: datetime
) -> tuple[bool, int]:
    """Retorna (estourou, dias_atrasada). dias_atrasada=0 se nao estourou."""
    dias_corridos_limite = round(
        snapshot.prazo_resposta_dia_util * _FATOR_DIA_UTIL_PARA_CORRIDO
    )
    prazo_alvo = snapshot.aberta_em + timedelta(days=dias_corridos_limite)
    if agora <= prazo_alvo:
        return False, 0
    diff = agora - prazo_alvo
    return True, max(1, diff.days)


def executar(
    *,
    reclamacoes_abertas: list[ReclamacaoCalibracaoSnapshot],
    agora: datetime,
) -> list[AlertaReclamacaoVencendo]:
    """Filtra reclamacoes em RECEBIDA/EM_ANALISE com prazo estourado.

    Args:
      reclamacoes_abertas: snapshots ja filtrados pelo caller (estado
        IN (RECEBIDA, EM_ANALISE)).
      agora: timestamp atual (tz-aware).

    Returns:
      Lista de AlertaReclamacaoVencendo (pode ser vazia).

    Levanta:
      ValueError se `agora` nao for tz-aware (INV-VIG-004).
    """
    if agora.tzinfo is None:
        raise ValueError(
            "alertar_reclamacao_vencendo: agora exige datetime tz-aware "
            "(INV-VIG-004)"
        )

    alertas: list[AlertaReclamacaoVencendo] = []
    for snapshot in reclamacoes_abertas:
        # Defensivo: ignora terminais (caller deveria filtrar antes)
        if snapshot.estado not in {
            EstadoReclamacao.RECEBIDA,
            EstadoReclamacao.EM_ANALISE,
        }:
            continue
        estourou, dias = _prazo_estourou(snapshot, agora)
        if estourou:
            alertas.append(
                AlertaReclamacaoVencendo(
                    reclamacao_id=snapshot.id,
                    tenant_id=snapshot.tenant_id,
                    aberta_em=snapshot.aberta_em,
                    prazo_resposta_dia_util=snapshot.prazo_resposta_dia_util,
                    dias_atrasada=dias,
                    estado_atual=snapshot.estado,
                    correlation_id=snapshot.correlation_id,
                )
            )
    return alertas
