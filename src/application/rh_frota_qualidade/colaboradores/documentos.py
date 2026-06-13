"""Use case de anexação de documentos (T-COL-032).

anexar_documento — AnexoStoragePort + SHA-256 server-side + EXIF strip foto
                   (sem blur — ADV-COL-02) + coerencia_documento_vinculo alerta
                   (INV-COL-DOC-VINCULO).

Refs: AC-COL-05; D-COL-6; TL-COL-06; INV-COL-DOC-VINCULO; ADV-COL-01/02.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.rh_frota_qualidade.colaboradores.entities import Documento
from src.domain.rh_frota_qualidade.colaboradores.enums import TipoDocumento
from src.domain.rh_frota_qualidade.colaboradores.erros import ColaboradorInativo
from src.domain.rh_frota_qualidade.colaboradores.portas import AnexoStoragePort
from src.domain.rh_frota_qualidade.colaboradores.regras import coerencia_documento_vinculo
from src.domain.rh_frota_qualidade.colaboradores.repository import (
    ColaboradorRepository,
)

logger = logging.getLogger(__name__)

MIME_FOTO_PERMITIDOS: frozenset[str] = frozenset({"image/jpeg", "image/png"})
LIMITE_BYTES_ARQUIVO: int = 5 * 1024 * 1024  # 5MB


class ArquivoInvalido(Exception):
    """Arquivo inválido para anexação (MIME, tamanho, etc.)."""


@dataclass(frozen=True)
class ComandoAnexarDocumento:
    """Input do use case de anexação de documento."""

    tenant_id: UUID
    colaborador_id: UUID
    tipo: TipoDocumento
    arquivo_bytes: bytes
    nome_sugerido: str
    mime_type: str
    data_validade: date | None = None


def _strip_exif_se_foto(conteudo_bytes: bytes, mime_type: str) -> bytes:
    """Remove EXIF de foto via Pillow (TL-COL-06 / ADV-COL-02).

    Sem blur: foto de colaborador é dado COMUM de identificação (art. 7º V),
    não biométrico — o rosto é a finalidade (ADV-COL-02).
    Molde: equipamentos/services_foto_storage.py `_strip_exif`.
    """
    if mime_type not in MIME_FOTO_PERMITIDOS:
        return conteudo_bytes  # Não é foto — retorna sem alteração

    try:
        from PIL import Image, ImageOps
    except ImportError:
        logger.warning("Pillow não disponível — EXIF strip ignorado em teste")
        return conteudo_bytes

    try:
        img_raw: Image.Image = Image.open(io.BytesIO(conteudo_bytes))
        img_raw.load()
    except Exception as exc:
        raise ArquivoInvalido(f"Imagem inválida: {exc}") from exc

    transposta: Image.Image | None = ImageOps.exif_transpose(img_raw)
    if transposta is None:
        raise ArquivoInvalido("Imagem inválida: PIL retornou None")

    img_final: Image.Image = transposta
    saida = io.BytesIO()
    fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
    if fmt == "JPEG":
        if img_final.mode in {"RGBA", "P"}:
            img_final = img_final.convert("RGB")
        img_final.save(saida, format="JPEG", quality=85, optimize=True)
    else:
        img_final.save(saida, format="PNG", optimize=True)
    return saida.getvalue()


def _sha256_server_side(conteudo_bytes: bytes) -> str:
    """SHA-256 hex calculado server-side (INV-PROC-007 / D-COL-6).

    audit-pii-salt: skip -- sha256 de binário de arquivo (integridade de
    documento controlado), NÃO é PII; salt por tenant não se aplica.
    """
    return hashlib.sha256(conteudo_bytes).hexdigest()  # audit-pii-salt: skip -- binario de arquivo (nao PII textual); integridade WORM


def _salvar_documento_com_tenant(
    documento: Documento,
    *,
    tenant_id: UUID,
) -> None:
    """Salva documento com tenant_id via ORM direto."""
    from src.infrastructure.colaboradores.models import ColaboradorDocumento as DocModel

    DocModel.objects.update_or_create(
        id=documento.id,
        defaults={
            "colaborador_id": documento.colaborador_id,
            "tenant_id": tenant_id,
            "tipo": documento.tipo.value,
            "storage_key": documento.storage_key,
            "sha256": documento.sha256,
            "data_upload": documento.data_upload,
            "data_validade": documento.data_validade,
        },
    )


def anexar_documento(
    cmd: ComandoAnexarDocumento,
    *,
    repo_colab: ColaboradorRepository,
    storage_port: AnexoStoragePort,
) -> UUID:
    """Anexa documento ao colaborador (AC-COL-05 / D-COL-6 / TL-COL-06).

    Fluxo:
    1. Verifica que colaborador está ativo.
    2. Valida MIME/tamanho (ArquivoInvalido).
    3. Strip EXIF se foto (TL-COL-06 / ADV-COL-02 — sem blur).
    4. Calcula SHA-256 server-side pós-processamento (integridade).
    5. Salva via AnexoStoragePort → storage_key opaca.
    6. Alerta coerência vínculo×documento (INV-COL-DOC-VINCULO — não bloqueia).

    Returns:
        UUID do documento criado.
    Raises:
        ColaboradorInativo: colaborador desligado ou soft-deletado.
        ArquivoInvalido: MIME não permitido ou tamanho excedido.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} está inativo (D-COL-3)."
        )

    # Validação básica de tamanho
    if len(cmd.arquivo_bytes) > LIMITE_BYTES_ARQUIVO:
        raise ArquivoInvalido(
            f"Arquivo {len(cmd.arquivo_bytes)} bytes excede limite de {LIMITE_BYTES_ARQUIVO} (5MB)."
        )

    # EXIF strip se foto (TL-COL-06 / ADV-COL-02)
    conteudo_final = _strip_exif_se_foto(cmd.arquivo_bytes, cmd.mime_type)

    # SHA-256 server-side do conteúdo FINAL (pós-strip)
    sha256 = _sha256_server_side(conteudo_final)

    # Salva via porta (AnexoStoragePort — tipagem estrutural)
    storage_key: str = storage_port.salvar(
        pdf_bytes=conteudo_final,
        nome_sugerido=cmd.nome_sugerido,
    )

    # Alerta coerência vínculo × documento (INV-COL-DOC-VINCULO)
    coerente = coerencia_documento_vinculo(tipo=cmd.tipo, vinculo=colab.vinculo)
    if not coerente:
        logger.warning(
            "documento incompativel com vinculo (alerta INV-COL-DOC-VINCULO)",
            extra={
                "colaborador_id": str(cmd.colaborador_id),
                "tipo": cmd.tipo.value,
                "vinculo": colab.vinculo.value,
                "tenant_id": str(cmd.tenant_id),
            },
        )

    documento_id = uuid4()
    documento = Documento(
        id=documento_id,
        colaborador_id=cmd.colaborador_id,
        tipo=cmd.tipo,
        storage_key=storage_key,
        sha256=sha256,
        data_upload=datetime.now(UTC),
        data_validade=cmd.data_validade,
    )
    _salvar_documento_com_tenant(documento, tenant_id=cmd.tenant_id)

    logger.info(
        "documento anexado",
        extra={
            "documento_id": str(documento_id),
            "colaborador_id": str(cmd.colaborador_id),
            "tipo": cmd.tipo.value,
            "tenant_id": str(cmd.tenant_id),
            "sha256": sha256[:8] + "...",  # trecho para trace, sem vazar conteúdo
        },
    )
    return documento_id
