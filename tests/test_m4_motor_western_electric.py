"""Tests motor Western Electric (M4 P4 Fase 7 — T-CAL-118 dependencia).

P-CAL-R8 RBC + ISO 17025 cl. 7.7.1 — 4 regras classicas.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.motor_calculo.western_electric import (
    avaliar_regras_we,
)


def _dec_list(*vals: str) -> list[Decimal]:
    return [Decimal(v) for v in vals]


class TestRule1_3Sigma:
    def test_z_acima_3sigma_dispara(self) -> None:
        assert avaliar_regras_we(_dec_list("3.5")) == "RULE_1_3SIGMA"

    def test_z_abaixo_menos_3sigma_dispara(self) -> None:
        assert avaliar_regras_we(_dec_list("-3.5")) == "RULE_1_3SIGMA"

    def test_z_exato_3_nao_dispara(self) -> None:
        """3.0 exato eh borda — `abs(z) > 3` exclui o limite (sem caralha)."""
        assert avaliar_regras_we(_dec_list("3.0")) is None

    def test_dentro_de_3sigma_passa(self) -> None:
        assert avaliar_regras_we(_dec_list("0", "1", "-1", "2", "-2")) is None

    def test_uma_violacao_no_meio_dispara(self) -> None:
        assert (
            avaliar_regras_we(_dec_list("0", "1", "3.5", "2", "1"))
            == "RULE_1_3SIGMA"
        )


class TestRule5_TwoOfThree:
    def test_dois_de_tres_acima_2sigma_dispara(self) -> None:
        # Ultimos 3: [2.5, 1.0, 2.1] -> 2 acima de +2
        assert (
            avaliar_regras_we(_dec_list("0", "0", "2.5", "1.0", "2.1"))
            == "RULE_5_TWO_OF_THREE"
        )

    def test_dois_de_tres_abaixo_menos_2sigma_dispara(self) -> None:
        assert (
            avaliar_regras_we(_dec_list("0", "0", "-2.5", "-1.0", "-2.1"))
            == "RULE_5_TWO_OF_THREE"
        )

    def test_misturado_um_pos_um_neg_nao_dispara(self) -> None:
        """Regra 5 exige MESMO LADO — 1 pos + 1 neg nao conta."""
        assert avaliar_regras_we(_dec_list("0", "0", "2.5", "1.0", "-2.5")) is None

    def test_dois_de_tres_exato_2_nao_dispara(self) -> None:
        """`> 2.0` exclui o limite exato."""
        assert avaliar_regras_we(_dec_list("0", "0", "2.0", "1.0", "2.0")) is None


class TestRule2_SevenSameSide:
    def test_sete_positivos_consecutivos_dispara(self) -> None:
        zs = _dec_list("0.5", "1.0", "0.8", "1.2", "0.9", "1.1", "0.7")
        assert avaliar_regras_we(zs) == "RULE_2_SEVEN_SAME_SIDE"

    def test_sete_negativos_consecutivos_dispara(self) -> None:
        zs = _dec_list("-0.5", "-1.0", "-0.8", "-1.2", "-0.9", "-1.1", "-0.7")
        assert avaliar_regras_we(zs) == "RULE_2_SEVEN_SAME_SIDE"

    def test_seis_positivos_e_um_neg_no_meio_nao_dispara(self) -> None:
        zs = _dec_list("0.5", "1.0", "0.8", "-0.1", "0.9", "1.1", "0.7")
        assert avaliar_regras_we(zs) is None

    def test_zero_no_meio_nao_dispara(self) -> None:
        """Zero quebra a regra (`> 0` estrito)."""
        zs = _dec_list("0.5", "1.0", "0.8", "0", "0.9", "1.1", "0.7")
        assert avaliar_regras_we(zs) is None


class TestRule3_Trend:
    def test_seis_crescente_estrita_dispara(self) -> None:
        zs = _dec_list("0.1", "0.3", "0.5", "0.7", "0.9", "1.1")
        assert avaliar_regras_we(zs) == "RULE_3_TREND"

    def test_seis_decrescente_estrita_dispara(self) -> None:
        zs = _dec_list("1.0", "0.8", "0.5", "0.3", "0.0", "-0.5")
        assert avaliar_regras_we(zs) == "RULE_3_TREND"

    def test_cinco_pontos_nao_dispara(self) -> None:
        zs = _dec_list("0.1", "0.3", "0.5", "0.7", "0.9")
        assert avaliar_regras_we(zs) is None

    def test_tendencia_com_plato_nao_dispara(self) -> None:
        """Igualdade em qualquer par quebra tendencia ESTRITA."""
        zs = _dec_list("0.1", "0.3", "0.5", "0.5", "0.9", "1.1")
        assert avaliar_regras_we(zs) is None


class TestOrdem:
    def test_rule1_tem_prioridade_sobre_rule5(self) -> None:
        # Tem 2/3 acima de 2 sigma E 1 ponto acima de 3 sigma
        zs = _dec_list("0", "0", "2.5", "3.5", "2.1")
        # RULE_1 deve ganhar (avaliado primeiro)
        assert avaliar_regras_we(zs) == "RULE_1_3SIGMA"

    def test_rule5_tem_prioridade_sobre_rule2(self) -> None:
        # Tem 7 pos consecutivos E ultimos 3 com 2 acima de 2 sigma
        zs = _dec_list("0.5", "1.0", "0.8", "1.2", "2.5", "1.1", "2.1")
        # 7 pos consecutivos: ok; ultimos 3 = [2.5, 1.1, 2.1] -> RULE_5
        assert avaliar_regras_we(zs) == "RULE_5_TWO_OF_THREE"


class TestValidacoes:
    def test_lista_vazia_retorna_none(self) -> None:
        assert avaliar_regras_we([]) is None

    def test_um_elemento_so_avalia_rule1(self) -> None:
        assert avaliar_regras_we(_dec_list("0.5")) is None

    def test_float_recusa(self) -> None:
        with pytest.raises(TypeError, match="INV-CAL-INC-001"):
            avaliar_regras_we([Decimal("0.5"), 1.0])  # type: ignore[list-item]


class TestDeterminismo:
    def test_chamadas_repetidas_resultado_identico(self) -> None:
        zs = _dec_list("0.5", "1.0", "0.8", "1.2", "0.9", "1.1", "0.7")
        primeiro = avaliar_regras_we(zs)
        for _ in range(20):
            assert avaliar_regras_we(zs) == primeiro
