"""T-EQP-060 (US-EQP-006 AC-EQP-006-12 / P-EQP-S4) — clausula contratual
direito de recusar recebimento sem RC quando cliente recusa foto.

Marco 2 expoe apenas constante + helper em `validators.py`; gerador de
contrato tenant<->cliente em Wave A `comunicacao-contratual` lera daqui.

Cobre:
- Helper retorna texto canonico para versao default.
- Versao desconhecida -> ValueError (anti-drift).
- Constante VERSAO_CANONICA bate com frontmatter do doc canonico.
- Texto inclui as 4 letras (a)/(b)/fundamento/CDC obrigatorios.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.infrastructure.equipamentos.validators import (
    CLAUSULA_RECUSA_FOTO,
    CLAUSULA_RECUSA_FOTO_VERSAO_CANONICA,
    clausula_contratual_recusa_foto,
)


def test_helper_retorna_texto_canonico_versao_default():
    texto = clausula_contratual_recusa_foto()
    assert texto == CLAUSULA_RECUSA_FOTO
    assert "CLAUSULA — DOCUMENTACAO FOTOGRAFICA DE RECEBIMENTO" in texto


def test_helper_versao_desconhecida_falha_loud():
    with pytest.raises(ValueError, match=r"v9.99-2030-12-31"):
        clausula_contratual_recusa_foto("v9.99-2030-12-31")


def test_versao_canonica_bate_doc():
    doc = Path("docs/conformidade/equipamentos/aviso-foto-recebimento.md")
    assert doc.exists(), f"Doc canonico esperado em {doc}"
    conteudo = doc.read_text(encoding="utf-8")
    # A versao canonica do aviso UX e o frontmatter compartilhado;
    # T-EQP-060 reusa esse marcador.
    assert CLAUSULA_RECUSA_FOTO_VERSAO_CANONICA in conteudo


def test_texto_inclui_quatro_clausulas_obrigatorias():
    texto = clausula_contratual_recusa_foto()
    # Estrutura mandatoria (advogado-saas-regulado):
    assert "(a) Recusar o recebimento" in texto
    assert "(b) Aceitar o recebimento mediante termo de RESPONSABILIDADE" in texto
    # Fundamento legal explicito.
    assert "ISO/IEC 17025 cl. 7.4" in texto
    assert "LGPD art. 7º V" in texto
    assert "Codigo Civil arts. 421" in texto
    # CDC mencionado (defesa basica do consumidor preservada).
    assert "CDC" in texto


def test_texto_nao_tem_cta_promocional():
    """P-EQP-A6 + P-EQP-S4 — clausula NAO pode ter CTA / promocao /
    chamada pra acao (allowlist semantica do advogado)."""
    texto = clausula_contratual_recusa_foto().lower()
    # Falsos termos comerciais nunca devem aparecer.
    for proibido in [
        "compre",
        "contrate",
        "promocao",
        "promoção",
        "desconto",
        "oferta",
        "garantia estendida",
    ]:
        assert proibido not in texto, f"CTA proibido '{proibido}' encontrado."
