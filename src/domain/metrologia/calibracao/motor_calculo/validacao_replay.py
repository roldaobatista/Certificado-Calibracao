"""Validacao de divergencia entre algoritmos (P4 Fase 3 Batch D — T-CAL-059..060).

§16.5 spec M4 + ADR-0025 cl. 7.11 — 2 algoritmos independentes (GUM
classico Decimal + Monte Carlo NumPy) calculam U expandida da mesma
calibracao. Compara-se a divergencia para detectar bug no motor.

Classificacao (§16.5):
  - divergencia <= 0.1%   -> SILENCIOSO (passa)
  - 0.1% < div <= 1%      -> ALERTA_P3 (Qualidade revisa; nao bloqueia)
  - divergencia > 1%      -> INACEITAVEL (levanta DivergenciaCalculoInaceitavel;
                                          estado calibracao volta em_execucao
                                          + NC automatica CAPA aberto)

Por que esse caminho:
- Sem comparacao, bug em um motor passaria silencioso ate auditoria CGCRE
  pegar inconsistencia em campo (retencao 25a) — catastrofe regulatoria.
- 1% e tolerancia conservadora (NIT-DICLA-030 §7 — incerteza tipicamente
  fica entre 0.1% e 5% do valor lido; 1% de divergencia entre algoritmos
  ja eh suspeito).
- Replay deterministico (ADR-0025) garante que mesma input -> mesma
  classificacao, sempre.

Catalogo:
  - ClassificacaoDivergencia: enum (SILENCIOSO | ALERTA_P3 | INACEITAVEL)
  - DivergenciaCalculoInaceitavel: excecao quando div > 1%
  - comparar_algoritmos(resultado_gum, resultado_mc) ->
      (divergencia_pct: Decimal, classificacao: ClassificacaoDivergencia)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.domain.metrologia.calibracao.motor_calculo.gum_classico import (
    ResultadoGUM,
)

# Limites da classificacao (§16.5 spec — Decimal puro pra determinismo)
LIMITE_SILENCIOSO_PCT = Decimal("0.1")  # <= 0.1% silencioso
LIMITE_ALERTA_PCT = Decimal("1.0")  # 0.1% < x <= 1% alerta P3


class ClassificacaoDivergencia(str, Enum):
    """3 zonas de severidade da divergencia algoritmo_1 vs algoritmo_2."""

    SILENCIOSO = "SILENCIOSO"
    ALERTA_P3 = "ALERTA_P3"
    INACEITAVEL = "INACEITAVEL"


class DivergenciaCalculoInaceitavel(Exception):
    """Levantada quando divergencia > 1% (estado volta em_execucao + NC).

    Caller (use case `solicitarRevisao`) captura, registra
    EventoDeCalibracao tipo=divergencia_motor_calculo_inaceitavel +
    cria NaoConformidade automatica + transita estado calibracao
    em_revisao_1 -> em_execucao (re-executar).
    """

    def __init__(self, divergencia_pct: Decimal, U_gum: Decimal, U_mc: Decimal) -> None:  # - U eh notacao metrologica
        self.divergencia_pct = divergencia_pct
        self.U_gum = U_gum
        self.U_mc = U_mc
        super().__init__(
            f"DivergenciaCalculoInaceitavel: {divergencia_pct}% "
            f"(GUM={U_gum}, MC={U_mc}; limite={LIMITE_ALERTA_PCT}%)"
        )


@dataclass(frozen=True)
class ResultadoMC:
    """Resultado Monte Carlo (placeholder ate Batch C implementar real).

    Mesma interface conceitual de ResultadoGUM, mas vem do 2o caminho.
    Batch C (T-CAL-055..058 — BLOQUEADO DEP-001 numpy) substitui o stub.

    Campos:
      u_combinada: estimativa Monte Carlo de u_c (Decimal).
      U_expandida: U pela cobertura empirica (percentis 2.275/97.725).
      nivel_confianca: cobertura nominal (default 0.9545).
      n_iteracoes: numero de iteracoes Monte Carlo executadas.
      seed: seed deterministico (= calibracao_id hash, ADR-0025).
    """

    u_combinada: Decimal
    U_expandida: Decimal  # - notacao metrologica canonica (U maiusculo)
    nivel_confianca: Decimal
    n_iteracoes: int
    seed: int


def comparar_algoritmos(
    resultado_gum: ResultadoGUM,
    resultado_mc: ResultadoMC,
) -> tuple[Decimal, ClassificacaoDivergencia]:
    """Compara U_expandida dos 2 algoritmos e classifica divergencia.

    Calculo:
      div_pct = |U_gum - U_mc| / U_gum * 100

    Args:
      resultado_gum: ResultadoGUM do 1o caminho (Decimal puro).
      resultado_mc: ResultadoMC do 2o caminho (Monte Carlo).

    Retorna:
      (divergencia_pct, classificacao) — divergencia em pontos
      percentuais (Decimal) + classe (ClassificacaoDivergencia).

    Levanta:
      DivergenciaCalculoInaceitavel — quando div > LIMITE_ALERTA_PCT (1%).
      ValueError — quando U_gum == 0 (divisao por zero).
    """
    if resultado_gum.U_expandida == 0:
        # Calibracao descritiva (sem limites) — divergencia indefinida.
        # Por convencao: se MC tambem == 0, classifica SILENCIOSO.
        # Se MC != 0 e GUM == 0, INACEITAVEL (algoritmos discordam estrutural).
        if resultado_mc.U_expandida == 0:
            return Decimal("0"), ClassificacaoDivergencia.SILENCIOSO
        raise DivergenciaCalculoInaceitavel(
            Decimal("999"),  # marcador indefinido
            resultado_gum.U_expandida,
            resultado_mc.U_expandida,
        )

    diff_abs = abs(resultado_gum.U_expandida - resultado_mc.U_expandida)
    divergencia_pct = (diff_abs / resultado_gum.U_expandida) * Decimal("100")

    if divergencia_pct <= LIMITE_SILENCIOSO_PCT:
        return divergencia_pct, ClassificacaoDivergencia.SILENCIOSO

    if divergencia_pct <= LIMITE_ALERTA_PCT:
        return divergencia_pct, ClassificacaoDivergencia.ALERTA_P3

    # > 1% -> INACEITAVEL: levanta para forcar caller a tratar
    raise DivergenciaCalculoInaceitavel(
        divergencia_pct,
        resultado_gum.U_expandida,
        resultado_mc.U_expandida,
    )
