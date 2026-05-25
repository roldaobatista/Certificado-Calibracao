"""Unit test de `canonicalizar_texto_probatorio` + `hash_texto_canonicalizado`
(TST-005 + Q-OS-03 + Q-OS-06 INV-DOC-CANON-001).

Garante determinismo cross-platform e cobertura dos 5 passos do ADR-0029.
"""

from __future__ import annotations

import hashlib

import pytest
from src.domain.operacao.os.regras import (
    canonicalizar_texto_probatorio,
    hash_texto_canonicalizado,
)


def test_canonicalizar_texto_minimo_valido():
    canonico = canonicalizar_texto_probatorio("Aceito o servico.")
    assert canonico == "<<<CORPO INICIO>>>\nAceito o servico.\n<<<CORPO FIM>>>"


def test_canonicalizar_crlf_vira_lf():
    canonico = canonicalizar_texto_probatorio("linha1\r\nlinha2\rlinha3")
    assert "\r" not in canonico
    assert canonico == "<<<CORPO INICIO>>>\nlinha1\nlinha2\nlinha3\n<<<CORPO FIM>>>"


def test_canonicalizar_trailing_whitespace_removido_por_linha():
    canonico = canonicalizar_texto_probatorio("linha1   \nlinha2\t\nlinha3")
    assert canonico == "<<<CORPO INICIO>>>\nlinha1\nlinha2\nlinha3\n<<<CORPO FIM>>>"


def test_canonicalizar_strip_leading_trailing_global():
    canonico = canonicalizar_texto_probatorio("\n\n  texto  \n\n")
    assert canonico == "<<<CORPO INICIO>>>\ntexto\n<<<CORPO FIM>>>"


def test_canonicalizar_nfc_unicode():
    nfd = "café"
    nfc_esperado = "café"
    canonico = canonicalizar_texto_probatorio(nfd)
    assert nfc_esperado in canonico


def test_canonicalizar_tipo_invalido_raises():
    with pytest.raises(TypeError, match="corpo deve ser str"):
        canonicalizar_texto_probatorio(b"bytes")  # type: ignore[arg-type]


# Hash determinístico — vetor fixo


def test_hash_texto_canonicalizado_vetor_fixo_1():
    """Vetor fixo INV-DOC-CANON-001: input -> hash exato (regressao se hash mudar)."""
    texto = "Aceito o servico."
    canonico = "<<<CORPO INICIO>>>\nAceito o servico.\n<<<CORPO FIM>>>"
    # audit-pii-salt: skip -- hash de texto canonico publico (ADR-0029), nao PII; vetor fixo de regressao cross-platform
    hash_esperado = hashlib.sha256(canonico.encode("utf-8")).hexdigest()
    assert hash_texto_canonicalizado(texto) == hash_esperado


def test_hash_texto_canonicalizado_crlf_e_lf_geram_mesmo_hash():
    """Determinismo cross-platform: Win (CRLF) e Linux (LF) -> mesmo hash."""
    assert hash_texto_canonicalizado("linha1\r\nlinha2") == hash_texto_canonicalizado(
        "linha1\nlinha2"
    )


def test_hash_texto_canonicalizado_nfd_e_nfc_geram_mesmo_hash():
    nfd = "café"
    nfc = "café"
    assert hash_texto_canonicalizado(nfd) == hash_texto_canonicalizado(nfc)


def test_hash_texto_canonicalizado_trailing_whitespace_irrelevante():
    assert hash_texto_canonicalizado("linha1   \nlinha2") == hash_texto_canonicalizado(
        "linha1\nlinha2"
    )
