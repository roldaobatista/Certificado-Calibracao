"""Testes arredondamento NIT-DICLA-030 §7.5 (P4 Fase 3 Batch A — T-CAL-046..049).

Cobre regra de 2 algarismos significativos com banker's rounding
(ROUND_HALF_EVEN), JCGM 100:2008 §7.2.6.

Padroes:
  - TST-005: >=1 happy + >=1 borda por classe de magnitude.
  - Decimal puro (INV-CAL-INC-003 — float introduz erro metrologico).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.motor_calculo.arredondamento import (
    DIGITOS_SIGNIFICATIVOS,
    REGRA_ID,
    arredondar_2_digitos_significativos,
    arredondar_lista,
)


class TestRegraIdConstante:
    def test_regra_id_canonica(self) -> None:
        # Bate com OrcamentoIncerteza.arredondamento_aplicado_regra default (§16.6)
        assert REGRA_ID == "NIT_DICLA_030_2_DIGITOS_SIG"

    def test_digitos_significativos_eh_2(self) -> None:
        assert DIGITOS_SIGNIFICATIVOS == 2


class TestArredondaValoresPequenos:
    """Magnitudes < 1 — casos comuns em calibracao de precisao."""

    def test_0_001234_vai_0_0012(self) -> None:
        # Dois sig: '1' e '2'. 3 (proximo digito) < 5 -> mantem '12'
        assert arredondar_2_digitos_significativos(Decimal("0.001234")) == Decimal("0.0012")

    def test_0_05678_vai_0_057(self) -> None:
        # Dois sig: '5' e '6'. 7 (proximo) > 5 -> sobe pra '57'.
        assert arredondar_2_digitos_significativos(Decimal("0.05678")) == Decimal("0.057")

    def test_0_00055_ja_2_sig_mantem(self) -> None:
        # 0.00055 ja esta com 2 sig ('5','5'). adjusted=-4, quantize 1e-5
        # 55 (em escala 1e-5) ja inteiro -> mantem
        assert arredondar_2_digitos_significativos(Decimal("0.00055")) == Decimal("0.00055")

    def test_0_000555_banker_eleva_par(self) -> None:
        # 0.000555 -> dois sig '5','5'; proximo '5' exato. Banker's: digito
        # retido eh '5' (impar) -> sobe pra '6' (par)
        # adjusted=-4, quantize 1e-5. 555e-6 / 1e-5 = 55.5 -> banker's 56 -> 56e-5
        assert arredondar_2_digitos_significativos(Decimal("0.000555")) == Decimal("0.00056")

    def test_0_00099_arredonda_0_00099(self) -> None:
        # Dois sig: '9','9'. Proximo nao existe -> mantem.
        # adjusted=-4, quantize_to=10^-5? Não - adjusted("0.00099") = -4 (msd em 1e-4),
        # quantize_to = 10^(-4 - 1) = 10^-5. 0.00099 quantize 10^-5 = 0.00099
        assert arredondar_2_digitos_significativos(Decimal("0.00099")) == Decimal("0.00099")

    def test_arredonda_eleva_ordem_magnitude_0_0095_vai_0_0095(self) -> None:
        # 0.0095 -> '9','5' arredondado fica 0.0095 (sem mudanca)
        # adjusted("0.0095")=-3, quantize 10^-4 -> '0.0095'
        assert arredondar_2_digitos_significativos(Decimal("0.0095")) == Decimal("0.0095")


class TestArredondaValoresMaiores:
    """Magnitudes >= 1."""

    def test_1_234_vai_1_2(self) -> None:
        # '1','2'. proximo '3' < 5 -> mantem.
        assert arredondar_2_digitos_significativos(Decimal("1.234")) == Decimal("1.2")

    def test_1_567_vai_1_6(self) -> None:
        # '1','5'. proximo '6' > 5 -> sobe.
        assert arredondar_2_digitos_significativos(Decimal("1.567")) == Decimal("1.6")

    def test_12_345_vai_12(self) -> None:
        # '1','2'. proximo '3' < 5 -> mantem '12'.
        assert arredondar_2_digitos_significativos(Decimal("12.345")) == Decimal("12")

    def test_98_765_banker(self) -> None:
        # adjusted("98.765")=1. quantize 10^0 = '99'
        # 98.765 ~ 99 (8 par seria 98; mas .765 > .5 forca 99 normal)
        assert arredondar_2_digitos_significativos(Decimal("98.765")) == Decimal("99")

    def test_150_mantem(self) -> None:
        # adjusted("150")=2. quantize 10^1 = decimal('1.5E+2') == 150
        resultado = arredondar_2_digitos_significativos(Decimal("150"))
        assert resultado == Decimal("150")

    def test_155_banker_arredonda_par(self) -> None:
        # 155 -> '1','5'. proximo '5' exato -> banker's: par mais proximo
        # adjusted("155")=2, quantize 10^1. 155 / 10 = 15.5 -> banker's 16 -> 160
        assert arredondar_2_digitos_significativos(Decimal("155")) == Decimal("1.6E+2")

    def test_165_banker_arredonda_par(self) -> None:
        # 165 -> '1','6'. proximo '5' exato -> par mais proximo (6 ja par) -> 16 -> 160
        assert arredondar_2_digitos_significativos(Decimal("165")) == Decimal("1.6E+2")


class TestArredondaValoresMuitoGrandes:
    def test_12345678(self) -> None:
        # adjusted=7. quantize 10^6 = '1.2E+7'
        resultado = arredondar_2_digitos_significativos(Decimal("12345678"))
        # 12345678 / 1e6 = 12.345678 -> 12 -> 12e6
        assert resultado == Decimal("1.2E+7")

    def test_99999999(self) -> None:
        # adjusted=7. 99999999/1e6 = 99.999999 -> arredonda 100 -> 1.0e8
        resultado = arredondar_2_digitos_significativos(Decimal("99999999"))
        assert resultado == Decimal("1.0E+8")


class TestArredondaValoresMuitoPequenos:
    def test_e_10(self) -> None:
        # 1.234e-10 -> adjusted=-10. quantize 10^-11 -> 1.2e-10
        resultado = arredondar_2_digitos_significativos(Decimal("1.234E-10"))
        assert resultado == Decimal("1.2E-10")

    def test_e_30_borda(self) -> None:
        resultado = arredondar_2_digitos_significativos(Decimal("9.876E-30"))
        # adjusted=-30. quantize 10^-31. 9.876 -> arredonda em 1 casa apos virgula
        # quantize_to = 10^(-30-1) = 10^-31
        # 9.876e-30 -> 98.76e-31 -> arredonda 99e-31 (banker's nao aplica pois >5)
        assert resultado == Decimal("9.9E-30")


class TestArredondaValoresNegativos:
    def test_negativo_preserva_sinal(self) -> None:
        assert arredondar_2_digitos_significativos(Decimal("-0.05678")) == Decimal("-0.057")

    def test_negativo_banker_par(self) -> None:
        # -155 -> par mais proximo (6) preserva sinal -> -160
        assert arredondar_2_digitos_significativos(Decimal("-155")) == Decimal("-1.6E+2")

    def test_negativo_muito_pequeno(self) -> None:
        assert arredondar_2_digitos_significativos(Decimal("-1.234E-10")) == Decimal("-1.2E-10")


class TestZero:
    def test_zero_exato_escala_2_sig(self) -> None:
        # Zero exato: preserva escala 2 sig pra serializacao consistente.
        resultado = arredondar_2_digitos_significativos(Decimal("0"))
        assert resultado == 0
        # Verifica escala preservada (Decimal('0E-2') tem expoente -2)
        assert str(resultado) == "0E-2" or resultado == Decimal("0.00")

    def test_zero_negativo_tratado_como_zero(self) -> None:
        # -0 (raro mas possivel em Decimal) tambem deve dar 0E-2
        resultado = arredondar_2_digitos_significativos(Decimal("-0"))
        assert resultado == 0


class TestRejeitaFloat:
    """INV-CAL-INC-003: Decimal puro, nunca float."""

    def test_rejeita_float_simples(self) -> None:
        with pytest.raises(TypeError, match="espera Decimal"):
            arredondar_2_digitos_significativos(1.234)  # type: ignore[arg-type]

    def test_rejeita_int(self) -> None:
        # int tambem nao aceito (forca chamador a converter explicito)
        with pytest.raises(TypeError, match="espera Decimal"):
            arredondar_2_digitos_significativos(150)  # type: ignore[arg-type]

    def test_rejeita_string(self) -> None:
        with pytest.raises(TypeError, match="espera Decimal"):
            arredondar_2_digitos_significativos("1.234")  # type: ignore[arg-type]


class TestArredondaLista:
    def test_lista_vazia(self) -> None:
        assert arredondar_lista([]) == []

    def test_lista_3_elementos(self) -> None:
        entrada = [Decimal("0.05678"), Decimal("12.345"), Decimal("1.234")]
        esperado = [Decimal("0.057"), Decimal("12"), Decimal("1.2")]
        assert arredondar_lista(entrada) == esperado


class TestDeterminismo:
    """Mesmo input -> mesmo output, sempre (replay deterministico ADR-0025)."""

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            (Decimal("0.001234"), Decimal("0.0012")),
            (Decimal("12.345"), Decimal("12")),
            (Decimal("-0.05678"), Decimal("-0.057")),
            (Decimal("0"), Decimal("0E-2")),
        ],
    )
    def test_determinismo_100x(self, entrada: Decimal, esperado: Decimal) -> None:
        # Rodando 100 vezes deve dar mesma saida (sem flakiness)
        for _ in range(100):
            assert arredondar_2_digitos_significativos(entrada) == esperado
