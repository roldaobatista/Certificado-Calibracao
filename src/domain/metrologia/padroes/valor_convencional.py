# ruff: noqa: RUF001, RUF002, RUF003 — simbolos gregos canonicos (σ, ν) na notacao GUM
"""Valor convencional do padrao — 2º caminho de cálculo cl. 7.11 (M5 T-PAD-005).

ADR-0071: o "2º caminho" é VERIFICACAO DE SOFTWARE — duas implementacoes
INDEPENDENTES do MESMO mensurando que devem convergir (provam ausencia de bug),
NAO dois estimadores de naturezas diferentes. A deteccao de deriva (tendencia)
é controle SEPARADO, na carta Shewhart (regra 5 — shewhart.py), nao aqui.

Mensurando: melhor estimativa do valor convencional do padrao a partir dos N
certificados externos historicos = media ponderada pela inversa da variancia
(JCGM 100 / EURAMET cg-18). Decimal puro (sem numpy — DEP-001).

Incerteza: u_c = sqrt(1 / Σ(1/u_i²)); ν_eff por Welch-Satterthwaite; k via
t-Student (reuso fator_k_para_95 do motor GUM M4) quando ν_eff < 30, senao k=2
(NC-3 RBC — k=2 fixo subestima com poucos recals).

Metodo versionado (`VERSAO_MOTOR_VALOR_CONVENCIONAL` — cl. 7.11); revisao de
consultor RBC credenciado pre-tenant-A (GATE-PAD-SHEWHART-RBC).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext

from src.domain.metrologia.calibracao.motor_calculo.gum_classico import (
    fator_k_para_95,
)

# Mesma precisao do motor GUM (gum_classico sobe pra 50) — chain longa de Decimal.
getcontext().prec = max(getcontext().prec, 50)

VERSAO_MOTOR_VALOR_CONVENCIONAL = "1.0.0-media-ponderada-inv-var"

# Tolerancia de convergencia entre as 2 implementacoes (relativa). Com prec=50,
# divergencia real (bug) é ordens de magnitude maior; 1e-30 separa ruido de
# Decimal de erro de implementacao.
_TOL_CONVERGENCIA_RELATIVA = Decimal("1e-30")


@dataclass(frozen=True, slots=True)
class CertHistorico:
    """Um certificado externo historico do padrao (entrada do calculo)."""

    valor: Decimal  # valor convencional reportado pelo cert
    u_padrao: Decimal  # incerteza-padrao u_i (> 0)
    graus_liberdade: int | None  # ν_i (None = infinito)

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal) or not isinstance(self.u_padrao, Decimal):
            raise TypeError("CertHistorico.valor/u_padrao devem ser Decimal")
        if self.u_padrao <= 0:
            raise ValueError(f"CertHistorico.u_padrao deve ser > 0 (achou {self.u_padrao})")
        if self.graus_liberdade is not None and self.graus_liberdade < 1:
            raise ValueError(f"CertHistorico.graus_liberdade < 1: {self.graus_liberdade}")


class DivergenciaImplementacoesError(Exception):
    """As 2 implementacoes do mesmo mensurando divergiram — bug de software
    (ADR-0071). NAO é divergencia metrologica; bloqueia release."""

    def __init__(self, caminho_a: Decimal, caminho_b: Decimal) -> None:
        self.caminho_a = caminho_a
        self.caminho_b = caminho_b
        super().__init__(
            f"2º caminho cl. 7.11: implementacoes divergiram (bug de software) — "
            f"A={caminho_a} B={caminho_b}"
        )


@dataclass(frozen=True, slots=True)
class ResultadoValorConvencional:
    valor_convencional: Decimal
    u_combinada: Decimal
    graus_liberdade_efetivos: int | None
    k: Decimal
    U_expandida: Decimal  # - U notacao metrologica canonica
    n_certificados: int
    versao_motor: str = VERSAO_MOTOR_VALOR_CONVENCIONAL


def _media_ponderada_fechada(certs: list[CertHistorico]) -> Decimal:
    """Implementacao A — forma fechada: x̄ = Σ(x_i/u_i²) / Σ(1/u_i²)."""
    num = sum((c.valor / (c.u_padrao * c.u_padrao) for c in certs), Decimal("0"))
    den = sum((Decimal("1") / (c.u_padrao * c.u_padrao) for c in certs), Decimal("0"))
    return num / den


def _media_ponderada_decomposta(certs: list[CertHistorico]) -> Decimal:
    """Implementacao B — INDEPENDENTE: normaliza pesos primeiro, depois soma.

    p_i = (1/u_i²) / Σ(1/u_j²) ;  x̄ = Σ(p_i · x_i). Algebricamente igual a A,
    porem via quantidades/ordem diferentes — um bug em uma das duas diverge.
    """
    total_inv_var = sum(
        (Decimal("1") / (c.u_padrao * c.u_padrao) for c in certs), Decimal("0")
    )
    acc = Decimal("0")
    for c in certs:
        peso = (Decimal("1") / (c.u_padrao * c.u_padrao)) / total_inv_var
        acc += peso * c.valor
    return acc


def _u_combinada(certs: list[CertHistorico]) -> Decimal:
    """u_c = sqrt(1 / Σ(1/u_i²))."""
    total_inv_var = sum(
        (Decimal("1") / (c.u_padrao * c.u_padrao) for c in certs), Decimal("0")
    )
    return (Decimal("1") / total_inv_var).sqrt()


def _graus_liberdade_efetivos(
    certs: list[CertHistorico], u_c: Decimal
) -> int | None:
    """Welch-Satterthwaite para a media ponderada (JCGM 100 G.4).

    ν_eff = u_c⁴ / Σ( c_i⁴ / ν_i ), c_i = (1/u_i)/Σ(1/u_j²) = sensibilidade·u_i.
    Componentes com ν_i = None (infinito) nao contribuem (termo zero). Se TODOS
    sao infinitos, ν_eff = None (k=2).
    """
    total_inv_var = sum(
        (Decimal("1") / (c.u_padrao * c.u_padrao) for c in certs), Decimal("0")
    )
    soma = Decimal("0")
    algum_finito = False
    for c in certs:
        if c.graus_liberdade is None:
            continue
        algum_finito = True
        # contribuicao_i = (1/u_i) / Σ(1/u²)
        contrib = (Decimal("1") / c.u_padrao) / total_inv_var
        contrib4 = contrib * contrib * contrib * contrib
        soma += contrib4 / Decimal(c.graus_liberdade)
    if not algum_finito or soma == 0:
        return None
    u_c4 = u_c * u_c * u_c * u_c
    nu = u_c4 / soma
    # piso conservador: floor (subestima dof -> k maior -> conservador)
    return max(1, int(nu))


def calcular(certs: list[CertHistorico]) -> ResultadoValorConvencional:
    """Calcula o valor convencional + incerteza expandida com verificacao
    de software (2 implementacoes do mesmo mensurando — ADR-0071).

    Levanta DivergenciaImplementacoesError se as implementacoes nao convergem
    (bug). ValueError se < 1 certificado.
    """
    if not certs:
        raise ValueError("calcular valor convencional exige >= 1 certificado")

    caminho_a = _media_ponderada_fechada(certs)
    caminho_b = _media_ponderada_decomposta(certs)

    # Verificacao de software cl. 7.11: as 2 implementacoes do MESMO mensurando
    # devem convergir. Divergencia = bug, NAO controle metrologico.
    escala = abs(caminho_a) if caminho_a != 0 else Decimal("1")
    if abs(caminho_a - caminho_b) > escala * _TOL_CONVERGENCIA_RELATIVA:
        raise DivergenciaImplementacoesError(caminho_a, caminho_b)

    u_c = _u_combinada(certs)
    nu_eff = _graus_liberdade_efetivos(certs, u_c)
    k = fator_k_para_95(nu_eff)
    return ResultadoValorConvencional(
        valor_convencional=caminho_a,
        u_combinada=u_c,
        graus_liberdade_efetivos=nu_eff,
        k=k,
        U_expandida=k * u_c,
        n_certificados=len(certs),
    )
