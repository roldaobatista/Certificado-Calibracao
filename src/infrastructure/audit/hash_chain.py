"""sha256 da linha de auditoria — encadeia com hash_atual da anterior.

Formula (ADR-0002 §6, faseamento-foundation-waves §2):
    hash_atual = sha256(hash_anterior_bytes || payload_canonicalizado_bytes)

Onde:
- hash_anterior: hexdigest da linha anterior (64 chars). Se nao houver
  anterior (primeira linha), usa string vazia ""
- payload_canonicalizado: JSON canonicalizado (canonicalizar.py)

Cada elo amarra o anterior — adulterar 1 linha quebra a cadeia em todas as
seguintes. Verificacao integral roda no Marco 8 (drill).
"""

from __future__ import annotations

import hashlib


def calcular_hash(hash_anterior: str | None, payload_canonicalizado: str) -> str:
    """Concatena (hash_anterior || payload) e devolve sha256 hex."""
    anterior_bytes = (hash_anterior or "").encode("utf-8")
    payload_bytes = payload_canonicalizado.encode("utf-8")
    return hashlib.sha256(anterior_bytes + payload_bytes).hexdigest()
