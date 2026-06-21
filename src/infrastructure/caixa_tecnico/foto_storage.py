"""Adapter real do ``FotoComprovanteStoragePort`` (Fatia 3a — T-CT-040).

Pipeline foto-comprovante (D-CT-4 / TL-CT-01/02 / ADV-CT-03/04):
  1. valida tipo: JPG/PNG + MIME allowlist + ≤5MB.
  2. **EXIF strip** obrigatório via Pillow (decode + re-encode) — o re-encode é o
     que remove EXIF/GPS. EXIF **nunca** vira canal de GPS (D-CT-6 / INV-LGPD-CONSENT-001).
  3. ``foto_hash = HMAC-tenant(sha256(bytes pós-strip))`` (ADR-0064 / D-CT-4) — via
     ``hashear_pii_com_salt_tenant`` sobre o sha256-hex dos bytes limpos; guarda só
     o hexdigest do HMAC (separa por tenant → fotos idênticas cross-tenant coexistem).
  4. content-address: ``<MEDIA_ROOT>/caixa_tecnico/<tenant>/<hmac[:2]>/<hmac>``.
  5. ``salvar`` idempotente (``if not exists`` — replay não re-grava — D-CT-4/5).

NÃO é ``AnexoStoragePort`` (que é p/ PDF). Storage local Wave A; B2 = GATE pré-prod.

Refs: T-CT-040; D-CT-4/5/6; ADR-0064; INV-CT-FOTO-001; INV-CT-FOTO-DEDUP-001;
INV-LGPD-CONSENT-001 (EXIF não vira GPS). Molde: ``equipamentos/services_foto_storage.py``.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Final
from uuid import UUID

from django.conf import settings
from PIL import Image, ImageOps

from src.domain.caixa_tecnico.erros import (
    FotoComprovanteObrigatoria,
    FotoTipoInvalido,
)
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

LIMITE_BYTES_FOTO: Final[int] = 5 * 1024 * 1024  # 5MB (D-CT-4)
MIME_PERMITIDOS: Final[frozenset[str]] = frozenset({"image/jpeg", "image/png"})
_MIME_PARA_PIL_FORMAT: Final[dict[str, str]] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
}


class FotoComprovanteStorageLocal:
    """Implementação real de ``FotoComprovanteStoragePort`` (filesystem local Wave A)."""

    def __init__(self, base_dir: Path | None = None) -> None:
        raiz = base_dir if base_dir is not None else Path(getattr(settings, "MEDIA_ROOT", "media"))
        self._base_dir = Path(raiz) / "caixa_tecnico"

    def validar_e_processar(
        self,
        tenant_id: UUID,
        bytes_foto: bytes,
        mime_type: str,
    ) -> tuple[bytes, str]:
        """Valida → EXIF strip → HMAC-tenant. Retorna ``(bytes_limpos, foto_hash)``.

        Raises:
            FotoComprovanteObrigatoria: bytes vazios (412 FOTO_OBRIGATORIA).
            FotoTipoInvalido: MIME fora da allowlist, >5MB ou imagem corrompida (422).
        """
        if not bytes_foto:
            raise FotoComprovanteObrigatoria(
                "foto-comprovante ausente — bytes vazios (412 FOTO_OBRIGATORIA)"
            )
        if mime_type not in MIME_PERMITIDOS:
            raise FotoTipoInvalido(
                f"mime_type {mime_type!r} não permitido — use image/jpeg ou image/png"
            )
        if len(bytes_foto) > LIMITE_BYTES_FOTO:
            raise FotoTipoInvalido(
                f"foto {len(bytes_foto)} bytes excede o limite {LIMITE_BYTES_FOTO} (5MB)"
            )

        bytes_limpos = self._strip_exif(bytes_foto, mime_type)

        # foto_hash = HMAC-tenant sobre o sha256 dos bytes PÓS-strip (ADR-0064 / D-CT-4).
        # O sha256 é só content-address do binário; a separação por tenant (anti-correlação
        # cross-tenant — ADV-CT-04) vem do HMAC-tenant em hashear_pii_com_salt_tenant.
        digest_binario = hashlib.sha256(
            bytes_limpos
        ).hexdigest()  # audit-pii-salt: skip -- sha256 de BYTES de imagem pós-strip (binário, não PII textual); o salt por tenant vem do HMAC em hashear_pii_com_salt_tenant na linha seguinte (ADR-0064)
        foto_hash_completo = hashear_pii_com_salt_tenant(digest_binario, tenant_id)
        # Coluna foto_hash guarda só o hexdigest do HMAC (Wave A: key fixo; o prefixo vN
        # do helper é descartado — dedup/content-address operam sobre o hex puro).
        foto_hash = foto_hash_completo.split(":", 1)[1]
        return bytes_limpos, foto_hash

    def salvar(
        self,
        tenant_id: UUID,
        foto_hash: str,
        bytes_limpos: bytes,
    ) -> str:
        """Grava content-addressed por tenant. Idempotente (``if not exists`` — D-CT-4/5)."""
        destino = self._caminho(tenant_id, foto_hash)
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(bytes_limpos)
        return f"/media/caixa_tecnico/{tenant_id}/{foto_hash[:2]}/{foto_hash}"

    def _caminho(self, tenant_id: UUID, foto_hash: str) -> Path:
        return self._base_dir / str(tenant_id) / foto_hash[:2] / foto_hash

    @staticmethod
    def _strip_exif(conteudo: bytes, mime_type: str) -> bytes:
        """Remove EXIF (inclui GPS) via decode + re-encode (molde equipamentos)."""
        try:
            img_aberta = Image.open(io.BytesIO(conteudo))
            img_aberta.load()
        except Exception as exc:
            raise FotoTipoInvalido(f"imagem inválida/corrompida: {exc}") from exc

        img = ImageOps.exif_transpose(img_aberta)
        if img is None:
            raise FotoTipoInvalido("imagem inválida: Pillow retornou None")

        saida = io.BytesIO()
        fmt = _MIME_PARA_PIL_FORMAT[mime_type]
        if fmt == "JPEG":
            if img.mode in {"RGBA", "P"}:
                img = img.convert("RGB")
            # save SEM exif= → o re-encode descarta EXIF/GPS embutido.
            img.save(saida, format="JPEG", quality=85, optimize=True)
        else:
            img.save(saida, format="PNG", optimize=True)
        return saida.getvalue()
