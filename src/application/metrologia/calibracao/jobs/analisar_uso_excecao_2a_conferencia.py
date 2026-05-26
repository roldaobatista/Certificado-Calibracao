"""Job `analisar_uso_excecao_2a_conferencia` (T-CAL-121) — AC-CAL-008-5 + P-CAL-S9.

ADR-0026 abre excecao na 2a conferencia (conferente == revisor) em 4
condicoes objetivas, com limite duro de 5%/mes do total de calibracoes
aprovadas. AC-CAL-008-5 + P-CAL-S9 corretora: alertar P2 (gerente
qualidade) quando o uso atinge 3%/mes (1/3 do limite), pra ter folga
operacional antes do estouro.

Janela movel: 30 dias contados a partir de `agora`.

Funcao PURA — recebe lista de snapshots de Calibracao APROVADA na janela
e separa entre as que usaram excecao (excecao_2a_conf_id NOT NULL) vs
total. Calcula percentual; alerta P2 se >= 3%; alerta P1 se >= 5%.

Adapter Django (caller) consulta DB com:
  Calibracao.objects.filter(
      tenant_id=t,
      status='aprovada',
      criada_em__gte=agora - timedelta(days=30),
  )
e passa lista para esta funcao.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao

_JANELA_DIAS = 30
_LIMITE_ALERTA_P2 = Decimal("0.03")  # 3% — ADR-0026 alerta antecipado
_LIMITE_ALERTA_P1 = Decimal("0.05")  # 5% — ADR-0026 limite duro


@dataclass(frozen=True, slots=True)
class AnaliseUsoExcecao:
    """Resultado da analise — caller publica alerta se severidade != NONE."""

    tenant_id: UUID
    janela_inicio: datetime
    janela_fim: datetime
    total_aprovadas: int
    total_com_excecao: int
    percentual: Decimal  # 4 casas; 0.0250 = 2.50%
    severidade: str  # NONE | P2_ALERTA | P1_ESTOURO


def _calcular_percentual(total_aprovadas: int, total_com_excecao: int) -> Decimal:
    if total_aprovadas == 0:
        return Decimal("0.0000")
    raw = Decimal(total_com_excecao) / Decimal(total_aprovadas)
    return raw.quantize(Decimal("0.0001"))


def _classificar_severidade(percentual: Decimal) -> str:
    if percentual >= _LIMITE_ALERTA_P1:
        return "P1_ESTOURO"
    if percentual >= _LIMITE_ALERTA_P2:
        return "P2_ALERTA"
    return "NONE"


def executar(
    *,
    tenant_id: UUID,
    calibracoes_aprovadas_janela: list[CalibracaoSnapshot],
    agora: datetime,
) -> AnaliseUsoExcecao:
    """Analisa uso de excecao 2a conferencia em janela movel 30d.

    Args:
      tenant_id: tenant alvo.
      calibracoes_aprovadas_janela: snapshots ja filtrados pelo caller
        (status=APROVADA + criada_em >= agora - 30d + tenant_id=...).
      agora: timestamp atual (tz-aware).

    Returns:
      AnaliseUsoExcecao com percentual + severidade.

    Levanta:
      ValueError se `agora` nao for tz-aware.
    """
    if agora.tzinfo is None:
        raise ValueError(
            "analisar_uso_excecao_2a_conferencia: agora exige datetime tz-aware "
            "(INV-VIG-004)"
        )

    janela_inicio = agora - timedelta(days=_JANELA_DIAS)

    aprovadas = 0
    com_excecao = 0
    for snapshot in calibracoes_aprovadas_janela:
        # Defensivo: ignora status != APROVADA (caller deveria filtrar)
        if snapshot.status != EstadoCalibracao.APROVADA:
            continue
        # Defensivo: ignora tenant errado
        if snapshot.tenant_id != tenant_id:
            continue
        # Defensivo: ignora fora da janela
        if snapshot.criada_em < janela_inicio:
            continue
        aprovadas += 1
        if snapshot.excecao_2a_conf_id is not None:
            com_excecao += 1

    percentual = _calcular_percentual(aprovadas, com_excecao)
    severidade = _classificar_severidade(percentual)

    return AnaliseUsoExcecao(
        tenant_id=tenant_id,
        janela_inicio=janela_inicio,
        janela_fim=agora,
        total_aprovadas=aprovadas,
        total_com_excecao=com_excecao,
        percentual=percentual,
        severidade=severidade,
    )
