"""T-EQP-038 — helper `texto_termo_transferencia` + 4 clausulas + anti-drift.

Cobre:
- Versao canonica retorna texto completo com 4 clausulas.
- Cada clausula referencia fundamento legal especifico.
- Versao desconhecida -> ValueError.
- `versao_canonica` Python igual ao frontmatter do doc.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from src.infrastructure.equipamentos.validators import (
    CLAUSULA_1_LGPD_ART_18,
    CLAUSULA_2_LEI_14063_ART_4,
    CLAUSULA_3_NAO_CESSAO_GARANTIA,
    CLAUSULA_4_TITULARIDADE_DADO_PESSOAL,
    TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA,
    texto_termo_transferencia,
)

DOC_TERMO_PATH = (
    Path(__file__).parent.parent
    / "docs"
    / "conformidade"
    / "equipamentos"
    / "transferencia-termo.md"
)


def test_texto_termo_versao_atual_retorna_4_clausulas():
    texto = texto_termo_transferencia()
    # Texto contem trechos canonicos de cada clausula.
    assert "LGPD" in texto
    assert "art. 18" in texto
    assert "Lei 14.063" in texto
    assert "art. 4o" in texto
    assert "garantias" in texto
    assert "ISO/IEC 17025" in texto
    assert "art. 5o VI" in texto
    assert "art. 5o VII" in texto
    assert "consentimento_historico_expresso" in texto


def test_clausula_1_referencia_lgpd_art_18():
    assert "art. 18 da LGPD" in CLAUSULA_1_LGPD_ART_18
    assert "DPO" in CLAUSULA_1_LGPD_ART_18


def test_clausula_2_referencia_lei_14063_e_codigo_penal():
    assert "Lei 14.063/2020" in CLAUSULA_2_LEI_14063_ART_4
    assert "299" in CLAUSULA_2_LEI_14063_ART_4  # falsidade ideologica
    assert "171" in CLAUSULA_2_LEI_14063_ART_4  # estelionato
    assert "482" in CLAUSULA_2_LEI_14063_ART_4  # CLT


def test_clausula_3_referencia_iso_17025_e_garantia():
    assert "garantias do fabricante" in CLAUSULA_3_NAO_CESSAO_GARANTIA
    assert "ISO/IEC 17025 cl. 8.4" in CLAUSULA_3_NAO_CESSAO_GARANTIA


def test_clausula_4_referencia_lgpd_art_5_titularidade_dado_pessoal():
    """v1.1 NEW — P-EQP-A1 advogado."""
    assert "titularidade" in CLAUSULA_4_TITULARIDADE_DADO_PESSOAL
    assert "dados pessoais" in CLAUSULA_4_TITULARIDADE_DADO_PESSOAL
    assert "consentimento_historico_expresso" in CLAUSULA_4_TITULARIDADE_DADO_PESSOAL


def test_versao_desconhecida_levanta():
    with pytest.raises(ValueError, match="nao implementada"):
        texto_termo_transferencia("v0.1-antigo")


def test_versao_canonica_bate_com_frontmatter_do_doc():
    """Anti-drift — versao Python igual ao frontmatter."""
    assert DOC_TERMO_PATH.exists(), f"doc ausente: {DOC_TERMO_PATH}"
    conteudo = DOC_TERMO_PATH.read_text(encoding="utf-8")
    match = re.search(r"versao_canonica:\s*(\S+)", conteudo)
    assert match, "frontmatter sem versao_canonica"
    versao_doc = match.group(1).strip()
    assert versao_doc == TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA, (
        f"DRIFT — Python={TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA} doc={versao_doc}. "
        "Atualize constante + frontmatter no MESMO PR (advogado-saas-regulado)."
    )


def test_4_clausulas_unicas():
    """Cada clausula tem texto distinto."""
    clausulas = {
        CLAUSULA_1_LGPD_ART_18,
        CLAUSULA_2_LEI_14063_ART_4,
        CLAUSULA_3_NAO_CESSAO_GARANTIA,
        CLAUSULA_4_TITULARIDADE_DADO_PESSOAL,
    }
    assert len(clausulas) == 4
