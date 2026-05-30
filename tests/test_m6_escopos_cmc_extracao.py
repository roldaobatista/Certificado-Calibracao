"""Testes do motor determinístico de extração de escopo CGCRE (M6 Fatia 4 — T-ECMC-050/054).

Puro (sem Django). Inclui o REPLAY do contrato cl. 7.11
(`tests/replay_metrologico/escopos_cmc_extracao.json`) — mesma entrada -> mesma
saída (ADR-0025). NÃO IA (T-ECMC-050).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from src.domain.metrologia.escopos_cmc.extracao import (
    MapaColunas,
    parsear_decimal_ptbr,
    parsear_tabela,
)

_FIXTURE = (
    Path(__file__).parent / "replay_metrologico" / "escopos_cmc_extracao.json"
)


def _dec(v: str | None) -> Decimal | None:
    return None if v is None else Decimal(v)


class TestParsearDecimalPtbr:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("0,5", Decimal("0.5")),
            ("1.234,56", Decimal("1234.56")),
            ("200", Decimal("200")),
            ("-30", Decimal("-30")),
            ("(0,5", Decimal("0.5")),  # parêntese colado
            ("200) kg", Decimal("200")),  # unidade colada
            ("0.5", Decimal("0.5")),  # en-US sem vírgula
            ("", None),
            ("sem numero", None),
            ("abc", None),
        ],
    )
    def test_parse(self, entrada: str, esperado: Decimal | None) -> None:
        assert parsear_decimal_ptbr(entrada) == esperado


class TestMapaColunas:
    def test_exige_faixa_ou_min_max(self) -> None:
        with pytest.raises(ValueError, match="faixa"):
            parsear_tabela([["a", "b"]], MapaColunas(grandeza=0, cmc=1))

    def test_faixa_min_max_separados(self) -> None:
        linhas = [["Massa", "0,5", "200", "kg", "0,1"]]
        mapa = MapaColunas(
            grandeza=0, faixa_min=1, faixa_max=2, unidade=3, cmc=4
        )
        (linha,) = parsear_tabela(linhas, mapa)
        assert linha.faixa_min == Decimal("0.5")
        assert linha.faixa_max == Decimal("200")
        assert linha.confianca == Decimal("1")

    def test_linha_vazia_ignorada(self) -> None:
        linhas = [["", "", ""], ["Massa", "0,5 a 200", "0,1"]]
        mapa = MapaColunas(grandeza=0, faixa=1, cmc=2)
        out = parsear_tabela(linhas, mapa)
        assert len(out) == 1


class TestReplayContrato:
    """cl. 7.11 — mesma entrada -> saída idêntica ao ground truth versionado."""

    def test_replay_bate_ground_truth(self) -> None:
        dados = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        mapa = MapaColunas(**dados["mapa"])
        out = parsear_tabela(dados["linhas"], mapa)
        esperado = dados["esperado"]
        assert len(out) == len(esperado)
        for linha, exp in zip(out, esperado, strict=True):
            assert linha.grandeza_texto == exp["grandeza_texto"]
            assert linha.unidade == exp["unidade"]
            assert linha.cmc_texto == exp["cmc_texto"]
            assert linha.metodo_texto == exp["metodo_texto"]
            assert linha.faixa_min == _dec(exp["faixa_min"])
            assert linha.faixa_max == _dec(exp["faixa_max"])
            assert linha.confianca == Decimal(exp["confianca"])

    def test_determinismo_idempotente(self) -> None:
        dados = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        mapa = MapaColunas(**dados["mapa"])
        a = parsear_tabela(dados["linhas"], mapa)
        b = parsear_tabela(dados["linhas"], mapa)
        assert a == b
