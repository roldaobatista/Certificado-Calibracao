"""Helpers QR HMAC versionado — Marco 2 SEC-QR-001 / INV-051.

Helper UNICO de geracao e verificacao do hash do QR Code de equipamento.
Centralizado para que o hook `.claude/hooks/qr-hmac-check.sh` possa
permitir `hmac.new(settings.QR_HMAC_KEY_REGISTRO.*)` SOMENTE neste
arquivo (defesa em profundidade contra ataque pre-imagem via desvio
em outro modulo).

Invariantes que este modulo materializa:
- **SEC-QR-001**: HMAC-SHA256 com chave VERSIONADA. Prefixo `qrN:`
  permite rotacao de chave sem invalidar etiquetas fisicas ja impressas.
- **INV-051**: payload do hash e `<equipamento_id>|<tenant_id>|<emitido_em_iso>`;
  >=22 chars (>=128 bits entropia).
- **INV-EQP-QR-NUNCA-RECOMPUTA**: `verificar_qr_hash_em_tabela` SEMPRE
  consulta a tabela `QRCode` por igualdade do hash inteiro (UNIQUE index);
  NUNCA recomputa HMAC para validacao. Recomputacao so existe em
  `gerar_qr_hash_versionado` (na hora de criar o registro).

Referencias spec: AC-EQP-001-5; review tech-lead TL1; review advogado
A1/A3; review corretora P-EQP-S2.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from django.conf import settings

if TYPE_CHECKING:
    from .models import QRCode


def _payload_canonico(
    equipamento_id: UUID | str, tenant_id: UUID | str, emitido_em: datetime
) -> bytes:
    """Monta o payload canonico que entra no HMAC.

    Ordem fixa `<equipamento_id>|<tenant_id>|<iso_8601>`; ISO com
    timezone (`emitido_em.isoformat()` ja inclui offset porque o
    Django armazena tudo em UTC com `USE_TZ=True`).
    """
    if equipamento_id is None or tenant_id is None or emitido_em is None:
        raise ValueError("gerar_qr_hash_versionado exige equipamento_id, tenant_id e emitido_em")
    return f"{equipamento_id}|{tenant_id}|{emitido_em.isoformat()}".encode()


def gerar_qr_hash_versionado(
    equipamento_id: UUID | str,
    tenant_id: UUID | str,
    emitido_em: datetime,
) -> str:
    """Calcula `qrN:base64url(HMAC-SHA256(payload, QR_HMAC_KEY_ativa))`.

    Retorno com >=22 chars no digest base64url (>=128 bits entropia —
    base64url de 32 bytes do SHA256 = 43 chars sem padding). Prefixado
    com `{ativa_id}:` (ex.: `qr1:...`) — `verificar_qr_hash_em_tabela`
    consulta a tabela por igualdade exata.

    USO EXCLUSIVO no momento de cadastrar QR (cadastro de equipamento
    ou re-emissao). Para VALIDAR um hash apresentado por scan, use
    `verificar_qr_hash_em_tabela` — NUNCA recompute.
    """
    registro = settings.QR_HMAC_KEY_REGISTRO
    msg = _payload_canonico(equipamento_id, tenant_id, emitido_em)
    digest_bytes = hmac.new(registro.chave_ativa(), msg, hashlib.sha256).digest()
    digest_b64 = base64.urlsafe_b64encode(digest_bytes).rstrip(b"=").decode("ascii")
    return f"{registro.ativa_id}:{digest_b64}"


def verificar_qr_hash_em_tabela(hash_apresentado: str) -> QRCode | None:
    """Resolve hash de scan QR consultando a tabela `QRCode` (INV-EQP-QR-NUNCA-RECOMPUTA).

    Consulta por igualdade EXATA do hash inteiro (UNIQUE index `hash`).
    Retorna o registro se existir, esta vigente e nao revogado; `None`
    caso contrario. PROIBIDO recomputar HMAC neste fluxo — defesa em
    profundidade contra ataque pre-imagem via debugging/migration de
    chave aposentada.

    Casos que retornam `None`:
    - hash invalido (sem prefixo `qrN:`)
    - hash nao existe na tabela (404 indistinguivel em endpoint publico)
    - hash existe mas `revogado_em` foi gravado (re-emissao posterior)
    - chave aposentada presente no registry mas nao existe registro na
      tabela com aquele hash (cenario impossivel em uso normal — quem
      gerou tinha que ter gravado no momento da criacao).
    """
    from .models import QRCode  # import local para evitar ciclo no apps loading

    if not hash_apresentado or ":" not in hash_apresentado:
        return None
    return (
        QRCode.objects.filter(hash=hash_apresentado, revogado_em__isnull=True)
        .select_related("equipamento")
        .first()
    )
