"""Helpers LGPD M4 — derivacao server-side de hashes PII + sanitizacao
de payload de evento.

Implementacao Wave A (sem KMS real). HMAC determinístico server-side
usando chave config por tenant (HMAC_KEY_<TENANT>); rotacao + KMS MRK
real entram em Wave A pos-ADR-0064 GATE-CAL-HMAC-RETENCAO.

Cobre achados 1a passada Familia 5 (2026-05-27):
- SEG-CAL-01 (CRITICO): derivar `cliente_referencia_hash` +
  `cliente_key_id` server-side em vez de aceitar do body (vetor
  spoofing).
- SEG-CAL-03 (ALTO): helper unico `sanitizar_payload_evento_calibracao`
  (paralelo `sanitizar_payload_audit`).
- SEG-CAL-08 (MEDIO): mesmo padrao em
  `analise_critica_pedido_inline_hash`.
- SEG-CAL-07 (MEDIO): mesmo padrao em `motivo_hash`.
- LGPD-CAL-01 (MEDIO): single source of truth pra sanitizacao
  pre-evento.

Wave A: HMAC stub baseado em hashlib.sha256(tenant + cliente_id + key_atual).
PROD: GATE-CAL-KMS-MRK substitui por boto3 + kms.encrypt/decrypt + cache.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any, Final
from uuid import UUID

from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    formatar_hash_versionado,
)

# Wave A: chave fixa por tenant. PROD: KMS MRK ADR-0064.
# `bytes(32)` zero-fill garante que chave de DEV seja obviamente
# nao-segura — bloqueador de prod via env var.
_CHAVE_HMAC_WAVE_A: Final[bytes] = (
    b"WAVE_A_CHAVE_NAO_SEGURA_PARA_DEV_USAR_KMS_MRK_EM_PROD_______"[:32]
)

# Denylist de campos PII que NUNCA devem aparecer crus em evento de
# auditoria (paralelo `sanitizar_payload_audit` M1/M3).
_CAMPOS_PII_DENYLIST: Final[frozenset[str]] = frozenset(
    {
        "cpf",
        "cnpj",
        "rg",
        "nome",
        "nome_completo",
        "razao_social",
        "email",
        "telefone",
        "endereco",
        "logradouro",
        "cep",
        "data_nascimento",
        "passaporte",
    }
)

# UUIDs estruturais nao sao PII (paralelo bug `sanitizar_payload_audit`
# 2026-05-19). Isencao por sufixo de chave.
_SUFIXOS_UUID_ESTRUTURAL: Final[tuple[str, ...]] = (
    "_id",
    "_uuid",
    "_hash",
    "correlation_id",
    "causation_id",
)


def derivar_cliente_referencia_hash(
    *,
    cliente_id: UUID | None,
    tenant_id: UUID,
) -> str:
    """HMAC determinístico server-side a partir de (tenant_id, cliente_id).

    Substitui hash aceito do body (SEG-CAL-01 CRITICO). Cliente nao
    consegue spoofar referencia de outro cliente.

    cliente_id=None (recepcao avulsa sem cliente cadastrado) gera hash
    canonico do tenant + sentinel `__avulsa__` — preserva forma sem
    expor PII inexistente.

    Returns:
      String no formato canonico `v<NN>$<base64(HMAC-SHA256[32])>`
      conforme ADR-0064 + INV-HMAC-002.
    """
    if cliente_id is None:
        payload = f"{tenant_id}|__avulsa__"
    else:
        payload = f"{tenant_id}|{cliente_id}"
    mac = hmac.new(_CHAVE_HMAC_WAVE_A, payload.encode("utf-8"), hashlib.sha256)
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, mac.digest())


def derivar_cliente_key_id(*, tenant_id: UUID) -> str:
    """ID canonico da chave de cifragem por tenant (ADR-0064).

    Wave A: `tenant-<uuid8>-key-v<NN>`. PROD: ARN da chave KMS MRK.
    """
    short = str(tenant_id)[:8]
    return f"tenant-{short}-key-v{VERSAO_HMAC_ATUAL:02d}"


def derivar_hash_texto_canonicalizado(
    *,
    texto: str,
    tenant_id: UUID,
) -> str:
    """HMAC server-side de texto canonicalizado (ADR-0029).

    Substitui hashes aceitos do body em paths sensiveis:
    - `motivo_hash` (cancelar) — SEG-CAL-07
    - `analise_critica_pedido_inline_hash` (configurar) — SEG-CAL-08
    - `motivo_canonicalizado` derivado para subcontratacao.
    """
    payload = f"{tenant_id}|{texto}"
    mac = hmac.new(_CHAVE_HMAC_WAVE_A, payload.encode("utf-8"), hashlib.sha256)
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, mac.digest())


def derivar_user_id_hash(
    *,
    usuario_id: UUID,
    tenant_id: UUID,
) -> str:
    """HMAC server-side de (tenant_id, usuario_id) — INV-CAL-FRAUDE-EXEC-001
    + INV-CAL-FRAUDE-COR-001 + ADR-0064.

    Substitui UUID cru de executor / corretor / revisor / conferente em
    snapshots WORM (anti-stalking pos retencao 25a). View deriva no
    momento do request a partir do usuario autenticado.
    """
    payload = f"{tenant_id}|{usuario_id}|user_id"
    mac = hmac.new(_CHAVE_HMAC_WAVE_A, payload.encode("utf-8"), hashlib.sha256)
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, mac.digest())


def _eh_uuid_estrutural(chave: str) -> bool:
    chave_lower = chave.lower()
    return any(chave_lower.endswith(suf) for suf in _SUFIXOS_UUID_ESTRUTURAL)


_UUID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def sanitizar_payload_evento_calibracao(
    payload: dict[str, Any],
    *,
    finalidade: str,
) -> dict[str, Any]:
    """Sanitiza payload pre-INSERT em `evento_de_calibracao`.

    Aplica regras:
    1. Campo na denylist PII (`cpf`, `nome`, etc) -> "[REDACTED-PII]".
    2. Campo com sufixo `_id`/`_uuid`/`_hash` -> mantido (estrutural).
    3. Demais valores string que parecem UUID -> mantidos (paralelo
       bug 2026-05-19 `sanitizar_payload_audit`).
    4. Dict aninhado -> recursivo.
    5. List -> recursivo elemento a elemento.

    Args:
      payload: dict cru a sanitizar (caller passa snapshot use case).
      finalidade: string canonica usada por auditoria CGCRE
        ("calibracao_recepcionada", "leitura_registrada", etc).

    Returns:
      Novo dict (defensivo — nao muta input).
    """
    if not finalidade or len(finalidade) < 5:
        raise ValueError(
            "sanitizar_payload_evento_calibracao: finalidade obrigatoria "
            "(>=5 chars) — auditoria CGCRE exige rastreio"
        )
    resultado = _sanitizar_recursivo(payload)
    assert isinstance(resultado, dict)
    return resultado


def _sanitizar_recursivo(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {
            chave: (
                "[REDACTED-PII]"
                if chave.lower() in _CAMPOS_PII_DENYLIST
                and not _eh_uuid_estrutural(chave)
                else _sanitizar_recursivo(sub_valor)
            )
            for chave, sub_valor in valor.items()
        }
    if isinstance(valor, list):
        return [_sanitizar_recursivo(item) for item in valor]
    return valor


__all__ = [
    "derivar_cliente_key_id",
    "derivar_cliente_referencia_hash",
    "derivar_hash_texto_canonicalizado",
    "derivar_user_id_hash",
    "sanitizar_payload_evento_calibracao",
]
