"""HMAC sign — canonical string + assinatura HMAC-SHA256.

Implementa INV-WEBHOOK-OUT-003 (F-C1 P3 retrofit / R-2 / TL-02).

Canonical string EXPLICITA cobre signature stripping/replay parcial:
    canonical = f"{timestamp}.{method}.{path}.{sha256_hex(body)}"

Headers gerados:
    X-Afere-Signature: sha256=<hex>
    X-Afere-Timestamp: <unix-int>
    X-Afere-Event-Id: <uuid>
    X-Afere-Algo: HMAC-SHA256-canonical-v1

Modulo puro — sem dependencia de httpx/Django. Testavel isoladamente.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from uuid import UUID

ALGO_NOME = "HMAC-SHA256-canonical-v1"
JANELA_TIMESTAMP_SEGUNDOS = 300  # 5min (anti-replay no consumer externo)


@dataclass(frozen=True)
class HeadersAssinatura:
    """Headers que o adapter adiciona na requisicao outbound.

    `timestamp_unix`: int (segundos desde epoch). Consumer externo valida
        que `abs(now - timestamp_unix) <= JANELA_TIMESTAMP_SEGUNDOS`.

    `assinatura_hex`: HMAC-SHA256 da canonical string, em hex lowercase.

    `event_id`: propagado do `RequisicaoWebhook.event_id`.
    """

    timestamp_unix: int
    assinatura_hex: str
    event_id: UUID

    def como_dict(self) -> dict[str, str]:
        """Materializa como dict pronto pra passar ao client HTTP."""
        return {
            "X-Afere-Signature": f"sha256={self.assinatura_hex}",
            "X-Afere-Timestamp": str(self.timestamp_unix),
            "X-Afere-Event-Id": str(self.event_id),
            "X-Afere-Algo": ALGO_NOME,
        }


def _sha256_hex(body_bytes: bytes) -> str:
    """SHA-256 hex (lowercase) do body."""
    return hashlib.sha256(body_bytes).hexdigest()


def _canonical_string(
    *,
    timestamp_unix: int,
    metodo: str,
    caminho: str,
    body_bytes: bytes,
) -> str:
    """Constroi a canonical string `{ts}.{method}.{path}.{sha256(body)}`.

    Metodo UPPERCASE. Path COMO recebido (sem normalizar — o consumer
    externo precisa ver exatamente o path que foi assinado).
    """
    return f"{timestamp_unix}.{metodo.upper()}.{caminho}.{_sha256_hex(body_bytes)}"


def assinar(
    *,
    metodo: str,
    caminho: str,
    body_bytes: bytes,
    chave_hmac: bytes,
    event_id: UUID,
    timestamp_unix: int | None = None,
) -> HeadersAssinatura:
    """Gera HeadersAssinatura para uma requisicao outbound.

    Argumentos:
        metodo: HTTP method (GET/POST/PUT/PATCH/DELETE).
        caminho: path da URL (path + query string, sem hostname).
        body_bytes: body serializado em bytes. Para GET, b"".
        chave_hmac: chave dedicada do destino (lookup por `destino_id` no
            adapter). NUNCA reutilizar entre destinos diferentes.
        event_id: UUID v4 propagado no header.
        timestamp_unix: opcional. Default = time.time() now. Util pra teste.
    """
    if timestamp_unix is None:
        timestamp_unix = int(time.time())

    canonical = _canonical_string(
        timestamp_unix=timestamp_unix,
        metodo=metodo,
        caminho=caminho,
        body_bytes=body_bytes,
    )
    assinatura_hex = hmac.new(
        chave_hmac, canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return HeadersAssinatura(
        timestamp_unix=timestamp_unix,
        assinatura_hex=assinatura_hex,
        event_id=event_id,
    )


def verificar(
    *,
    metodo: str,
    caminho: str,
    body_bytes: bytes,
    chave_hmac: bytes,
    assinatura_hex_recebida: str,
    timestamp_unix_recebido: int,
    agora_unix: int | None = None,
    janela_seg: int = JANELA_TIMESTAMP_SEGUNDOS,
) -> bool:
    """Verifica uma assinatura recebida (uso pelo consumer externo ou
    cross-check em teste).

    Constant-time compare via hmac.compare_digest.
    Rejeita se timestamp esta fora da janela (`agora ± janela_seg`).
    """
    if agora_unix is None:
        agora_unix = int(time.time())
    if abs(agora_unix - timestamp_unix_recebido) > janela_seg:
        return False

    canonical = _canonical_string(
        timestamp_unix=timestamp_unix_recebido,
        metodo=metodo,
        caminho=caminho,
        body_bytes=body_bytes,
    )
    assinatura_esperada = hmac.new(
        chave_hmac, canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(assinatura_esperada, assinatura_hex_recebida)
