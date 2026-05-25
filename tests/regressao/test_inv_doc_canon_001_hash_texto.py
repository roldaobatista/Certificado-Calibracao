"""Anti-regressao INV-DOC-CANON-001 (Q-OS-06 P5 conserto) — hash determinístico
cross-platform de texto probatorio.

Texto canônico (ADR-0029) usado em `AceiteAtividade.texto_hash`,
`Calibracao.observacoes_hash`, `DispensaAceiteAtividade.motivo_hash`
etc precisa hashar IGUAL em Windows e Linux. Bug-classe: Win usa
CRLF, Linux LF. Sem canonicalizacao -> assinaturas digitais quebram.

≥3 testes: vetor fixo (regressao do hash), CRLF/LF determinismo,
NFC/NFD determinismo, hash hex de 64 chars valido.
"""

from __future__ import annotations

import re

from src.domain.operacao.os.regras import hash_texto_canonicalizado


def test_inv_doc_canon_001_hash_hex_64_chars_valido():
    """Hash sempre eh SHA-256 hex (64 chars lowercase)."""
    h = hash_texto_canonicalizado("texto qualquer")
    assert re.fullmatch(r"[0-9a-f]{64}", h)


def test_inv_doc_canon_001_crlf_e_lf_geram_mesmo_hash():
    """Win (CRLF) e Linux (LF) -> mesmo hash."""
    assert hash_texto_canonicalizado(
        "Aceito\r\no servico tecnico realizado.\r\n"
    ) == hash_texto_canonicalizado("Aceito\no servico tecnico realizado.\n")


def test_inv_doc_canon_001_nfd_e_nfc_geram_mesmo_hash():
    """Acentos compostos (NFC) ou decompostos (NFD) -> mesmo hash."""
    nfd = "Açao tecnica concluída"  # 'a' + combining cedilla, 'i' + combining acute
    nfc = "Açao tecnica concluída"  # compostos
    assert hash_texto_canonicalizado(nfd) == hash_texto_canonicalizado(nfc)


def test_inv_doc_canon_001_trailing_whitespace_irrelevante():
    """Editor que insere trailing space nao altera hash."""
    assert hash_texto_canonicalizado(
        "Aceito o servico.   \nObservacao normal aqui.\t"
    ) == hash_texto_canonicalizado(
        "Aceito o servico.\nObservacao normal aqui."
    )
