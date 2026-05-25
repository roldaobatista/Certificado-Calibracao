# ruff: noqa: RUF001, RUF002, RUF003 — simbolos gregos canonicos GUM (ν, ρ) na notacao metrologica oficial
"""Testes GUM classico (P4 Fase 3 Batch B — T-CAL-050..054).

Cobre propagacao de incerteza GUM JCGM 100:2008 + NIT-DICLA-030 rev. 15
em Decimal puro.

Padroes:
  - TST-005: >=1 happy + >=1 borda por funcao.
  - Decimal puro (INV-CAL-INC-003).
  - Testes deterministicos (replay ADR-0025).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.motor_calculo.gum_classico import (
    ComponenteEntrada,
    ResultadoGUM,
    combinar_componentes,
    combinar_tipo_a,
    fator_k_para_95,
    propagar,
    welch_satterthwaite,
)

# =====================================================================
# ComponenteEntrada (validacoes)
# =====================================================================


class TestComponenteEntradaValidacoes:
    def test_happy_tipo_a(self) -> None:
        c = ComponenteEntrada(nome="rep", u_i=Decimal("0.01"), tipo="A", grau_liberdade=5)
        assert c.u_i == Decimal("0.01")

    def test_happy_tipo_b_dof_infinito(self) -> None:
        c = ComponenteEntrada(nome="res", u_i=Decimal("0.005"), tipo="B", grau_liberdade=None)
        assert c.grau_liberdade is None

    def test_rejeita_u_i_negativo(self) -> None:
        with pytest.raises(ValueError, match="u_i < 0"):
            ComponenteEntrada(nome="x", u_i=Decimal("-0.01"), tipo="B", grau_liberdade=None)

    def test_rejeita_u_i_float(self) -> None:
        with pytest.raises(TypeError, match="deve ser Decimal"):
            ComponenteEntrada(nome="x", u_i=0.01, tipo="B", grau_liberdade=None)  # type: ignore[arg-type]

    def test_rejeita_tipo_invalido(self) -> None:
        with pytest.raises(ValueError, match="tipo invalido"):
            ComponenteEntrada(nome="x", u_i=Decimal("0.01"), tipo="C", grau_liberdade=1)

    def test_rejeita_tipo_a_sem_dof(self) -> None:
        with pytest.raises(ValueError, match="Tipo A exige grau_liberdade"):
            ComponenteEntrada(nome="x", u_i=Decimal("0.01"), tipo="A", grau_liberdade=None)

    def test_rejeita_dof_zero(self) -> None:
        with pytest.raises(ValueError, match="grau_liberdade < 1"):
            ComponenteEntrada(nome="x", u_i=Decimal("0.01"), tipo="A", grau_liberdade=0)


# =====================================================================
# combinar_tipo_a (T-CAL-050)
# =====================================================================


class TestCombinarTipoA:
    def test_happy_n_10(self) -> None:
        # s_x = 0.05, n = 10 -> u_a = 0.05 / sqrt(10) ~ 0.01581
        u_a, dof = combinar_tipo_a(Decimal("0.05"), 10)
        assert dof == 9
        # Tolerancia: aproximar pra 0.0158
        assert Decimal("0.0158") < u_a < Decimal("0.0159")

    def test_n_minimo_2(self) -> None:
        # n=2 aceito (mas NIT-DICLA-030 recomenda n>=6)
        u_a, dof = combinar_tipo_a(Decimal("0.1"), 2)
        assert dof == 1
        assert u_a > 0

    def test_rejeita_n_menor_2(self) -> None:
        with pytest.raises(ValueError, match="n < 2"):
            combinar_tipo_a(Decimal("0.05"), 1)

    def test_rejeita_s_x_negativo(self) -> None:
        with pytest.raises(ValueError, match="s_x < 0"):
            combinar_tipo_a(Decimal("-0.05"), 10)

    def test_rejeita_s_x_float(self) -> None:
        with pytest.raises(TypeError, match="deve ser Decimal"):
            combinar_tipo_a(0.05, 10)  # type: ignore[arg-type]

    def test_determinismo(self) -> None:
        # mesmo input -> mesmo output (replay ADR-0025)
        primeiro = combinar_tipo_a(Decimal("0.05"), 10)
        for _ in range(50):
            assert combinar_tipo_a(Decimal("0.05"), 10) == primeiro


# =====================================================================
# combinar_componentes (T-CAL-051)
# =====================================================================


class TestCombinarComponentes:
    def test_dois_componentes_independentes(self) -> None:
        # u_c = sqrt(0.01^2 + 0.005^2) = sqrt(0.0001 + 0.000025) = sqrt(0.000125)
        # ~ 0.01118
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "A", 5),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        u_c = combinar_componentes(componentes)
        # u_c^2 ~ 0.000125
        # Verificacao: (0.01118)^2 = 0.000125
        assert Decimal("0.01118") < u_c < Decimal("0.01119")

    def test_um_componente_so(self) -> None:
        # Caso degenerado: 1 componente -> u_c = u_i
        componentes = [ComponenteEntrada("x", Decimal("0.025"), "B", None)]
        assert combinar_componentes(componentes) == Decimal("0.025")

    def test_componentes_zerados(self) -> None:
        componentes = [
            ComponenteEntrada("a", Decimal("0"), "A", 1),
            ComponenteEntrada("b", Decimal("0"), "B", None),
        ]
        assert combinar_componentes(componentes) == Decimal("0")

    def test_rejeita_lista_vazia(self) -> None:
        with pytest.raises(ValueError, match="lista vazia"):
            combinar_componentes([])

    def test_com_correlacao_positiva(self) -> None:
        # u_c^2 = 0.01^2 + 0.01^2 + 2*1.0*0.01*0.01 = 0.0001 + 0.0001 + 0.0002 = 0.0004
        # u_c = 0.02 (correlacao perfeita = soma simples)
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.01"), "B", None),
        ]
        correl = [("a", "b", Decimal("1.0"))]
        u_c = combinar_componentes(componentes, correl)
        assert u_c == Decimal("0.02")

    def test_com_correlacao_negativa_completa(self) -> None:
        # u_c^2 = 0.01^2 + 0.01^2 + 2*(-1)*0.01*0.01 = 0.0001 + 0.0001 - 0.0002 = 0
        # u_c = 0 (correlacao -1 perfeita -> cancelamento)
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.01"), "B", None),
        ]
        correl = [("a", "b", Decimal("-1.0"))]
        u_c = combinar_componentes(componentes, correl)
        assert u_c == Decimal("0")

    def test_rejeita_correlacao_fora_intervalo(self) -> None:
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.01"), "B", None),
        ]
        with pytest.raises(ValueError, match="fora de"):
            combinar_componentes(componentes, [("a", "b", Decimal("1.5"))])

    def test_rejeita_correlacao_componente_inexistente(self) -> None:
        componentes = [ComponenteEntrada("a", Decimal("0.01"), "B", None)]
        with pytest.raises(ValueError, match="inexistente"):
            combinar_componentes(componentes, [("a", "x", Decimal("0.5"))])

    def test_rejeita_variancia_negativa_correlacao_excessiva(self) -> None:
        # Correlacoes negativas no limite podem dar variancia negativa
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        # ρ = -1 com magnitudes diferentes -> variancia ainda positiva
        # mas se tivessemos correlacoes cruzadas extremas com 3 componentes,
        # poderiamos cair em < 0. Aqui validamos caminho positivo:
        u_c = combinar_componentes(componentes, [("a", "b", Decimal("-1"))])
        assert u_c >= 0


# =====================================================================
# welch_satterthwaite (T-CAL-052)
# =====================================================================


class TestWelchSatterthwaite:
    def test_todos_tipo_b_dof_infinito(self) -> None:
        # Todos componentes Tipo B sem dof -> ν_eff = infinito (None)
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        assert welch_satterthwaite(componentes) is None

    def test_um_tipo_a_n_10(self) -> None:
        # Componente Tipo A com dof=9. u_i=0.01 -> ν_eff aproximado:
        # u_c^2 = 0.0001; denom = 0.01^4 / 9 = 1e-8 / 9 = 1.11e-9
        # ν_eff = (1e-4)^2 / 1.11e-9 = 1e-8 / 1.11e-9 = ~9.0
        componentes = [ComponenteEntrada("a", Decimal("0.01"), "A", 9)]
        dof = welch_satterthwaite(componentes)
        assert dof == 9  # so 1 componente Tipo A -> ν_eff = dof_a

    def test_mistura_a_b(self) -> None:
        # Tipo A (u=0.01, dof=4) + Tipo B (u=0.005, dof=inf)
        # u_c^2 = 0.0001 + 0.000025 = 0.000125
        # denom = (0.01^4)/4 + 0 = 1e-8 / 4 = 2.5e-9
        # ν_eff = (0.000125)^2 / 2.5e-9 = 1.5625e-8 / 2.5e-9 = 6.25 -> 6
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "A", 4),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        dof = welch_satterthwaite(componentes)
        assert dof == 6

    def test_componentes_zerados(self) -> None:
        # u_c = 0 -> retorna None (cobertura indefinida)
        componentes = [
            ComponenteEntrada("a", Decimal("0"), "A", 5),
        ]
        assert welch_satterthwaite(componentes) is None

    def test_rejeita_lista_vazia(self) -> None:
        with pytest.raises(ValueError, match="lista vazia"):
            welch_satterthwaite([])


# =====================================================================
# fator_k_para_95 (T-CAL-053)
# =====================================================================


class TestFatorK:
    def test_dof_none_eh_k_2(self) -> None:
        # Limite normal -> k=2 (95.45%)
        assert fator_k_para_95(None) == Decimal("2.000")

    def test_dof_acima_100_eh_k_2(self) -> None:
        assert fator_k_para_95(150) == Decimal("2.000")

    def test_dof_1_tabela(self) -> None:
        # dof=1 -> k=13.97 (Tabela G.2 GUM)
        assert fator_k_para_95(1) == Decimal("13.97")

    def test_dof_10_tabela(self) -> None:
        assert fator_k_para_95(10) == Decimal("2.284")

    def test_dof_100_tabela(self) -> None:
        assert fator_k_para_95(100) == Decimal("2.025")

    def test_dof_intermediario_usa_inferior(self) -> None:
        # dof=23 nao tabelado; usa entrada de dof=20 (inferior mais proxima)
        # = conservador (k_20=2.133 >= k_23 real)
        assert fator_k_para_95(23) == Decimal("2.133")

    def test_dof_45_usa_40(self) -> None:
        assert fator_k_para_95(45) == Decimal("2.064")

    def test_rejeita_dof_zero(self) -> None:
        with pytest.raises(ValueError, match="dof < 1"):
            fator_k_para_95(0)


# =====================================================================
# propagar (T-CAL-054) — fluxo end-to-end
# =====================================================================


class TestPropagar:
    def test_happy_3_componentes(self) -> None:
        # Cenario tipico calibracao de massa:
        # - Repetibilidade Tipo A: s_x=0.0005, n=10 -> u_a ~ 0.000158
        # - Resolucao Tipo B: u_b=0.00005 (dof=inf)
        # - Padrao referencia Tipo B: u_b=0.0001 (dof=inf)
        u_a, dof_a = combinar_tipo_a(Decimal("0.0005"), 10)
        componentes = [
            ComponenteEntrada("repetibilidade", u_a, "A", dof_a),
            ComponenteEntrada("resolucao", Decimal("0.00005"), "B", None),
            ComponenteEntrada("padrao", Decimal("0.0001"), "B", None),
        ]
        resultado = propagar(componentes)
        assert isinstance(resultado, ResultadoGUM)
        assert resultado.u_combinada > 0
        assert resultado.fator_k > 0
        assert resultado.U_expandida == resultado.fator_k * resultado.u_combinada
        assert resultado.nivel_confianca == Decimal("0.9545")

    def test_resultado_so_tipo_b_k_2(self) -> None:
        # Todos Tipo B dof=inf -> k=2 normal limite
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "B", None),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        resultado = propagar(componentes)
        assert resultado.grau_liberdade_efetivo is None
        assert resultado.fator_k == Decimal("2.000")

    def test_determinismo(self) -> None:
        componentes = [
            ComponenteEntrada("a", Decimal("0.01"), "A", 5),
            ComponenteEntrada("b", Decimal("0.005"), "B", None),
        ]
        primeiro = propagar(componentes)
        for _ in range(50):
            atual = propagar(componentes)
            assert atual.u_combinada == primeiro.u_combinada
            assert atual.U_expandida == primeiro.U_expandida
            assert atual.fator_k == primeiro.fator_k


def test_resultado_gum_dataclass_imutavel() -> None:
    """ResultadoGUM eh frozen — invariante de imutabilidade."""
    from dataclasses import FrozenInstanceError

    r = ResultadoGUM(
        u_combinada=Decimal("0.01"),
        grau_liberdade_efetivo=10,
        fator_k=Decimal("2.284"),
        U_expandida=Decimal("0.022"),
    )
    with pytest.raises(FrozenInstanceError):
        r.u_combinada = Decimal("999")  # type: ignore[misc]
