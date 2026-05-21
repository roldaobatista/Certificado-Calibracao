"""Geracao de PDF da etiqueta do equipamento (T-EQP-002 / AC-EQP-001-2).

Renderiza template HTML+CSS via WeasyPrint (TL1 tech-lead), consumindo
o hash do `QRCode` da fundacao T-EQP-006 (SEC-QR-001). Se o equipamento
ainda nao tem QRCode vigente, cria UM agora — idempotente via UNIQUE
hash (re-emissao explicita usa revogar_qrcode_anterior).

Anti-PII (revisao spec AC-EQP-001-2 + INV-051):
- Template NAO inclui nome do cliente, localizacao, historico.
- Inclui: TAG, numero_serie, fabricante, modelo, nome_fantasia tenant
  (emitente — equivalente ao logo).
- Nada vai pro QR Code: o que entra ali e SO o hash opaco (rastreio
  via tabela `equipamentos_qrcode` — INV-EQP-QR-NUNCA-RECOMPUTA).

Cache 60s (AC-EQP-001-2): aplicado no header do response em viewset.

NAO-OBJETIVO: este service NAO grava evento de auditoria de visualizacao
(quem viu/imprimiu a etiqueta) — isso e feito em camada anterior via
`AcessoDadosCliente` no viewset (T-EQP-024 da ficha 360).
"""

from __future__ import annotations

import base64
import io
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import qrcode
import qrcode.image.pil
from django.db import transaction
from django.template.loader import render_to_string
from weasyprint import HTML

from .services_qr import gerar_qr_hash_versionado

if TYPE_CHECKING:
    from .models import Equipamento, QRCode


def _gerar_qr_png_base64(payload: str, box_size: int = 8) -> str:
    """Renderiza o payload como PNG base64-encoded pra embed via data: URI.

    `box_size=8` produz QR de ~280px (suficiente pra etiqueta 32mm a
    300 DPI). `error_correction=H` (30%) tolera amassamento/sujeira
    da etiqueta fisica.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img: qrcode.image.pil.PilImage = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@transaction.atomic
def garantir_qrcode_vigente(equipamento: Equipamento) -> QRCode:
    """Retorna o QRCode vigente do equipamento (cria se ausente).

    Idempotente: se ja existe registro com `revogado_em IS NULL`,
    retorna esse. Caso contrario, gera novo hash via
    `gerar_qr_hash_versionado` e grava. Race-condition acolhida pela
    UNIQUE no `hash` (cripto-impossivel colidir; em concorrencia
    rarissima o segundo cria sobreviveria via SELECT FOR UPDATE).
    """
    from .models import QRCode  # import local para evitar ciclo

    vigente = (
        QRCode.objects.select_for_update()
        .filter(equipamento=equipamento, revogado_em__isnull=True)
        .first()
    )
    if vigente is not None:
        return vigente

    emitido = datetime.now(UTC)
    novo = QRCode.objects.create(
        tenant=equipamento.tenant,
        equipamento=equipamento,
        hash=gerar_qr_hash_versionado(equipamento.id, equipamento.tenant_id, emitido),
        emitido_em=emitido,
    )
    return novo


def gerar_etiqueta_pdf(equipamento: Equipamento) -> bytes:
    """Renderiza a etiqueta do equipamento em PDF (60mm x 40mm, 2 colunas).

    Layout: coluna esquerda = QR Code (32mm); coluna direita = TAG +
    NS + fabricante + modelo + nome_fantasia do tenant (rodape). Sem
    PII de cliente (vide doc de modulo).
    """
    qrcode_obj = garantir_qrcode_vigente(equipamento)
    qr_png_base64 = _gerar_qr_png_base64(qrcode_obj.hash)
    html = render_to_string(
        "equipamentos/etiqueta_qr.html",
        {
            "tag": equipamento.tag,
            "numero_serie": equipamento.numero_serie,
            "fabricante": equipamento.fabricante,
            "modelo": equipamento.modelo,
            "tenant_nome": equipamento.tenant.nome_fantasia,
            "qr_png_base64": qr_png_base64,
        },
    )
    pdf_bytes: bytes = HTML(string=html).write_pdf()
    return pdf_bytes
