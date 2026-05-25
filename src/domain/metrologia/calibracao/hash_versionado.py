"""Helpers crypto pra formato HashVersionado v<NN>$<base64> (P4 Fase 2 Batch B).

T-CAL-031..036. ADR-0064 + INV-HMAC-001..005.

Funções puras (sem KMS, sem rede, sem IO). Operam apenas em strings/bytes
no formato canonico. Chamada real ao KMS Multi-Region (AWS sa-east-1 ↔
us-east-1) fica em `src/infrastructure/calibracao/hash_kms.py` (Fase 5
use cases).

Por que separado em duas camadas:
  - Replay determinístico (ADR-0025 cl. 7.11) precisa rodar offline em CI,
    sem credenciais AWS. Esses helpers operam puro.
  - Auditoria pode verificar formato de hashes legados sem chave KMS atual.
  - Retenção 25a (ISO 17025 cl. 8.4) — verificacao precisa funcionar mesmo
    se hardware KMS de 2026 for desativado em 2051 (chave migrada).

Catalogo:
  - VERSAO_HMAC_ATUAL: int — versão da chave em produção (cravada
    em compose env HMAC_KEY_VERSION_<TENANT>).
  - parsear_hash_versionado(raw) -> (versao, hmac_bytes)
  - formatar_hash_versionado(versao, hmac_bytes) -> str
  - validar_versao(n)
  - canonicalizar_payload_para_hmac(dado_dict) -> bytes (JSON canónico)

INV-HMAC-001: HMAC-SHA256 com chave AES-256 em KMS MRK.
INV-HMAC-002: formato canónico v<NN>$<base64> validado por VO + helpers.
INV-HMAC-003: rotação anual de chave (KMS MRK preserva histórico).
INV-HMAC-004: retenção 25a (cl. 8.4 ISO 17025).
INV-HMAC-005: payload canonicalizado por canonicalizar_payload_para_hmac
  (replay determinístico — mesmo input = mesma assinatura, sempre).
"""

from __future__ import annotations

import base64
import json
import re
from typing import Final

# Versao da chave HMAC em producao. Cravada em config (HMAC_KEY_VERSION_<TENANT>).
# Comecou em 1 em 2026; rotacao anual (INV-HMAC-003).
VERSAO_HMAC_ATUAL: Final[int] = 1

# Mesmo padrao do VO HashVersionadoV0 (consistencia formato canónico).
_HASH_VERSIONADO_RE: Final[re.Pattern[str]] = re.compile(
    r"^v(\d{2})\$([A-Za-z0-9+/]+={0,2})$"
)

VERSAO_MIN: Final[int] = 1
VERSAO_MAX: Final[int] = 99

# HMAC-SHA256 = 32 bytes. Base64-encoded sem padding = 43 chars; com padding = 44.
HMAC_SHA256_BYTES: Final[int] = 32


class FormatoHashVersionadoInvalido(ValueError):
    """Formato canónico v<NN>$<base64> nao casa (INV-HMAC-002)."""


class VersaoForaDoIntervalo(ValueError):
    """Versao da chave HMAC fora de [VERSAO_MIN, VERSAO_MAX] (INV-HMAC-003)."""


def validar_versao(n: int) -> int:
    """Valida que n eh versao aceitavel da chave HMAC.

    Levanta VersaoForaDoIntervalo se fora de [1, 99]. Retorna n se ok
    (mantem fluxo funcional encadeavel).

    Por que limite 99: rotacao anual + retencao 25a + janela de migracao
    -> max ~30 versoes em 2051. Margem confortavel ate 99 evita reformato
    se durar mais que o previsto.
    """
    if not isinstance(n, int):
        raise TypeError(f"validar_versao espera int (achou {type(n).__name__})")
    if not (VERSAO_MIN <= n <= VERSAO_MAX):
        raise VersaoForaDoIntervalo(
            f"versao {n} fora de [{VERSAO_MIN}, {VERSAO_MAX}] (INV-HMAC-003)"
        )
    return n


def parsear_hash_versionado(raw: str) -> tuple[int, bytes]:
    """Parseia string v<NN>$<base64> em (versao, hmac_bytes).

    Retorna:
      (versao, hmac_bytes) onde:
        - versao: int em [1, 99]
        - hmac_bytes: bytes do HMAC decodificado (esperado 32 bytes pra
          HMAC-SHA256, mas helper aceita qualquer base64 valido pra
          permitir migracoes futuras de algoritmo).

    Levanta:
      FormatoHashVersionadoInvalido — quando regex nao casa OU base64
        contem caractere fora do alfabeto + padding RFC 4648.
      VersaoForaDoIntervalo — quando NN extraido nao esta em [1, 99].

    Uso:
      versao, hmac_bytes = parsear_hash_versionado("v01$3xZ8...")
    """
    if not isinstance(raw, str):
        raise FormatoHashVersionadoInvalido(
            f"parsear_hash_versionado espera str (achou {type(raw).__name__})"
        )
    m = _HASH_VERSIONADO_RE.match(raw)
    if not m:
        raise FormatoHashVersionadoInvalido(
            f"hash {raw!r} nao casa com formato v<NN>$<base64> (INV-HMAC-002)"
        )
    versao = int(m.group(1))
    validar_versao(versao)
    try:
        hmac_bytes = base64.b64decode(m.group(2), validate=True)
    except ValueError as e:
        # Padding sem caracteres invalidos -> tenta com padding inferido
        raise FormatoHashVersionadoInvalido(
            f"base64 invalido em hash {raw!r}: {e} (INV-HMAC-002)"
        ) from e
    return versao, hmac_bytes


def formatar_hash_versionado(versao: int, hmac_bytes: bytes) -> str:
    """Formata (versao, hmac_bytes) na string canónica v<NN>$<base64>.

    Usado pelo helper crypto KMS apos calcular HMAC-SHA256(payload, chave_v<NN>).

    Args:
      versao: int em [1, 99].
      hmac_bytes: bytes do HMAC. Comumente 32 bytes (HMAC-SHA256) mas
        helper aceita qualquer tamanho pra permitir migracao futura
        de algoritmo (somar versao garante separacao).

    Retorna:
      String v<NN>$<base64> com NN em 2 digitos (zero-padded) e base64
      RFC 4648 §3.2 com padding `=`.

    Levanta:
      VersaoForaDoIntervalo — versao fora de [1, 99].
      TypeError — hmac_bytes nao eh bytes.

    Uso:
      hash_str = formatar_hash_versionado(1, hmac_bytes)
      # hash_str == "v01$..."
    """
    validar_versao(versao)
    if not isinstance(hmac_bytes, bytes | bytearray):
        raise TypeError(
            f"formatar_hash_versionado espera bytes (achou "
            f"{type(hmac_bytes).__name__})"
        )
    b64 = base64.b64encode(bytes(hmac_bytes)).decode("ascii")
    return f"v{versao:02d}${b64}"


def canonicalizar_payload_para_hmac(dado: object) -> bytes:
    """Canonicaliza payload Python em bytes UTF-8 deterministicos.

    INV-HMAC-005 + ADR-0025 cl. 7.11 (replay deterministico): mesmo
    input -> mesma assinatura, sempre, em qualquer ordem de keys do
    dicionario, qualquer plataforma.

    Regras:
      - JSON RFC 8259
      - sort_keys=True (ordem alfabetica de chaves)
      - ensure_ascii=False (preserva acentos UTF-8 — INV-DOC-CANON-001 NFC)
      - separators=(',', ':') (sem espacos)
      - encode UTF-8 sem BOM

    Para tipos nao-JSON-nativos (Decimal, datetime, UUID), chamador
    converte ANTES (Decimal -> str, datetime.isoformat(), str(uuid)).

    Args:
      dado: qualquer tipo serializavel via json.dumps.

    Retorna:
      bytes do JSON canónico em UTF-8.

    Levanta:
      TypeError — tipo Python nao-JSON-nativo nao convertido.

    Uso:
      bytes_canon = canonicalizar_payload_para_hmac({"cliente_id": "a", "valor": "10.5"})
      hmac_bytes = hmac.new(chave, bytes_canon, sha256).digest()
    """
    try:
        texto = json.dumps(
            dado,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as e:
        raise TypeError(
            f"canonicalizar_payload_para_hmac: payload nao-serializavel "
            f"({e}). Converta Decimal/datetime/UUID pra str antes."
        ) from e
    return texto.encode("utf-8")
