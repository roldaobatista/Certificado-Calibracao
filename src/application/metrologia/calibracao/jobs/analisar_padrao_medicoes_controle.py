"""Job `analisar_padrao_medicoes_controle` (T-CAL-118) — P-CAL-R8 RBC.

ISO 17025 cl. 7.7.1 — apos cada INSERT de MedicaoControle, recalcular
as ultimas 30 medicoes do mesmo `padrao_id` + `grandeza` e aplicar 4
regras Western Electric. Se alguma regra disparou na ULTIMA medicao
(a recem-inserida), o caller deve emitir UPDATE de
`regra_western_electric_violada` na MedicaoControle + publicar alerta.

Trigger: por evento `MedicaoControle.Inserida` (consumer procrastinate).

Funcao PURA — recebe janela de ate 30 snapshots em ordem cronologica +
o snapshot recem-inserido. Retorna acao (regra violada) se aplicavel.

Regras (avaliadas mais grave primeiro):
  RULE_1_3SIGMA, RULE_5_TWO_OF_THREE, RULE_2_SEVEN_SAME_SIDE, RULE_3_TREND.

Defesa:
- Sem escore_z (None) na medicao recem-inserida -> nao avalia (motor
  Western Electric exige z-score; padrao sem incerteza_referencia
  cai aqui).
- Janela < 3 medicoes -> avalia apenas RULE_1_3SIGMA (sentinela
  unica suficiente).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import MedicaoControleSnapshot
from src.domain.metrologia.calibracao.motor_calculo.western_electric import (
    avaliar_regras_we,
)


@dataclass(frozen=True, slots=True)
class AcaoAtualizarRegraWE:
    """Acao a executar — caller emite UPDATE na MedicaoControle + alerta."""

    medicao_id: UUID  # FK MedicaoControle (a recem-inserida)
    tenant_id: UUID
    padrao_id: UUID
    grandeza: str
    regra_violada: str  # nome WHITELIST Western Electric
    janela_size: int  # quantidade de medicoes analisadas
    correlation_id: UUID  # herdado da medicao
    severidade: str  # P1_RULE1 (3sigma) | P2_OUTRAS_REGRAS


def _classificar_severidade(regra: str) -> str:
    """RULE_1_3SIGMA eh emergencial (P1); resto P2."""
    if regra == "RULE_1_3SIGMA":
        return "P1_RULE1"
    return "P2_OUTRAS_REGRAS"


def executar(
    *,
    medicao_recente: MedicaoControleSnapshot,
    janela_cronologica: list[MedicaoControleSnapshot],
) -> AcaoAtualizarRegraWE | None:
    """Analisa janela cronologica (antiga -> nova) + medicao recem-inserida.

    Args:
      medicao_recente: snapshot da medicao recem-inserida (caller
        garante que esta inclusa no fim da janela_cronologica OU passa
        janela ja contendo a recente).
      janela_cronologica: snapshots em ordem CRESCENTE de executado_em.
        Caller filtra: mesmo tenant_id + padrao_id + grandeza, ultimas
        30 mais recentes.

    Returns:
      AcaoAtualizarRegraWE se alguma regra disparou; None caso contrario.
    """
    # Defesa: sem z-score na medicao recente, motor nao avalia
    if medicao_recente.escore_z is None:
        return None

    # Coerencia tenant/padrao/grandeza na janela
    janela_valida: list[Decimal] = []
    for snap in janela_cronologica:
        if snap.tenant_id != medicao_recente.tenant_id:
            continue
        if snap.padrao_id != medicao_recente.padrao_id:
            continue
        if snap.grandeza != medicao_recente.grandeza:
            continue
        if snap.escore_z is None:
            continue
        janela_valida.append(snap.escore_z)

    if not janela_valida:
        return None

    regra = avaliar_regras_we(janela_valida)
    if regra is None:
        return None

    return AcaoAtualizarRegraWE(
        medicao_id=medicao_recente.id,
        tenant_id=medicao_recente.tenant_id,
        padrao_id=medicao_recente.padrao_id,
        grandeza=medicao_recente.grandeza,
        regra_violada=regra,
        janela_size=len(janela_valida),
        correlation_id=medicao_recente.correlation_id,
        severidade=_classificar_severidade(regra),
    )
