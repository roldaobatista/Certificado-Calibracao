"""Service de storage de foto de recebimento (T-EQP-052 / AC-EQP-006-5).

Responsabilidades:
1. Validar MIME (`image/jpeg` | `image/png`) — defesa contra upload de
   binario arbitrario.
2. Validar tamanho ≤5MB.
3. **EXIF strip** via Pillow (corretora RAT-EQP-FOTO / TL2): remove
   metadados EXIF (geolocalizacao, modelo de camera, timestamps,
   thumbnail embutido) re-codificando o binario.
4. Calcular SHA-256 do binario FINAL pos-strip (P-EQP-S3 / AC-EQP-006-10).
5. Gerar `storage_key` UUID opaco.
6. Persistir em `EquipamentoRecebimentoFoto` (BYTEA inline Marco 2;
   Wave A migra para B2 GATE-EQP-2).

NAO faz OCR anti-CPF (V2 — Marco 2 confia em allowlist semantica UX +
aviso textual ao operador conforme `aviso-foto-recebimento.md` v1.0).
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Final
from uuid import UUID, uuid4

from PIL import Image, ImageOps

LIMITE_BYTES_FOTO: Final[int] = 5 * 1024 * 1024  # 5MB
MIME_PERMITIDOS: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png"}
)
MIME_PARA_PIL_FORMAT: Final[dict[str, str]] = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
}


class FotoInvalida(Exception):
    """Base de erros do storage de foto."""


class MimeInvalido(FotoInvalida):
    """MIME nao em allowlist (jpeg/png)."""


class TamanhoExcedido(FotoInvalida):
    """Binario >5MB."""


class ConteudoCorrompido(FotoInvalida):
    """Pillow falha em decodificar — binario nao e imagem valida."""


@dataclass(frozen=True)
class ResultadoSalvarFoto:
    storage_key: str
    foto_sha256: str
    mime_type: str
    tamanho_bytes: int


def _strip_exif(conteudo_bytes: bytes, mime_type: str) -> bytes:
    """Remove EXIF via decodificacao + re-encode."""
    try:
        img = Image.open(io.BytesIO(conteudo_bytes))
        img.load()
    except Exception as exc:
        raise ConteudoCorrompido(f"imagem invalida: {exc}") from exc

    img = ImageOps.exif_transpose(img)
    if img is None:
        raise ConteudoCorrompido("imagem invalida: PIL retornou None")
    saida = io.BytesIO()
    fmt = MIME_PARA_PIL_FORMAT[mime_type]
    if fmt == "JPEG":
        if img.mode in {"RGBA", "P"}:
            img = img.convert("RGB")
        img.save(saida, format="JPEG", quality=85, optimize=True)
    else:
        img.save(saida, format="PNG", optimize=True)
    return saida.getvalue()


def _hash_binario_foto(binario: bytes) -> str:
    """SHA-256 hex do binario da foto.

    audit-pii-salt: skip -- SHA-256 de BINARIO de imagem (nao PII textual);
    P-EQP-S3 / RAT-EQP-FOTO exige hash deterministico cross-tenant para
    integridade WORM 25a (LGPD art. 16 retencao de evidencia) + audit
    forense corretora. Salt por tenant inviabilizaria deduplicacao +
    comparacao cross-tenant em peritagem.
    """
    return hashlib.sha256(binario).hexdigest()  # audit-pii-salt: skip -- binario foto (nao PII textual); P-EQP-S3 RAT-EQP-FOTO hash deterministico WORM 25a


@dataclass(frozen=True)
class FotoPreparada:
    """Saida de `preparar_foto`: metadados + binario limpo, sem persistencia.

    Caller usa pra incluir `storage_key` + `foto_sha256` no INSERT do
    `EquipamentoRecebimento` (evita UPDATE pos-INSERT bloqueado pelo
    trigger imutabilidade T-EQP-058) e depois chama
    `persistir_foto_preparada` para gravar o BLOB na tabela 1:1.
    """

    storage_key: str
    foto_sha256: str
    mime_type: str
    bytes_limpos: bytes
    tamanho_bytes: int


def preparar_foto(
    *, conteudo_bytes: bytes, mime_type: str
) -> FotoPreparada:
    """Valida + EXIF strip + sha256 + gera storage_key opaco.

    NAO persiste — caller chama `persistir_foto_preparada` apos criar
    o `EquipamentoRecebimento` com `foto_storage_key` + `foto_sha256`
    do retorno.
    """
    if mime_type not in MIME_PERMITIDOS:
        raise MimeInvalido(
            f"mime_type '{mime_type}' nao permitido. Permitidos: "
            f"{sorted(MIME_PERMITIDOS)}"
        )
    if len(conteudo_bytes) > LIMITE_BYTES_FOTO:
        raise TamanhoExcedido(
            f"binario {len(conteudo_bytes)} bytes excede limite "
            f"{LIMITE_BYTES_FOTO} (5MB)."
        )
    bytes_limpos = _strip_exif(conteudo_bytes, mime_type)
    foto_sha256 = _hash_binario_foto(bytes_limpos)
    storage_key = str(uuid4())
    return FotoPreparada(
        storage_key=storage_key,
        foto_sha256=foto_sha256,
        mime_type=mime_type,
        bytes_limpos=bytes_limpos,
        tamanho_bytes=len(bytes_limpos),
    )


def persistir_foto_preparada(
    *,
    tenant_id: UUID,
    recebimento_id: UUID,
    preparada: FotoPreparada,
) -> None:
    """Grava o BLOB da foto na tabela `EquipamentoRecebimentoFoto`.

    Deve ser chamado APOS criar `EquipamentoRecebimento` com
    `foto_storage_key = preparada.storage_key` (FK no INSERT, evita
    UPDATE pos-INSERT bloqueado pelo trigger T-EQP-058).
    """
    from src.infrastructure.equipamentos.models import (
        EquipamentoRecebimentoFoto,
    )

    EquipamentoRecebimentoFoto.objects.create(
        tenant_id=tenant_id,
        recebimento_id=recebimento_id,
        storage_key=preparada.storage_key,
        conteudo_bytes=preparada.bytes_limpos,
        mime_type=preparada.mime_type,
        tamanho_bytes=preparada.tamanho_bytes,
    )


def salvar_foto_recebimento(
    *,
    tenant_id: UUID,
    recebimento_id: UUID,
    conteudo_bytes: bytes,
    mime_type: str,
) -> ResultadoSalvarFoto:
    """[Legacy] Compatibilidade com chamadores antigos — internamente
    usa `preparar_foto` + `persistir_foto_preparada`. Desaconselhado
    para novos callers (precisa de UPDATE pos-INSERT do recebimento,
    o que e bloqueado pelo trigger T-EQP-058)."""
    preparada = preparar_foto(
        conteudo_bytes=conteudo_bytes, mime_type=mime_type
    )
    persistir_foto_preparada(
        tenant_id=tenant_id, recebimento_id=recebimento_id, preparada=preparada
    )
    return ResultadoSalvarFoto(
        storage_key=preparada.storage_key,
        foto_sha256=preparada.foto_sha256,
        mime_type=preparada.mime_type,
        tamanho_bytes=preparada.tamanho_bytes,
    )
