"""T-EQP-013 (AC-EQP-002-2 / INV-025 / P-EQP-A3) — helper de textos
canonicos 422 pos-certificado.

Cobre:
1. Cada chave T1-T5 retorna texto exato (immutabilidade canonica).
2. Cita ISO 17025 cl. 8.4.
3. Mapeamento campo -> chave fechado (tag/numero_serie/fabricante).
4. Campo fora da lista cai em T4 (fallback).
5. `_delete_versao` retorna T5.
6. Versao canonica bate com frontmatter do doc.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.infrastructure.equipamentos.validators import (
    TEXTO_T1_TAG,
    TEXTO_T2_NUMERO_SERIE,
    TEXTO_T3_FABRICANTE,
    TEXTO_T4_FALLBACK_GENERICO,
    TEXTO_T5_DELETE_VERSAO,
    TEXTOS_REJEICAO_422_VERSAO_CANONICA,
    texto_rejeicao_422_pos_cert,
)

DOC_TEXTOS_PATH = (
    Path(__file__).parent.parent
    / "docs"
    / "conformidade"
    / "equipamentos"
    / "textos-rejeicao-422.md"
)


def test_t1_tag_retorna_texto_canonico():
    assert texto_rejeicao_422_pos_cert("tag") == TEXTO_T1_TAG
    assert "TAG operacional" in TEXTO_T1_TAG
    assert "ISO/IEC 17025 cl. 8.4" in TEXTO_T1_TAG


def test_t2_numero_serie_retorna_texto_canonico():
    assert texto_rejeicao_422_pos_cert("numero_serie") == TEXTO_T2_NUMERO_SERIE
    assert "numero de serie" in TEXTO_T2_NUMERO_SERIE
    assert "ISO/IEC 17025 cl. 8.4" in TEXTO_T2_NUMERO_SERIE


def test_t3_fabricante_retorna_texto_canonico():
    assert texto_rejeicao_422_pos_cert("fabricante") == TEXTO_T3_FABRICANTE
    assert "fabricante nao pode ser alterado" in TEXTO_T3_FABRICANTE
    assert "NIT-DICLA-030" in TEXTO_T3_FABRICANTE


def test_t4_fallback_para_campo_nao_listado():
    """Campo critico futuro nao listado em T1-T3 deve cair em T4."""
    assert (
        texto_rejeicao_422_pos_cert("classe_metrologica_futura")
        == TEXTO_T4_FALLBACK_GENERICO
    )
    assert texto_rejeicao_422_pos_cert("modelo") == TEXTO_T4_FALLBACK_GENERICO
    assert "ISO/IEC 17025 cl. 8.4" in TEXTO_T4_FALLBACK_GENERICO


def test_t5_delete_versao_retorna_texto_canonico():
    assert texto_rejeicao_422_pos_cert("_delete_versao") == TEXTO_T5_DELETE_VERSAO
    assert "nao podem ser excluidas" in TEXTO_T5_DELETE_VERSAO
    assert "ISO/IEC 17025 cl. 8.4" in TEXTO_T5_DELETE_VERSAO


def test_versao_canonica_bate_com_frontmatter_do_doc():
    """Defesa anti-drift — `versao_canonica` no validator igual ao
    frontmatter do doc canonico."""
    assert DOC_TEXTOS_PATH.exists(), (
        f"doc canonico ausente: {DOC_TEXTOS_PATH}"
    )
    conteudo = DOC_TEXTOS_PATH.read_text(encoding="utf-8")
    match = re.search(r"versao_canonica:\s*([\d.]+)", conteudo)
    assert match, "frontmatter sem versao_canonica"
    versao_doc = match.group(1)
    assert versao_doc == TEXTOS_REJEICAO_422_VERSAO_CANONICA, (
        f"DRIFT — validator={TEXTOS_REJEICAO_422_VERSAO_CANONICA} doc={versao_doc}. "
        "Atualize o constant e o frontmatter no MESMO PR (advogado-saas-regulado)."
    )


def test_5_textos_todos_diferentes():
    """Cada T tem texto unico — nao reusar nem misturar."""
    textos = {
        TEXTO_T1_TAG,
        TEXTO_T2_NUMERO_SERIE,
        TEXTO_T3_FABRICANTE,
        TEXTO_T4_FALLBACK_GENERICO,
        TEXTO_T5_DELETE_VERSAO,
    }
    assert len(textos) == 5
