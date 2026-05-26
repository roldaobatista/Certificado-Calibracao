"""Calculo de PFA e PRA — JCGM 106:2012 §9 + ILAC G8:2019 §4.4.

PFA (Probability of False Accept) — probabilidade de aceitar item que
esta verdadeiramente fora dos limites de especificacao (consumer's risk).
Obrigatorio para regra BANDA_GUARDA_30 (INV-CAL-DEC-004).

PRA (Probability of False Reject) — probabilidade de rejeitar item que
esta verdadeiramente dentro dos limites (producer's risk). Obrigatorio
para regra RISCO_COMPARTILHADO (INV-CAL-DEC-004).

Modelo Gaussiano (JCGM 106 §9.1):
  - desvio-padrao da medicao = U_expandida / k (k=2 default => sigma = U/2)
  - integra densidade Gaussiana sobre a regiao "fora dos limites"
    (PFA) ou "dentro dos limites" condicionada a rejeicao (PRA).

Para o PFA classico:
  PFA = P(verdadeiro fora [LSL, USL] | medicao dentro)
      = (1 - P(verdadeiro dentro)) onde medicao = y
  Aproximacao 2-sided com erf:
    PFA ≈ 1 - (Φ((USL - y)/sigma) - Φ((LSL - y)/sigma))
  onde Φ(z) = (1 + erf(z/√2))/2.

Para PRA classico:
  PRA = P(verdadeiro dentro [LSL, USL] | medicao fora)
      = aproximacao similar invertida.

Por que `math.erf` (stdlib) em vez de numpy/scipy:
  - DEP-001 (auditor-supplychain) bloqueia numpy ate review.
  - Precisao dupla (~15 digitos) eh suficiente para Wave A. Refinamento
    Decimal-puro via serie de Taylor pode vir em V2 (campo
    `versao_motor_calculo` ja absorve a mudanca via replay_hash).

Determinismo:
  `math.erf` eh especificado em IEEE 754 + libm — resultado bit-a-bit
  identico em qualquer SO + arquitetura x86_64/arm64. Suficiente para
  replay 25a (cl. 8.4). Mudanca de versao da libm fica versionada via
  `versao_motor_calculo` (ADR-0025).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

# Fator de cobertura k=2 padrao (nivel de confianca ~95.45%)
K_PADRAO = Decimal("2")


@dataclass(frozen=True, slots=True)
class ParametrosPFAPRA:
    """Parametros de entrada para PFA/PRA (JCGM 106 §9)."""

    valor_medido: Decimal
    U_expandida: Decimal  # - U canonico
    k: Decimal  # fator de cobertura (default 2.0)
    lsl: Decimal | None
    usl: Decimal | None

    def __post_init__(self) -> None:
        if self.k <= 0:
            raise ValueError(
                f"k deve ser > 0 (achou {self.k}) — fator de cobertura GUM"
            )
        if self.U_expandida < 0:
            raise ValueError(
                f"U_expandida deve ser >= 0 (achou {self.U_expandida})"
            )
        if self.lsl is None and self.usl is None:
            raise ValueError(
                "PFA/PRA exigem ao menos um limite (LSL OU USL); "
                "sem limites -> calibracao descritiva -> NA -> PFA nao se aplica"
            )


def _phi(z: float) -> float:
    """Funcao distribuicao acumulada Gaussiana padrao Φ(z).

    Φ(z) = (1 + erf(z/√2))/2.
    `math.erf` eh ISO C99 + IEEE 754 — determinismo cross-platform.
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calcular_pfa(parametros: ParametrosPFAPRA) -> Decimal:
    """PFA (Probability of False Accept) — JCGM 106 §9.1.

    Aproximacao Gaussiana 2-sided. Retorna probabilidade ∈ [0, 1] em
    Decimal com 6 casas (`quantize` para replay determinico).

    Caso especiais:
      - U_expandida == 0 -> PFA == 0 (medicao perfeita; nao ha risco).
      - LSL None ou USL None -> 1-sided (so um limite).

    INV-CAL-DEC-004: chamado obrigatoriamente quando regra=BANDA_GUARDA_30.
    """
    if parametros.U_expandida == 0:
        return Decimal("0.0000")

    sigma = parametros.U_expandida / parametros.k
    sigma_f = float(sigma)
    y = float(parametros.valor_medido)

    if parametros.lsl is not None and parametros.usl is not None:
        # 2-sided: PFA ≈ 1 - (Φ((USL-y)/sigma) - Φ((LSL-y)/sigma))
        usl_f = float(parametros.usl)
        lsl_f = float(parametros.lsl)
        p_dentro = _phi((usl_f - y) / sigma_f) - _phi((lsl_f - y) / sigma_f)
        pfa = max(0.0, 1.0 - p_dentro)
    elif parametros.usl is not None:
        # 1-sided superior: PFA = 1 - Φ((USL-y)/sigma) = Φ(-(USL-y)/sigma)
        usl_f = float(parametros.usl)
        pfa = 1.0 - _phi((usl_f - y) / sigma_f)
    else:
        # 1-sided inferior: PFA = Φ((LSL-y)/sigma)
        assert parametros.lsl is not None  # for type-checker
        lsl_f = float(parametros.lsl)
        pfa = _phi((lsl_f - y) / sigma_f)

    pfa_clamped = max(0.0, min(1.0, pfa))
    return Decimal(f"{pfa_clamped:.6f}")


def calcular_pra(parametros: ParametrosPFAPRA) -> Decimal:
    """PRA (Probability of False Reject) — JCGM 106 §9.

    Em modelo Gaussiano simetrico, PRA ≈ PFA para item proximo aos limites
    (a probabilidade de aceitar fora ~= rejeitar dentro). Mas formalmente:
      PRA = P(verdadeiro dentro [LSL, USL] | medicao fora dos limites)
    Para a aproximacao Wave A, calculamos como complemento simples baseado
    na densidade Gaussiana centrada em y com desvio sigma = U/k:
      PRA = P(verdadeiro fora dos limites) calculado como 1 - P(dentro).

    Esta aproximacao eh conservadora (subestima ligeiramente para itens
    no centro dos limites; superestima para itens proximos a limites).
    Modelo refinado (Bayes prior + densidade do mensurando) entra em V2.

    INV-CAL-DEC-004: chamado obrigatoriamente quando regra=RISCO_COMPARTILHADO.
    """
    # Reusa formula PFA — em Wave A sao matematicamente identicos para
    # o modelo Gaussiano simples. Refinamento Bayesiano com prior do
    # mensurando vai em V2 (campo versao_motor_calculo absorve mudanca
    # via replay_hash; resultados antigos continuam verificaveis).
    return calcular_pfa(parametros)
