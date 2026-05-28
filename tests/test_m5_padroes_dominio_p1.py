# ruff: noqa: RUF001, RUF002, RUF003 — simbolo grego canonico (σ = sigma) na notacao estatistica
"""Testes do dominio puro M5 padroes — P1 (T-PAD-001/004).

Enums + carta Shewhart (Western Electric). Puro, sem DB.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    DecisaoRTCarta,
    EstadoPadrao,
    RegraWesternElectric,
    ResultadoPT,
    ResultadoVI,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.padroes.shewhart import (
    LimitesControle,
    calcular_limites,
    detectar_violacoes,
)


class TestEnums:
    def test_estado_terminal_so_sucateado(self) -> None:
        assert EstadoPadrao.SUCATEADO.terminal is True
        assert EstadoPadrao.BAIXADO.terminal is False

    def test_so_em_uso_permite_calibracao(self) -> None:
        assert EstadoPadrao.EM_USO.permite_uso_em_calibracao is True
        for e in EstadoPadrao:
            if e != EstadoPadrao.EM_USO:
                assert e.permite_uso_em_calibracao is False

    def test_recal_retornado_pendente_nao_permite_uso(self) -> None:
        # C-4 FURO-1: voltou do lab mas pendente aprovacao RT -> bloqueado.
        assert (
            EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO.permite_uso_em_calibracao
            is False
        )

    def test_rbc_exige_perfil_a(self) -> None:
        assert VinculacaoCadeia.RBC.exige_perfil_a is True
        assert VinculacaoCadeia.INMETRO.exige_perfil_a is False

    def test_subtipo_auxiliar(self) -> None:
        assert SubtipoPadrao.AUXILIAR_AMBIENTAL.eh_auxiliar is True
        assert SubtipoPadrao.PRINCIPAL.eh_auxiliar is False

    def test_vi_reprovada_bloqueia(self) -> None:
        assert ResultadoVI.REPROVADO.bloqueia_uso is True
        assert ResultadoVI.APROVADO.bloqueia_uso is False

    def test_pt_rejeitado_bloqueia(self) -> None:
        assert ResultadoPT.REJEITADO.bloqueia_uso is True

    def test_classe_tem_oiml(self) -> None:
        assert ClassePadrao.E1.value == "E1"

    def test_decisao_rt_so_aceito_libera(self) -> None:
        assert DecisaoRTCarta.ACEITO_COM_JUSTIFICATIVA.libera_uso is True
        assert DecisaoRTCarta.RECALIBRAR.libera_uso is False
        assert DecisaoRTCarta.SUSPENDER_USO.libera_uso is False


# Limites canonicos pra isolar a logica de regra (LC=0, σ=1 -> ±1σ=±1, ±2σ=±2, ±3σ=±3).
_LIM = LimitesControle(
    linha_central=Decimal("0"),
    sigma=Decimal("1"),
    ucl=Decimal("3"),
    lcl=Decimal("-3"),
    n_pontos=10,
)


def _regras(pontos: list[str]) -> set[RegraWesternElectric]:
    viol = detectar_violacoes([Decimal(p) for p in pontos], _LIM)
    return {v.regra for v in viol}


class TestCalcularLimites:
    def test_lc_e_sigma_amostral(self) -> None:
        lim = calcular_limites([Decimal("2"), Decimal("4")])
        assert lim.linha_central == Decimal("3")
        # var = ((2-3)^2+(4-3)^2)/(2-1) = 2 ; sigma = sqrt(2)
        assert lim.sigma == Decimal("2").sqrt()
        assert lim.ucl == Decimal("3") + Decimal("3") * Decimal("2").sqrt()
        assert lim.lcl == Decimal("3") - Decimal("3") * Decimal("2").sqrt()

    def test_menos_de_2_pontos_rejeita(self) -> None:
        with pytest.raises(ValueError, match=">= 2 pontos"):
            calcular_limites([Decimal("5")])

    def test_float_rejeitado(self) -> None:
        with pytest.raises(TypeError, match="Decimal"):
            calcular_limites([Decimal("1"), 2.0])  # type: ignore[list-item]


class TestRegra1:
    def test_ponto_fora_3sigma_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_1_FORA_3SIGMA in _regras(["0", "0", "4", "0"])

    def test_dentro_3sigma_nao_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_1_FORA_3SIGMA not in _regras(["0", "2", "0"])


class TestRegra2MesmoLado:
    def test_2de3_acima_2sigma_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_2_2DE3_2SIGMA in _regras(["0", "2.5", "2.5"])

    def test_2de3_lados_opostos_NAO_dispara(self) -> None:
        # C-3: sem 'mesmo lado' isto seria falso-positivo. Deve NAO disparar.
        regras = _regras(["2.5", "-2.5", "0.5"])
        assert RegraWesternElectric.REGRA_2_2DE3_2SIGMA not in regras


class TestRegra3MesmoLado:
    def test_4de5_acima_1sigma_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_3_4DE5_1SIGMA in _regras(
            ["1.5", "1.5", "1.5", "0", "1.5"]
        )

    def test_4de5_lados_opostos_NAO_dispara(self) -> None:
        regras = _regras(["1.5", "1.5", "-1.5", "-1.5", "0"])
        assert RegraWesternElectric.REGRA_3_4DE5_1SIGMA not in regras


class TestRegra4Run8:
    def test_8_mesmo_lado_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_4_RUN_8 in _regras(["0.1"] * 8)

    def test_7_mesmo_lado_NAO_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_4_RUN_8 not in _regras(["0.1"] * 7)


class TestRegra5Tendencia:
    def test_7_crescente_dispara(self) -> None:
        # Dentro de ±1σ pra isolar de R1/R3; cruza LC pra evitar R4.
        assert RegraWesternElectric.REGRA_5_TENDENCIA_7 in _regras(
            ["-0.6", "-0.4", "-0.2", "0", "0.2", "0.4", "0.6"]
        )

    def test_7_decrescente_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_5_TENDENCIA_7 in _regras(
            ["0.6", "0.4", "0.2", "0", "-0.2", "-0.4", "-0.6"]
        )

    def test_nao_monotonico_NAO_dispara(self) -> None:
        assert RegraWesternElectric.REGRA_5_TENDENCIA_7 not in _regras(
            ["-0.6", "-0.4", "-0.5", "0", "0.2", "0.4", "0.6"]
        )


class TestSigmaZero:
    def test_pontos_iguais_sem_regra_sigma_mas_run_e_trend_valem(self) -> None:
        # sigma=0: R1/R2/R3 nao disparam; mas 8 iguais acima de LC dispara R4.
        lim_zero = LimitesControle(
            linha_central=Decimal("-1"),  # LC abaixo dos pontos
            sigma=Decimal("0"),
            ucl=Decimal("-1"),
            lcl=Decimal("-1"),
            n_pontos=8,
        )
        viol = detectar_violacoes([Decimal("0")] * 8, lim_zero)
        regras = {v.regra for v in viol}
        assert RegraWesternElectric.REGRA_4_RUN_8 in regras
        assert RegraWesternElectric.REGRA_1_FORA_3SIGMA not in regras
