"""Testes validacao replay (P4 Fase 3 Batch D — T-CAL-059..060).

Cobre comparacao algoritmo_1 (GUM) vs algoritmo_2 (Monte Carlo) com
classificacao em 3 zonas (§16.5 spec + ADR-0025).

Padroes:
  - TST-005: >=1 happy + >=1 borda por zona.
  - Decimal puro (INV-CAL-INC-003).
  - Deterministico (ADR-0025).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.motor_calculo.gum_classico import ResultadoGUM
from src.domain.metrologia.calibracao.motor_calculo.validacao_replay import (
    LIMITE_ALERTA_PCT,
    LIMITE_SILENCIOSO_PCT,
    ClassificacaoDivergencia,
    DivergenciaCalculoInaceitavel,
    ResultadoMC,
    comparar_algoritmos,
)


def _criar_gum(U: Decimal) -> ResultadoGUM:  # - U canonico
    return ResultadoGUM(
        u_combinada=U / Decimal("2"),
        grau_liberdade_efetivo=None,
        fator_k=Decimal("2.000"),
        U_expandida=U,
    )


def _criar_mc(U: Decimal) -> ResultadoMC:  # - U canonico
    return ResultadoMC(
        u_combinada=U / Decimal("2"),
        U_expandida=U,
        nivel_confianca=Decimal("0.9545"),
        n_iteracoes=1_000_000,
        seed=12345,
    )


# =====================================================================
# Zona SILENCIOSO (<= 0.1%)
# =====================================================================


class TestZonaSilencioso:
    def test_divergencia_zero(self) -> None:
        gum = _criar_gum(Decimal("0.0100"))
        mc = _criar_mc(Decimal("0.0100"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div == 0
        assert classe == ClassificacaoDivergencia.SILENCIOSO

    def test_divergencia_0_05_pct(self) -> None:
        # 0.01000 vs 0.01005 -> 0.5% — espera ALERTA_P3 nao SILENCIOSO
        # Vou usar 0.01000 vs 0.010005 -> 0.05% silencioso
        gum = _criar_gum(Decimal("0.010000"))
        mc = _criar_mc(Decimal("0.010005"))
        div, classe = comparar_algoritmos(gum, mc)
        # diff_abs=0.000005, U_gum=0.01, div=0.05%
        assert div == Decimal("0.05000")
        assert classe == ClassificacaoDivergencia.SILENCIOSO

    def test_borda_exata_0_1_pct(self) -> None:
        # 0.01 vs 0.01001 -> 0.1% exato (borda — ainda SILENCIOSO)
        gum = _criar_gum(Decimal("0.01000"))
        mc = _criar_mc(Decimal("0.01001"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div == Decimal("0.10000")
        assert classe == ClassificacaoDivergencia.SILENCIOSO

    def test_divergencia_negativa_simetrica(self) -> None:
        # MC < GUM tambem entra em SILENCIOSO (usa abs)
        gum = _criar_gum(Decimal("0.010005"))
        mc = _criar_mc(Decimal("0.010000"))
        div, classe = comparar_algoritmos(gum, mc)
        assert classe == ClassificacaoDivergencia.SILENCIOSO


# =====================================================================
# Zona ALERTA_P3 (0.1% < x <= 1%)
# =====================================================================


class TestZonaAlertaP3:
    def test_divergencia_0_5_pct(self) -> None:
        # 0.01 vs 0.01005 -> 0.5%
        gum = _criar_gum(Decimal("0.01000"))
        mc = _criar_mc(Decimal("0.01005"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div == Decimal("0.50000")
        assert classe == ClassificacaoDivergencia.ALERTA_P3

    def test_borda_exata_1_pct(self) -> None:
        # 0.01 vs 0.0101 -> 1% exato (borda superior — ainda ALERTA_P3)
        gum = _criar_gum(Decimal("0.01000"))
        mc = _criar_mc(Decimal("0.01010"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div == Decimal("1.0000")
        assert classe == ClassificacaoDivergencia.ALERTA_P3

    def test_borda_logo_acima_0_1(self) -> None:
        # 0.10001% -> ALERTA_P3 (acima do limite SILENCIOSO)
        gum = _criar_gum(Decimal("100.00000"))  # U_gum grande pra precisao
        mc = _criar_mc(Decimal("100.10001"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div > LIMITE_SILENCIOSO_PCT
        assert classe == ClassificacaoDivergencia.ALERTA_P3


# =====================================================================
# Zona INACEITAVEL (> 1%) -> levanta excecao
# =====================================================================


class TestZonaInaceitavel:
    def test_divergencia_2_pct_levanta(self) -> None:
        gum = _criar_gum(Decimal("0.01000"))
        mc = _criar_mc(Decimal("0.01020"))  # 2% diff
        with pytest.raises(DivergenciaCalculoInaceitavel) as exc:
            comparar_algoritmos(gum, mc)
        assert exc.value.divergencia_pct == Decimal("2.0000")
        assert exc.value.U_gum == Decimal("0.01000")
        assert exc.value.U_mc == Decimal("0.01020")

    def test_divergencia_5_pct_levanta(self) -> None:
        gum = _criar_gum(Decimal("0.01"))
        mc = _criar_mc(Decimal("0.0105"))  # 5% diff
        with pytest.raises(DivergenciaCalculoInaceitavel):
            comparar_algoritmos(gum, mc)

    def test_borda_logo_acima_1_pct_levanta(self) -> None:
        # 1.01% -> INACEITAVEL
        gum = _criar_gum(Decimal("100.00"))
        mc = _criar_mc(Decimal("101.01"))  # 1.01% diff
        with pytest.raises(DivergenciaCalculoInaceitavel):
            comparar_algoritmos(gum, mc)


# =====================================================================
# Caso especial: U_gum == 0 (calibracao descritiva)
# =====================================================================


class TestCalibracaoDescritiva:
    def test_ambos_zero_silencioso(self) -> None:
        gum = _criar_gum(Decimal("0"))
        mc = _criar_mc(Decimal("0"))
        div, classe = comparar_algoritmos(gum, mc)
        assert div == 0
        assert classe == ClassificacaoDivergencia.SILENCIOSO

    def test_gum_zero_mc_diferente_inaceitavel(self) -> None:
        # GUM == 0 mas MC != 0: discordancia estrutural -> INACEITAVEL
        gum = _criar_gum(Decimal("0"))
        mc = _criar_mc(Decimal("0.01"))
        with pytest.raises(DivergenciaCalculoInaceitavel):
            comparar_algoritmos(gum, mc)


# =====================================================================
# Determinismo (replay ADR-0025)
# =====================================================================


class TestDeterminismo:
    def test_mesmo_input_mesma_classificacao_100x(self) -> None:
        gum = _criar_gum(Decimal("0.01000"))
        mc = _criar_mc(Decimal("0.01005"))
        primeiro = comparar_algoritmos(gum, mc)
        for _ in range(100):
            assert comparar_algoritmos(gum, mc) == primeiro


# =====================================================================
# Sanity das constantes
# =====================================================================


def test_limites_publicos_consistentes_com_spec() -> None:
    # §16.5 spec — limites canonicos
    assert LIMITE_SILENCIOSO_PCT == Decimal("0.1")
    assert LIMITE_ALERTA_PCT == Decimal("1.0")


def test_excecao_carrega_payload_diagnostico() -> None:
    gum = _criar_gum(Decimal("0.01"))
    mc = _criar_mc(Decimal("0.02"))  # 100% diff
    with pytest.raises(DivergenciaCalculoInaceitavel) as exc:
        comparar_algoritmos(gum, mc)
    # str() inclui valores pra log/diagnostico
    msg = str(exc.value)
    assert "GUM=0.01" in msg
    assert "MC=0.02" in msg


def test_resultado_mc_frozen() -> None:
    from dataclasses import FrozenInstanceError

    mc = ResultadoMC(
        u_combinada=Decimal("0.005"),
        U_expandida=Decimal("0.01"),
        nivel_confianca=Decimal("0.9545"),
        n_iteracoes=1_000_000,
        seed=42,
    )
    with pytest.raises(FrozenInstanceError):
        mc.U_expandida = Decimal("999")  # type: ignore[misc]
