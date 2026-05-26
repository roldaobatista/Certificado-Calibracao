"""Testes motor PFA/PRA (P4 Fase 5 Batch G — T-CAL-086 / INV-CAL-DEC-004).

JCGM 106:2012 §9 — distribuicao Gaussiana centrada em y com desvio
sigma = U/k. Testes verificam ordem de grandeza + monotonia + casos
de fronteira.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.motor_calculo.pfa_pra import (
    ParametrosPFAPRA,
    calcular_pfa,
    calcular_pra,
)


def _params(
    valor: str,
    U: str,
    lsl: str | None = "90",
    usl: str | None = "110",
    k: str = "2",
) -> ParametrosPFAPRA:
    return ParametrosPFAPRA(
        valor_medido=Decimal(valor),
        U_expandida=Decimal(U),
        k=Decimal(k),
        lsl=Decimal(lsl) if lsl is not None else None,
        usl=Decimal(usl) if usl is not None else None,
    )


class TestPFA:
    def test_u_zero_pfa_zero(self) -> None:
        """Medicao perfeita: PFA = 0 (nao ha incerteza pra introduzir erro)."""
        assert calcular_pfa(_params("100", "0")) == Decimal("0.0000")

    def test_centro_dos_limites_pfa_baixa(self) -> None:
        """Item no centro [90, 110] com U pequena -> PFA proximo de 0."""
        pfa = calcular_pfa(_params("100", "1"))
        assert pfa < Decimal("0.01"), f"esperava PFA<<1%, achou {pfa}"

    def test_proximo_limite_superior_pfa_aumenta(self) -> None:
        """Item proximo ao USL -> PFA significativa."""
        pfa = calcular_pfa(_params("109", "2"))
        # 109 +- 1 (sigma=1) — cauda alem 110 representa ~16%
        assert pfa > Decimal("0.10"), f"esperava PFA>10%, achou {pfa}"

    def test_fora_limites_pfa_alta(self) -> None:
        """Item ja fora dos limites -> PFA tende a 100% (toda a densidade
        proximamente fora)."""
        pfa = calcular_pfa(_params("115", "1"))  # USL=110, valor=115
        # Item 5sigma alem do USL -> cauda dentro [LSL,USL] muito pequena
        assert pfa > Decimal("0.99"), f"esperava PFA>99%, achou {pfa}"

    def test_pfa_clamped_entre_0_e_1(self) -> None:
        pfa1 = calcular_pfa(_params("50", "100"))  # valores extremos
        assert Decimal("0") <= pfa1 <= Decimal("1")
        pfa2 = calcular_pfa(_params("150", "100"))
        assert Decimal("0") <= pfa2 <= Decimal("1")

    def test_one_sided_usl(self) -> None:
        """So USL — densidade alem do USL eh PFA."""
        pfa = calcular_pfa(_params("100", "10", lsl=None, usl="110"))
        # 100 +- 5 (sigma=5) — Φ(2)=0.9772 -> PFA = 1 - 0.9772 = ~2.3%
        assert Decimal("0.01") < pfa < Decimal("0.05")

    def test_one_sided_lsl(self) -> None:
        pfa = calcular_pfa(_params("100", "10", lsl="90", usl=None))
        # densidade abaixo de LSL=90 com sigma=5 e centro 100 -> ~2.3%
        assert Decimal("0.01") < pfa < Decimal("0.05")

    def test_determinismo_replay_pfa(self) -> None:
        """ADR-0025 — chamadas identicas produzem resultado identico."""
        p = _params("105", "3")
        primeiro = calcular_pfa(p)
        for _ in range(20):
            assert calcular_pfa(p) == primeiro


class TestPRA:
    def test_pra_para_caso_identico_iguala_pfa_em_wave_a(self) -> None:
        """Wave A: aproximacao identica (V2 refina via Bayes prior)."""
        p = _params("100", "5")
        assert calcular_pra(p) == calcular_pfa(p)

    def test_validacao_sem_limites_recusa(self) -> None:
        with pytest.raises(ValueError, match="LSL OU USL"):
            ParametrosPFAPRA(
                valor_medido=Decimal("100"),
                U_expandida=Decimal("5"),
                k=Decimal("2"),
                lsl=None,
                usl=None,
            )

    def test_k_negativo_recusa(self) -> None:
        with pytest.raises(ValueError, match="k"):
            ParametrosPFAPRA(
                valor_medido=Decimal("100"),
                U_expandida=Decimal("5"),
                k=Decimal("-1"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
            )

    def test_U_negativa_recusa(self) -> None:
        with pytest.raises(ValueError, match="U_expandida"):
            ParametrosPFAPRA(
                valor_medido=Decimal("100"),
                U_expandida=Decimal("-1"),
                k=Decimal("2"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
            )
