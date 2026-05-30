"""M7 Fatia 0 (T-PROC-000) — geometria de faixa compartilhada `faixa_cobertura`.

Cobre o módulo puro extraído de escopos_cmc/cobertura.py (D-PROC-6). A contenção
`faixa_contida` já é exercitada via M6 (re-export); aqui foco nos reasons NEUTROS
de `avaliar_contencao` (M6 mantém os reasons `cmc_*` próprios; M7 usará estes).
"""

from __future__ import annotations

from decimal import Decimal

from src.domain.metrologia import faixa_cobertura as fc
from src.domain.metrologia.value_objects import FaixaMedicao


def _f(lo: str, hi: str, un: str = "g") -> FaixaMedicao:
    return FaixaMedicao(Decimal(lo), Decimal(hi), un)


def test_faixa_contida_dentro_e_borda():
    escopo = _f("0", "1000")
    assert fc.faixa_contida(solicitada=_f("10", "20"), escopo=escopo)
    assert fc.faixa_contida(solicitada=_f("0", "1000"), escopo=escopo)  # borda


def test_faixa_contida_intersecao_parcial_nao_cobre():
    escopo = _f("0", "1000")
    assert not fc.faixa_contida(solicitada=_f("900", "2000"), escopo=escopo)
    assert not fc.faixa_contida(solicitada=_f("-5", "10"), escopo=escopo)


def test_faixa_contida_unidade_divergente_fail_closed():
    assert not fc.faixa_contida(solicitada=_f("10", "20", "kg"), escopo=_f("0", "1000", "g"))


def test_avaliar_contencao_reasons_neutros():
    escopo = _f("0", "1000")
    assert fc.avaliar_contencao(solicitada=_f("10", "20"), escopo=escopo) == (
        True,
        fc.REASON_OK,
    )
    assert fc.avaliar_contencao(solicitada=_f("900", "2000"), escopo=escopo) == (
        False,
        fc.REASON_FORA_DA_FAIXA,
    )
    assert fc.avaliar_contencao(
        solicitada=_f("10", "20", "kg"), escopo=escopo
    ) == (False, fc.REASON_UNIDADE_INCOMPATIVEL)


def test_reasons_neutros_sem_prefixo_de_dominio():
    # Geometria compartilhada não vaza semântica de CMC/escopo.
    assert "cmc" not in fc.REASON_FORA_DA_FAIXA
    assert "cmc" not in fc.REASON_UNIDADE_INCOMPATIVEL
