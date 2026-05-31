"""SAN-INCERTEZA-PONTO Fatia domínio (ADR-0077) — derivação Tipo A por ponto +
agregado pior-caso. Puro (sem Django/PG). Regras consultor-rbc Q-RBC-1/2/3.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.enums import (
    LeiEscalonamento,
    MetodoTipoAPonto,
)
from src.domain.metrologia.calibracao.motor_calculo.incerteza_por_ponto import (
    N_MINIMO_TIPO_A,
    TipoAInsuficienteError,
    agregado_pior_caso,
    derivar_tipo_a_ponto,
    desvio_padrao_amostral,
)

# 6 repetições com média 10.0; s_x conhecido.
_SEIS = [Decimal("10.0"), Decimal("10.2"), Decimal("9.8"), Decimal("10.1"),
         Decimal("9.9"), Decimal("10.0")]


class TestDesvioPadraoAmostral:
    def test_n_menor_que_2_levanta(self):
        with pytest.raises(ValueError, match="n < 2"):
            desvio_padrao_amostral([Decimal("1")])

    def test_valores_iguais_da_zero(self):
        assert desvio_padrao_amostral([Decimal("5"), Decimal("5"), Decimal("5")]) == Decimal("0")

    def test_calculo_conhecido(self):
        # [2,4,6] -> média 4, var = (4+0+4)/2 = 4, s = 2
        assert desvio_padrao_amostral([Decimal("2"), Decimal("4"), Decimal("6")]) == Decimal("2")


class TestDerivarTipoAPonto:
    def test_n_maior_igual_6_usa_sx_proprio(self):
        r = derivar_tipo_a_ponto(valores_repeticoes=_SEIS, perfil="A")
        assert r.metodo is MetodoTipoAPonto.SX_PROPRIO
        assert r.n_repeticoes == 6
        assert r.dof == 5
        assert r.tipo_a_insuficiente is False
        assert r.s_usado is not None and r.s_usado > 0

    def test_n_entre_2_e_6_com_pool_usa_s_pooled(self):
        r = derivar_tipo_a_ponto(
            valores_repeticoes=[Decimal("10"), Decimal("10.1"), Decimal("9.9")],
            perfil="A",
            s_pooled=(Decimal("0.15"), 29),
        )
        assert r.metodo is MetodoTipoAPonto.S_POOLED
        assert r.s_usado == Decimal("0.15")
        assert r.dof == 29
        assert r.tipo_a_insuficiente is False

    def test_n_entre_2_e_6_perfil_A_sem_pool_fail_closed(self):
        with pytest.raises(TipoAInsuficienteError):
            derivar_tipo_a_ponto(
                valores_repeticoes=[Decimal("10"), Decimal("10.1"), Decimal("9.9")],
                perfil="A",
            )

    @pytest.mark.parametrize("perfil", ["B", "C", "D"])
    def test_n_entre_2_e_6_nao_A_sem_pool_ressalva(self, perfil):
        r = derivar_tipo_a_ponto(
            valores_repeticoes=[Decimal("10"), Decimal("10.1"), Decimal("9.9")],
            perfil=perfil,
        )
        assert r.metodo is MetodoTipoAPonto.SX_PROPRIO
        assert r.tipo_a_insuficiente is True  # ressalva registrada, não bloqueia
        assert r.n_repeticoes == 3

    def test_n_menor_que_2_ausente(self):
        r = derivar_tipo_a_ponto(valores_repeticoes=[Decimal("10")], perfil="A")
        assert r.metodo is MetodoTipoAPonto.AUSENTE
        assert r.s_usado is None
        assert r.dof is None
        assert r.tipo_a_insuficiente is True

    def test_n_zero_ausente_nao_levanta(self):
        r = derivar_tipo_a_ponto(valores_repeticoes=[], perfil="A")
        assert r.metodo is MetodoTipoAPonto.AUSENTE

    def test_n_minimo_constante(self):
        assert N_MINIMO_TIPO_A == 6


class TestAgregadoPiorCaso:
    def test_retorna_max_nao_media(self):
        us = [Decimal("0.10"), Decimal("0.30"), Decimal("0.20")]
        # média seria 0.20; pior-caso é 0.30 (média subestima — Q-RBC-3)
        assert agregado_pior_caso(us) == Decimal("0.30")

    def test_lista_vazia_levanta(self):
        with pytest.raises(ValueError, match="vazia"):
            agregado_pior_caso([])

    def test_um_ponto(self):
        assert agregado_pior_caso([Decimal("0.05")]) == Decimal("0.05")


class TestEnums:
    def test_metodo_tipo_a_valores(self):
        assert {m.value for m in MetodoTipoAPonto} == {"SX_PROPRIO", "S_POOLED", "AUSENTE"}

    def test_lei_escalonamento_valores(self):
        assert {lei.value for lei in LeiEscalonamento} == {"CONSTANTE", "PROPORCIONAL", "LINEAR_AFIM"}
