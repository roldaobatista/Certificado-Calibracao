"""VOs CNPJ + CPF — testes (Wave A · clientes · Marco 1).

CNPJ alfanumerico (ADR-0017, IN RFB 2.229/2024 vigencia jul/2026):
- Aceita 12 chars alfanumericos [A-Z0-9] + 2 digitos verificadores.
- Retrocompativel: CNPJ numerico antigo continua valido.

CPF: 11 digitos com algoritmo Receita.
"""

from __future__ import annotations

import pytest

from src.domain.shared.value_objects import CNPJ, CPF


# ============================================================================
# CNPJ — vetores oficiais + edge cases
# ============================================================================


class TestCNPJNumerico:
    """CNPJ antigo (so digitos) — retrocompativel pos IN RFB 2.229/2024."""

    @pytest.mark.parametrize(
        "valor",
        [
            "11222333000181",  # CNPJ real Petrobras (exemplo publico)
            "33000167000101",  # CNPJ real Banco do Brasil (exemplo publico)
            "11.222.333/0001-81",  # com pontuacao
        ],
    )
    def test_inv_036_cnpj_numerico_valido(self, valor: str) -> None:
        cnpj = CNPJ(valor)
        assert cnpj.value == "11222333000181" or cnpj.value == "33000167000101"
        assert cnpj.e_alfanumerico is False

    def test_inv_036_cnpj_dv_errado_rejeita(self) -> None:
        with pytest.raises(ValueError, match="DV invalido"):
            CNPJ("11222333000182")  # ultimo digito trocado

    def test_inv_036_cnpj_formato_curto_rejeita(self) -> None:
        with pytest.raises(ValueError, match="formato invalido"):
            CNPJ("123")

    def test_inv_036_cnpj_sequencia_trivial_rejeita(self) -> None:
        # 14 digitos iguais passariam DV mas nao sao CNPJ reais
        with pytest.raises(ValueError, match="sequencia trivial"):
            CNPJ("11111111111111")


class TestCNPJAlfanumerico:
    """CNPJ pos IN RFB 2.229/2024 — letras nas 12 primeiras posicoes."""

    def test_inv_036_cnpj_alfanumerico_valido_serpro_oficial(self) -> None:
        """Vetor de teste oficial Serpro (IN RFB 2.229/2024 anexo).

        Algoritmo: cada char vale ord(c)-48; DV por modulo 11 padrao.
        '12ABC34501DE' (12 chars) + DV calculado.
        """
        # Calculamos DV pra esse vetor pra cravar o algoritmo no teste.
        # Posicoes ord(c)-48: 1,2,17,18,19,3,4,5,0,1,20,21
        # Pesos DV1: [5,4,3,2,9,8,7,6,5,4,3,2]
        # Soma DV1: 1*5+2*4+17*3+18*2+19*9+3*8+4*7+5*6+0*5+1*4+20*3+21*2
        #         = 5+8+51+36+171+24+28+30+0+4+60+42 = 459
        # 459 % 11 = 8 -> DV1 = 11-8 = 3
        # Pesos DV2: [6,5,4,3,2,9,8,7,6,5,4,3,2]
        # Soma DV2: 1*6+2*5+17*4+18*3+19*2+3*9+4*8+5*7+0*6+1*5+20*4+21*3+3*2
        #         = 6+10+68+54+38+27+32+35+0+5+80+63+6 = 424
        # 424 % 11 = 6 -> DV2 = 11-6 = 5
        cnpj_str = "12ABC34501DE35"
        cnpj = CNPJ(cnpj_str)
        assert cnpj.value == "12ABC34501DE35"
        assert cnpj.e_alfanumerico is True

    def test_inv_036_cnpj_alfanumerico_dv_errado_rejeita(self) -> None:
        with pytest.raises(ValueError, match="DV invalido"):
            CNPJ("12ABC34501DE99")

    def test_inv_036_cnpj_aceita_pontuacao_alfanumerico(self) -> None:
        # Mesmo conteudo, separadores comuns
        cnpj = CNPJ("12.ABC.345/01DE-35")
        assert cnpj.value == "12ABC34501DE35"

    def test_inv_036_cnpj_letra_minuscula_normaliza_pra_maiuscula(self) -> None:
        cnpj = CNPJ("12abc34501de35")
        assert cnpj.value == "12ABC34501DE35"

    def test_inv_036_cnpj_dv_alfanumerico_no_dv_rejeita(self) -> None:
        # DVs precisam ser DIGITOS (regex [0-9]{2}), nao letras
        with pytest.raises(ValueError, match="formato invalido"):
            CNPJ("12ABC34501DEAB")


class TestCNPJFormatado:
    def test_formatacao_canonica(self) -> None:
        cnpj = CNPJ("11222333000181")
        assert cnpj.formatado() == "11.222.333/0001-81"

    def test_formatacao_alfanumerico(self) -> None:
        cnpj = CNPJ("12ABC34501DE35")
        assert cnpj.formatado() == "12.ABC.345/01DE-35"


# ============================================================================
# CPF — vetores + edge
# ============================================================================


class TestCPF:
    @pytest.mark.parametrize(
        "valor",
        [
            "52998224725",  # CPF valido publico (gerado)
            "529.982.247-25",
            "529 982 247 25",
        ],
    )
    def test_cpf_valido(self, valor: str) -> None:
        cpf = CPF(valor)
        assert cpf.value == "52998224725"

    def test_cpf_dv_errado_rejeita(self) -> None:
        with pytest.raises(ValueError, match="DV invalido"):
            CPF("52998224726")

    def test_cpf_formato_curto_rejeita(self) -> None:
        with pytest.raises(ValueError, match="formato invalido"):
            CPF("123")

    def test_cpf_sequencia_trivial_rejeita(self) -> None:
        with pytest.raises(ValueError, match="sequencia trivial"):
            CPF("11111111111")

    def test_cpf_letras_no_meio_rejeita(self) -> None:
        with pytest.raises(ValueError, match="formato invalido"):
            CPF("529.A82.247-25")

    def test_cpf_formatado(self) -> None:
        cpf = CPF("52998224725")
        assert cpf.formatado() == "529.982.247-25"
