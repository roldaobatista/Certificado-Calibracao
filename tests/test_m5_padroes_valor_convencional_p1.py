# ruff: noqa: RUF001, RUF002, RUF003 — simbolos gregos canonicos na notacao GUM
"""Testes do 2º caminho de cálculo do valor convencional — P1 (T-PAD-005, ADR-0071).

Verificacao de software (2 implementacoes do MESMO mensurando convergem) +
media ponderada por inversa da variancia + Welch-Satterthwaite + k t-Student.
Puro, sem DB. Valores conferidos a mao.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.padroes.valor_convencional import (
    CertHistorico,
    calcular,
)


def _cert(valor: str, u: str, nu: int | None) -> CertHistorico:
    return CertHistorico(Decimal(valor), Decimal(u), nu)


class TestMediaPonderada:
    def test_cert_unico_retorna_o_proprio_valor(self) -> None:
        r = calcular([_cert("100.0", "0.1", None)])
        assert r.valor_convencional == Decimal("100.0")
        assert r.u_combinada == Decimal("0.1")
        assert r.n_certificados == 1

    def test_media_ponderada_dois_certs(self) -> None:
        # A: 100.0 u=0.1 (w=100) ; B: 100.2 u=0.2 (w=25) ; Σw=125
        # x̄ = (100*100 + 100.2*25)/125 = 12505/125 = 100.04
        r = calcular([_cert("100.0", "0.1", None), _cert("100.2", "0.2", None)])
        assert r.valor_convencional == Decimal("100.04")
        # u_c = sqrt(1/125)
        assert r.u_combinada == (Decimal("1") / Decimal("125")).sqrt()

    def test_pesos_iguais_media_simples(self) -> None:
        r = calcular([_cert("10", "0.5", None), _cert("12", "0.5", None)])
        assert r.valor_convencional == Decimal("11")


class TestIncertezaEK:
    def test_todos_infinitos_k2(self) -> None:
        r = calcular([_cert("5", "0.1", None), _cert("5", "0.1", None)])
        assert r.graus_liberdade_efetivos is None
        assert r.k == Decimal("2.000")

    def test_cert_unico_nu4_k_tstudent(self) -> None:
        # single cert ν=4 -> ν_eff=4 -> k = fator_k_para_95(4) = 2.869 (tabela GUM)
        r = calcular([_cert("100", "0.1", 4)])
        assert r.graus_liberdade_efetivos == 4
        assert r.k == Decimal("2.869")
        assert r.U_expandida == Decimal("2.869") * Decimal("0.1")

    def test_U_igual_k_vezes_uc(self) -> None:
        r = calcular([_cert("100.0", "0.1", None), _cert("100.2", "0.2", None)])
        assert r.U_expandida == r.k * r.u_combinada


class TestVerificacaoSoftware:
    def test_implementacoes_convergem_varios_inputs(self) -> None:
        # As 2 implementacoes sao algebricamente iguais -> calcular() NAO levanta.
        casos = [
            [_cert("100", "0.1", None)],
            [_cert("1.5", "0.01", 9), _cert("1.52", "0.02", 5)],
            [_cert("0.333", "0.001", None), _cert("0.334", "0.002", 30), _cert("0.332", "0.0015", 12)],
        ]
        for certs in casos:
            r = calcular(certs)  # nao levanta DivergenciaImplementacoesError
            assert r.valor_convencional > 0


class TestValidacoes:
    def test_lista_vazia_rejeita(self) -> None:
        with pytest.raises(ValueError, match=">= 1 certificado"):
            calcular([])

    def test_u_padrao_zero_rejeita(self) -> None:
        with pytest.raises(ValueError, match="u_padrao deve ser > 0"):
            _cert("100", "0", None)

    def test_u_padrao_negativo_rejeita(self) -> None:
        with pytest.raises(ValueError, match="u_padrao deve ser > 0"):
            _cert("100", "-0.1", None)

    def test_nu_zero_rejeita(self) -> None:
        with pytest.raises(ValueError, match="graus_liberdade < 1"):
            _cert("100", "0.1", 0)

    def test_float_rejeita(self) -> None:
        with pytest.raises(TypeError, match="Decimal"):
            CertHistorico(100.0, Decimal("0.1"), None)  # type: ignore[arg-type]
