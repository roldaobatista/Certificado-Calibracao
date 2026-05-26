"""Testes motor de decisao ILAC G8 (P4 Fase 5 Batch G — T-CAL-086).

Cobre todas as 7 zonas (6 ILAC G8 + NA) atraves de cenarios bem-definidos
+ as 3 regras de decisao (ACEITACAO_SIMPLES / BANDA_GUARDA_30 /
RISCO_COMPARTILHADO).

Geometria de teste:
  Especificacao padrao: LSL = 90, USL = 110 (faixa 90-110).
  Variando valor_medido + U_expandida atraves dos casos de fronteira.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.enums import RegraDecisao
from src.domain.metrologia.calibracao.motor_calculo.decisao_ilac import (
    BANDA_GUARDA_PCT,
    EntradaAvaliacao,
    classificar_zona_ilac_g8,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8


def _entrada(
    valor: str,
    U: str,
    lsl: str | None = "90",
    usl: str | None = "110",
    regra: RegraDecisao = RegraDecisao.ACEITACAO_SIMPLES,
) -> EntradaAvaliacao:
    return EntradaAvaliacao(
        valor_medido=Decimal(valor),
        U_expandida=Decimal(U),
        lsl=Decimal(lsl) if lsl is not None else None,
        usl=Decimal(usl) if usl is not None else None,
        regra=regra,
    )


# =====================================================================
# Calibracao descritiva: sem limites -> NA (cl. 7.8.6)
# =====================================================================


class TestCalibracaoDescritivaNA:
    def test_sem_limites_retorna_na(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("100.0", "1.0", lsl=None, usl=None))
        assert zona == ZonaILACG8.NA

    def test_sem_limites_com_banda_guarda_tambem_retorna_na(self) -> None:
        zona = classificar_zona_ilac_g8(
            _entrada(
                "100.0", "1.0", lsl=None, usl=None, regra=RegraDecisao.BANDA_GUARDA_30
            )
        )
        assert zona == ZonaILACG8.NA


# =====================================================================
# ACEITACAO_SIMPLES — 4 zonas: PASS / CONDITIONAL_PASS / CONDITIONAL_FAIL / FAIL
# =====================================================================


class TestAceitacaoSimples:
    def test_pass_intervalo_inteiramente_dentro(self) -> None:
        # 100 +- 5: [95, 105] dentro de [90, 110]
        zona = classificar_zona_ilac_g8(_entrada("100", "5"))
        assert zona == ZonaILACG8.PASS

    def test_conditional_pass_valor_dentro_intervalo_cruza_limite(self) -> None:
        # 108 +- 5: valor 108 dentro [90,110], mas [103, 113] cruza USL=110
        zona = classificar_zona_ilac_g8(_entrada("108", "5"))
        assert zona == ZonaILACG8.CONDITIONAL_PASS

    def test_conditional_fail_valor_fora_intervalo_cruza_limite(self) -> None:
        # 113 +- 5: valor 113 fora [90,110], mas [108, 118] cruza USL=110
        zona = classificar_zona_ilac_g8(_entrada("113", "5"))
        assert zona == ZonaILACG8.CONDITIONAL_FAIL

    def test_fail_intervalo_inteiramente_fora_acima(self) -> None:
        # 120 +- 5: [115, 125] totalmente acima de USL=110
        zona = classificar_zona_ilac_g8(_entrada("120", "5"))
        assert zona == ZonaILACG8.FAIL

    def test_fail_intervalo_inteiramente_fora_abaixo(self) -> None:
        # 80 +- 5: [75, 85] totalmente abaixo de LSL=90
        zona = classificar_zona_ilac_g8(_entrada("80", "5"))
        assert zona == ZonaILACG8.FAIL

    def test_pass_no_limite_exato(self) -> None:
        # 100 +- 10: [90, 110] coincide com [LSL, USL] — PASS (borda)
        zona = classificar_zona_ilac_g8(_entrada("100", "10"))
        assert zona == ZonaILACG8.PASS


# =====================================================================
# BANDA_GUARDA_30 — 6 zonas: PASS / PASS_COM_RESSALVA / CONDITIONAL_PASS /
#                            CONDITIONAL_FAIL / FAIL_COM_RESSALVA / FAIL
# =====================================================================


class TestBandaGuarda30:
    REGRA = RegraDecisao.BANDA_GUARDA_30

    def test_pass_dentro_da_banda_de_guarda(self) -> None:
        # U=2 -> guarda=0.6; banda efetiva [90.6, 109.4]
        # 100 +- 2: [98, 102] totalmente dentro de [90.6, 109.4] => PASS
        zona = classificar_zona_ilac_g8(_entrada("100", "2", regra=self.REGRA))
        assert zona == ZonaILACG8.PASS

    def test_pass_com_ressalva_dentro_limites_fora_guarda(self) -> None:
        # U=1 -> guarda=0.30; USL_eff=109.70; LSL_eff=90.30.
        # 109 +- 1: [108, 110] — totalmente dentro de [90, 110] (110<=110)
        # mas superior=110 > USL_eff=109.70 -> banda de guarda violada
        # -> PASS_COM_RESSALVA.
        zona = classificar_zona_ilac_g8(_entrada("109", "1", regra=self.REGRA))
        assert zona == ZonaILACG8.PASS_COM_RESSALVA

    def test_conditional_pass_valor_dentro_intervalo_cruza_limite_externo(
        self,
    ) -> None:
        # 109 +- 2: [107, 111] cruza USL=110, valor 109 dentro -> CONDITIONAL_PASS
        zona = classificar_zona_ilac_g8(_entrada("109", "2", regra=self.REGRA))
        assert zona == ZonaILACG8.CONDITIONAL_PASS

    def test_fail_com_ressalva_valor_fora_intervalo_cruza(self) -> None:
        # 111 +- 2: [109, 113] cruza USL=110; valor 111 fora [90,110] ->
        # FAIL_COM_RESSALVA (PFA alto)
        zona = classificar_zona_ilac_g8(_entrada("111", "2", regra=self.REGRA))
        assert zona == ZonaILACG8.FAIL_COM_RESSALVA

    def test_fail_intervalo_inteiramente_fora(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("120", "5", regra=self.REGRA))
        assert zona == ZonaILACG8.FAIL


# =====================================================================
# RISCO_COMPARTILHADO — mesma classificacao que ACEITACAO_SIMPLES
# =====================================================================


class TestRiscoCompartilhado:
    REGRA = RegraDecisao.RISCO_COMPARTILHADO

    def test_pass(self) -> None:
        assert classificar_zona_ilac_g8(_entrada("100", "5", regra=self.REGRA)) == (
            ZonaILACG8.PASS
        )

    def test_fail(self) -> None:
        assert classificar_zona_ilac_g8(_entrada("80", "5", regra=self.REGRA)) == (
            ZonaILACG8.FAIL
        )


# =====================================================================
# Limites one-sided (so LSL ou so USL)
# =====================================================================


class TestLimitesOneSided:
    def test_so_usl_pass_intervalo_abaixo(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("100", "5", lsl=None, usl="110"))
        assert zona == ZonaILACG8.PASS

    def test_so_usl_fail_intervalo_acima(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("120", "5", lsl=None, usl="110"))
        assert zona == ZonaILACG8.FAIL

    def test_so_lsl_pass(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("100", "5", lsl="90", usl=None))
        assert zona == ZonaILACG8.PASS

    def test_so_lsl_fail(self) -> None:
        zona = classificar_zona_ilac_g8(_entrada("80", "5", lsl="90", usl=None))
        assert zona == ZonaILACG8.FAIL


# =====================================================================
# Validacoes de entrada
# =====================================================================


class TestValidacoesEntrada:
    def test_lsl_maior_que_usl_recusa(self) -> None:
        with pytest.raises(ValueError, match="limites invertidos"):
            EntradaAvaliacao(
                valor_medido=Decimal("100"),
                U_expandida=Decimal("5"),
                lsl=Decimal("110"),
                usl=Decimal("90"),
                regra=RegraDecisao.ACEITACAO_SIMPLES,
            )

    def test_U_negativa_recusa(self) -> None:
        with pytest.raises(ValueError, match="U_expandida"):
            EntradaAvaliacao(
                valor_medido=Decimal("100"),
                U_expandida=Decimal("-1"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
                regra=RegraDecisao.ACEITACAO_SIMPLES,
            )

    def test_valor_medido_nao_decimal_recusa(self) -> None:
        with pytest.raises(TypeError, match="valor_medido"):
            EntradaAvaliacao(
                valor_medido=100.0,  # type: ignore[arg-type]
                U_expandida=Decimal("5"),
                lsl=Decimal("90"),
                usl=Decimal("110"),
                regra=RegraDecisao.ACEITACAO_SIMPLES,
            )


# =====================================================================
# Determinismo — replay bit-a-bit
# =====================================================================


def test_determinismo_replay_50_chamadas() -> None:
    """ADR-0025 cl. 7.11 + INV-CAL-INC-001: chamadas identicas produzem
    resultado identico bit-a-bit (Decimal puro)."""
    entrada = _entrada("100.123456", "2.345678", regra=RegraDecisao.BANDA_GUARDA_30)
    primeiro = classificar_zona_ilac_g8(entrada)
    for _ in range(50):
        assert classificar_zona_ilac_g8(entrada) == primeiro


def test_banda_guarda_pct_constante() -> None:
    """ADR-0024 fixa 30% — qualquer mudanca quebra replay 25a."""
    assert BANDA_GUARDA_PCT == Decimal("0.30")
