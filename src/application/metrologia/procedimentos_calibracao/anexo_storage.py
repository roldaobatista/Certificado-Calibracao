"""Porta de storage do anexo PDF do procedimento (M7 T-PROC-034 / C-4).

1ª porta de storage real do projeto (decisão tech-lead): o binário do PDF do
documento controlado é persistido por um adapter (B2/filesystem em infra), e o
`sha256` é recalculado SERVER-SIDE (nunca confiar no hash do cliente — integridade
de documento controlado cl. 7.2.1). O domínio nunca conhece storage (ADR-0007).
"""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class AnexoStoragePort(Protocol):
    """Persiste o binário do PDF e devolve a chave opaca de storage."""

    def salvar(self, *, pdf_bytes: bytes, nome_sugerido: str) -> str:
        """Retorna `storage_key` opaca (ex.: caminho B2). NÃO calcula hash."""
        ...


def sha256_server_side(pdf_bytes: bytes) -> str:
    """sha256 hex do binário, recalculado server-side (INV-PROC-007). Fonte
    única — use case e view usam este helper, nunca o hash do payload."""
    return hashlib.sha256(pdf_bytes).hexdigest()  # audit-pii-salt: skip -- sha256 de binario de PDF (integridade de documento controlado cl. 7.2.1), NAO e PII; salt por tenant nao se aplica a conteudo de arquivo
