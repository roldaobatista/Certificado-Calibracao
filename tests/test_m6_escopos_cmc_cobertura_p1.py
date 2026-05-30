"""Testes da cobertura RBC — M6 Fatia 1a (T-ECMC-004, ADR-0074).

Matemática pura das 3 condições: contenção total de faixa + U≥CMC (ILAC-P14 §5.5)
+ menor CMC por faixa (NIT-DICLA-012). Sem DB. Valores conferidos à mão.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.metrologia.escopos_cmc import cobertura
from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo, FormaCMC
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

_DT = datetime(2026, 1, 1, tzinfo=UTC)


def _faixa(lo: str, hi: str, unidade: str = "kg") -> FaixaMedicao:
    return FaixaMedicao(Decimal(lo), Decimal(hi), unidade)


def _escopo(
    *,
    faixa: FaixaMedicao,
    cmc: str = "0.01",
    forma: FormaCMC = FormaCMC.ABSOLUTA,
    coef: str | None = None,
    cmc_unidade: str = "kg",
) -> EscopoCMCSnapshot:
    return EscopoCMCSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        grandeza=Grandeza.MASSA,
        faixa=faixa,
        cmc_forma=forma,
        cmc_valor=Decimal(cmc),
        cmc_unidade=cmc_unidade,
        rbc_acreditado=True,
        versao=1,
        vigente_a_partir=_DT,
        estado=EstadoEscopo.CONFIRMADO,
        revision=0,
        vigencia_inicio=_DT,
        correlation_id=uuid4(),
        cmc_coef_relativo=None if coef is None else Decimal(coef),
    )


class TestContencaoTotal:
    def test_dentro_cobre(self) -> None:
        assert cobertura.faixa_contida(
            solicitada=_faixa("10", "20"), escopo=_faixa("0", "100")
        )

    def test_borda_exata_cobre(self) -> None:
        # solicitada == escopo (limites coincidem) -> contido (<=, >=)
        assert cobertura.faixa_contida(
            solicitada=_faixa("0", "100"), escopo=_faixa("0", "100")
        )

    def test_excede_topo_nao_cobre(self) -> None:
        assert not cobertura.faixa_contida(
            solicitada=_faixa("50", "150"), escopo=_faixa("0", "100")
        )

    def test_abaixo_do_piso_nao_cobre(self) -> None:
        # FaixaMedicao exige inferior<superior; -5<50 ok
        assert not cobertura.faixa_contida(
            solicitada=_faixa("-5", "50"), escopo=_faixa("0", "100")
        )

    def test_intersecao_parcial_nao_cobre(self) -> None:
        # interseção parcial (sobrepõe mas não contido) = fraude evitada (TL-C-08)
        assert not cobertura.faixa_contida(
            solicitada=_faixa("80", "120"), escopo=_faixa("0", "100")
        )

    def test_unidade_diferente_fail_closed(self) -> None:
        assert not cobertura.faixa_contida(
            solicitada=_faixa("10", "20", "g"), escopo=_faixa("0", "100", "kg")
        )


class TestAvaliarContencaoReason:
    def test_contido_reason_vazio(self) -> None:
        ok, reason = cobertura.avaliar_contencao(
            solicitada=_faixa("10", "20"), escopo=_faixa("0", "100")
        )
        assert ok and reason == cobertura.REASON_OK

    def test_fora_reason_estavel(self) -> None:
        ok, reason = cobertura.avaliar_contencao(
            solicitada=_faixa("50", "150"), escopo=_faixa("0", "100")
        )
        assert not ok and reason == cobertura.REASON_FORA_DO_ESCOPO

    def test_unidade_incompativel_reason(self) -> None:
        ok, reason = cobertura.avaliar_contencao(
            solicitada=_faixa("10", "20", "g"), escopo=_faixa("0", "100", "kg")
        )
        assert not ok and reason == cobertura.REASON_UNIDADE_INCOMPATIVEL


class TestCMCNoPonto:
    def test_absoluta_constante(self) -> None:
        esc = _escopo(faixa=_faixa("0", "100"), cmc="0.01")
        assert cobertura.cmc_no_ponto(escopo=esc, ponto=Decimal("5")) == Decimal("0.01")
        assert cobertura.cmc_no_ponto(escopo=esc, ponto=Decimal("99")) == Decimal("0.01")

    def test_relativa_linear_a_mais_b_x(self) -> None:
        # CMC = a + b·|X| = 0.01 + 0.0001·200 = 0.01 + 0.02 = 0.03
        esc = _escopo(
            faixa=_faixa("0", "300"),
            cmc="0.01",
            forma=FormaCMC.RELATIVA_LINEAR,
            coef="0.0001",
        )
        assert cobertura.cmc_no_ponto(escopo=esc, ponto=Decimal("200")) == Decimal("0.03")

    def test_relativa_usa_modulo_do_ponto(self) -> None:
        # mensurando negativo (ex. temperatura) -> usa |X|
        esc = _escopo(
            faixa=_faixa("-50", "50", "C"),
            cmc="0.1",
            forma=FormaCMC.RELATIVA_LINEAR,
            coef="0.01",
            cmc_unidade="C",
        )
        assert cobertura.cmc_no_ponto(escopo=esc, ponto=Decimal("-30")) == Decimal("0.4")

    def test_relativa_sem_coef_levanta(self) -> None:
        esc = _escopo(
            faixa=_faixa("0", "100"), forma=FormaCMC.RELATIVA_LINEAR, coef=None
        )
        with pytest.raises(ValueError, match="cmc_coef_relativo"):
            cobertura.cmc_no_ponto(escopo=esc, ponto=Decimal("10"))


class TestUAtendeCMC:
    def test_u_maior_que_cmc_atende(self) -> None:
        assert cobertura.u_atende_cmc(
            u_reportada=Decimal("0.05"), cmc_no_ponto=Decimal("0.01")
        )

    def test_u_igual_cmc_atende(self) -> None:
        # U == CMC satisfaz o piso (>=); a suspeita de cópia é flag separada
        assert cobertura.u_atende_cmc(
            u_reportada=Decimal("0.01"), cmc_no_ponto=Decimal("0.01")
        )

    def test_u_menor_que_cmc_nao_atende(self) -> None:
        # NC nº 1 de auditoria CGCRE: lab reportando incerteza melhor que a CMC
        assert not cobertura.u_atende_cmc(
            u_reportada=Decimal("0.005"), cmc_no_ponto=Decimal("0.01")
        )

    def test_avaliar_u_cmc_reason_abaixo(self) -> None:
        ok, reason = cobertura.avaliar_u_cmc(
            u_reportada=Decimal("0.005"), cmc_no_ponto=Decimal("0.01")
        )
        assert not ok and reason == cobertura.REASON_INCERTEZA_ABAIXO_CMC

    def test_avaliar_u_cmc_reason_ok(self) -> None:
        ok, reason = cobertura.avaliar_u_cmc(
            u_reportada=Decimal("0.02"), cmc_no_ponto=Decimal("0.01")
        )
        assert ok and reason == cobertura.REASON_OK

    def test_float_levanta(self) -> None:
        with pytest.raises(ValueError, match="Decimal"):
            cobertura.u_atende_cmc(u_reportada=0.05, cmc_no_ponto=Decimal("0.01"))  # type: ignore[arg-type]


class TestUIgualCMCSuspeita:
    def test_igual_e_suspeito(self) -> None:
        # RBC-NC-07: U=CMC cego é suspeito (orçamento deveria somar o instrumento)
        assert cobertura.u_igual_cmc_suspeita(
            u_reportada=Decimal("0.01"), cmc_no_ponto=Decimal("0.01")
        )

    def test_maior_nao_suspeito(self) -> None:
        assert not cobertura.u_igual_cmc_suspeita(
            u_reportada=Decimal("0.02"), cmc_no_ponto=Decimal("0.01")
        )


class TestMenorCMCPorFaixa:
    def test_dois_metodos_absolutos_pega_menor(self) -> None:
        # NIT-DICLA-012: N métodos na mesma faixa -> CMC publicada é a MENOR
        e1 = _escopo(faixa=_faixa("0", "100"), cmc="0.02")
        e2 = _escopo(faixa=_faixa("0", "100"), cmc="0.01")
        assert cobertura.menor_cmc_por_faixa([e1, e2], ponto=Decimal("50")) == Decimal(
            "0.01"
        )

    def test_mistura_absoluta_e_relativa_no_ponto(self) -> None:
        # absoluta 0.02 ; relativa a=0.005 b=0.0001 ponto=100 -> 0.005+0.01=0.015
        e_abs = _escopo(faixa=_faixa("0", "200"), cmc="0.02")
        e_rel = _escopo(
            faixa=_faixa("0", "200"),
            cmc="0.005",
            forma=FormaCMC.RELATIVA_LINEAR,
            coef="0.0001",
        )
        assert cobertura.menor_cmc_por_faixa(
            [e_abs, e_rel], ponto=Decimal("100")
        ) == Decimal("0.015")

    def test_vazio_retorna_none(self) -> None:
        assert cobertura.menor_cmc_por_faixa([], ponto=Decimal("50")) is None
