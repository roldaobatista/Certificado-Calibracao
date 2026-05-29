"""Use case `calcular_valor_convencional` — US-PAD-009 (M5 T-PAD-027, ADR-0071).

Calcula o valor convencional do padrao a partir do historico de certificados
externos, com VERIFICACAO DE SOFTWARE (cl. 7.11): 2 implementacoes independentes
do MESMO mensurando (forma fechada vs decomposta). Se divergirem, e bug de
software (`DivergenciaImplementacoesError`) — bloqueia release, NAO e divergencia
metrologica. k via Welch-Satterthwaite quando nu_eff < 30 (reuso GUM M4).

EXCLUSIVO perfil A/B (US-PAD-009). Use case PURO — apenas gateia perfil e delega
ao motor de dominio `valor_convencional.calcular` (sem Django, sem persistencia:
o resultado alimenta o cadastro/recal do padrao no caller).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.metrologia.padroes import valor_convencional
from src.domain.metrologia.padroes.valor_convencional import (
    CertHistorico,
    ResultadoValorConvencional,
)


class PerfilNaoPermiteSegundoCaminhoError(Exception):
    """US-PAD-009 — 2o caminho de calculo exclusivo perfil A/B."""

    def __init__(self) -> None:
        super().__init__(
            "US-PAD-009: calculo do valor convencional com 2o caminho (cl. 7.11) "
            "e exclusivo de tenant perfil A/B (ADR-0067/ADR-0071)."
        )


@dataclass(frozen=True, slots=True)
class CalcularValorConvencionalInput:
    certs: tuple[CertHistorico, ...]
    tenant_e_perfil_a_ou_b: bool

    def __post_init__(self) -> None:
        if not self.certs:
            raise ValueError(
                "calcular_valor_convencional exige >=1 certificado historico."
            )


@dataclass(frozen=True, slots=True)
class CalcularValorConvencionalOutput:
    resultado: ResultadoValorConvencional


def executar(
    inp: CalcularValorConvencionalInput,
) -> CalcularValorConvencionalOutput:
    """Gateia perfil e delega ao motor (propaga DivergenciaImplementacoesError)."""
    if not inp.tenant_e_perfil_a_ou_b:
        raise PerfilNaoPermiteSegundoCaminhoError
    resultado = valor_convencional.calcular(list(inp.certs))
    return CalcularValorConvencionalOutput(resultado=resultado)
