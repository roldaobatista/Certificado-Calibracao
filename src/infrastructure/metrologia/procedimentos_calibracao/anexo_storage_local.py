"""Adapter local de storage do anexo PDF (M7 T-PROC-034 — MVP dogfooding).

Implementa `AnexoStoragePort` persistindo o binário em filesystem local,
content-addressed por sha256. O B2 WORM real é diferido (GATE-PROC-ANEXO-B2 —
`project_deploy_so_quando_roldao_quiser` + `project_sem_contratacoes_externas`).
O sha256 é recalculado SERVER-SIDE no use case/view (INV-PROC-007) — este adapter
só guarda o binário e devolve a chave opaca.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from django.conf import settings


def _base_dir() -> Path:
    base = getattr(
        settings,
        "PROCEDIMENTO_ANEXO_DIR",
        Path(tempfile.gettempdir()) / "afere_procedimento_anexos",
    )
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


class AnexoStorageLocal:
    """Persiste o PDF content-addressed (`<sha256>.pdf`). Idempotente por conteúdo."""

    def salvar(self, *, pdf_bytes: bytes, nome_sugerido: str) -> str:
        digest = hashlib.sha256(pdf_bytes).hexdigest()  # audit-pii-salt: skip -- sha256 de binario de PDF (content-addressing de documento controlado), NAO e PII
        destino = _base_dir() / f"{digest}.pdf"
        if not destino.exists():
            destino.write_bytes(pdf_bytes)
        return f"procedimento_anexo/{digest}.pdf"


def obter_anexo_storage() -> AnexoStorageLocal:
    """Factory da porta (tests podem monkeypatch para um fake em memória)."""
    return AnexoStorageLocal()
