# ruff: noqa: RUF001, RUF002, RUF003 — simbolo grego canonico (σ = sigma) na notacao estatistica oficial
"""Carta de controle Shewhart — deteccao Western Electric (M5 T-PAD-004).

Decimal puro (sem numpy — DEP-001; mesmo motivo de gum_classico.py). Read-model
calculado on-demand (ADR-0070): os pontos vivem WORM em VerificacaoIntermediaria
+ RecalExternoPadrao; aqui so calculamos limites + detectamos violacoes. A
DECISAO derivada (quando uma regra dispara) eh congelada em AnaliseCartaControle
WORM pelo use case (ADR-0070 — fora deste modulo puro).

Regras (ADR-0070 + correcoes RBC C-3):
  R1 — 1 ponto alem de ±3σ (violacao dura P1)
  R2 — 2 de 3 consecutivos alem de ±2σ DO MESMO LADO
  R3 — 4 de 5 consecutivos alem de ±1σ DO MESMO LADO
  R4 — 8 consecutivos do mesmo lado da linha central
  R5 — 7 consecutivos monotonicos (tendencia — cerne da deteccao de deriva)

`VERSAO_MOTOR_SHEWHART` versiona o conjunto de regras + metodo estatistico
(cl. 7.11 — mudar regra muda decisao de aceite/recalibracao). Metodo de σ:
desvio-padrao amostral (n-1). O metodo definitivo (amostral vs moving-range)
fica sujeito a revisao de consultor RBC credenciado antes do 1º tenant perfil A
(GATE-PAD-SHEWHART-RBC) — por isso versionado.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .enums import RegraWesternElectric

VERSAO_MOTOR_SHEWHART = "1.0.0-amostral"

_MIN_PONTOS_LIMITES = 2  # desvio-padrao amostral exige n>=2


@dataclass(frozen=True, slots=True)
class LimitesControle:
    """Limites de controle congelaveis (entram no snapshot AnaliseCartaControle)."""

    linha_central: Decimal
    sigma: Decimal
    ucl: Decimal  # LC + 3σ
    lcl: Decimal  # LC - 3σ
    n_pontos: int
    versao_motor: str = VERSAO_MOTOR_SHEWHART


@dataclass(frozen=True, slots=True)
class ViolacaoWesternElectric:
    """Uma violacao detectada + os indices dos pontos que a formaram.

    `indices_pontos` referencia posicoes na serie (o use case mapeia pra FKs das
    VIs/recals — ADR-0070 `pontos_referenciados`, sem copiar valores).
    """

    regra: RegraWesternElectric
    indices_pontos: tuple[int, ...]


def calcular_limites(pontos: list[Decimal]) -> LimitesControle:
    """LC = media; σ = desvio-padrao amostral (n-1); UCL/LCL = LC ± 3σ.

    Levanta ValueError se < 2 pontos (σ amostral indefinido).
    """
    n = len(pontos)
    if n < _MIN_PONTOS_LIMITES:
        raise ValueError(
            f"calcular_limites exige >= {_MIN_PONTOS_LIMITES} pontos (achou {n})"
        )
    for p in pontos:
        if not isinstance(p, Decimal):
            raise TypeError(
                f"ponto deve ser Decimal (achou {type(p).__name__}) — "
                f"float introduz erro metrologico"
            )
    soma = sum(pontos, Decimal("0"))
    lc = soma / Decimal(n)
    variancia = sum(((p - lc) * (p - lc) for p in pontos), Decimal("0")) / Decimal(n - 1)
    sigma = variancia.sqrt()
    return LimitesControle(
        linha_central=lc,
        sigma=sigma,
        ucl=lc + Decimal("3") * sigma,
        lcl=lc - Decimal("3") * sigma,
        n_pontos=n,
    )


def _acima(valor: Decimal, lc: Decimal, sigma: Decimal, n_sigma: int) -> bool:
    return valor > lc + Decimal(n_sigma) * sigma


def _abaixo(valor: Decimal, lc: Decimal, sigma: Decimal, n_sigma: int) -> bool:
    return valor < lc - Decimal(n_sigma) * sigma


def detectar_violacoes(
    pontos: list[Decimal], limites: LimitesControle
) -> list[ViolacaoWesternElectric]:
    """Aplica as 5 regras Western Electric. Retorna todas as violacoes detectadas
    (uma serie pode disparar mais de uma regra).
    """
    lc = limites.linha_central
    sigma = limites.sigma
    violacoes: list[ViolacaoWesternElectric] = []

    # σ=0 (todos os pontos iguais): nenhuma regra baseada em σ dispara; R4/R5
    # (lado da media / monotonia) ainda valem.
    if sigma > 0:
        # R1 — 1 ponto alem de ±3σ.
        for i, v in enumerate(pontos):
            if _acima(v, lc, sigma, 3) or _abaixo(v, lc, sigma, 3):
                violacoes.append(
                    ViolacaoWesternElectric(
                        RegraWesternElectric.REGRA_1_FORA_3SIGMA, (i,)
                    )
                )

        # R2 — 2 de 3 consecutivos alem de ±2σ DO MESMO LADO.
        for i in range(len(pontos) - 2):
            janela = pontos[i : i + 3]
            acima = [i + j for j, v in enumerate(janela) if _acima(v, lc, sigma, 2)]
            abaixo = [i + j for j, v in enumerate(janela) if _abaixo(v, lc, sigma, 2)]
            if len(acima) >= 2:
                violacoes.append(
                    ViolacaoWesternElectric(
                        RegraWesternElectric.REGRA_2_2DE3_2SIGMA, tuple(acima)
                    )
                )
            elif len(abaixo) >= 2:
                violacoes.append(
                    ViolacaoWesternElectric(
                        RegraWesternElectric.REGRA_2_2DE3_2SIGMA, tuple(abaixo)
                    )
                )

        # R3 — 4 de 5 consecutivos alem de ±1σ DO MESMO LADO.
        for i in range(len(pontos) - 4):
            janela = pontos[i : i + 5]
            acima = [i + j for j, v in enumerate(janela) if _acima(v, lc, sigma, 1)]
            abaixo = [i + j for j, v in enumerate(janela) if _abaixo(v, lc, sigma, 1)]
            if len(acima) >= 4:
                violacoes.append(
                    ViolacaoWesternElectric(
                        RegraWesternElectric.REGRA_3_4DE5_1SIGMA, tuple(acima)
                    )
                )
            elif len(abaixo) >= 4:
                violacoes.append(
                    ViolacaoWesternElectric(
                        RegraWesternElectric.REGRA_3_4DE5_1SIGMA, tuple(abaixo)
                    )
                )

    # R4 — 8 consecutivos do mesmo lado da linha central (independe de σ).
    for i in range(len(pontos) - 7):
        janela = pontos[i : i + 8]
        if all(v > lc for v in janela) or all(v < lc for v in janela):
            violacoes.append(
                ViolacaoWesternElectric(
                    RegraWesternElectric.REGRA_4_RUN_8, tuple(range(i, i + 8))
                )
            )

    # R5 — 7 consecutivos monotonicos (estritamente cresc. ou decresc.).
    for i in range(len(pontos) - 6):
        janela = pontos[i : i + 7]
        crescente = all(janela[j] < janela[j + 1] for j in range(6))
        decrescente = all(janela[j] > janela[j + 1] for j in range(6))
        if crescente or decrescente:
            violacoes.append(
                ViolacaoWesternElectric(
                    RegraWesternElectric.REGRA_5_TENDENCIA_7, tuple(range(i, i + 7))
                )
            )

    return violacoes
