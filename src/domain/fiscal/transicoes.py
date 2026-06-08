"""Máquina de estados + hash probatório do domínio fiscal (Fatia 1a — T-FIS-013).

D-FIS-3 (máquina de estados):
    PENDING → AUTHORIZED | REJECTED
    AUTHORIZED → CANCELED
    REJECTED, CANCELED → (terminais)

D-FIS-4 (cancelamento): é uma transição de estado (a linha reflete o estado atual)
+ evento WORM append-only na cadeia hash (a aplicação publica). A imutabilidade
probatória vem do `snapshot_hash` canonicalizado (ADR-0029) + hash versionado
(ADR-0064), não de proibir o UPDATE da coluna `status`.

`network_timeout` do provider NÃO entra aqui: é erro de transporte
(`ProviderTimeoutError`), nenhuma nota é persistida (a aplicação faz `falhar_chave`
+ 503/504). Funções PURAS — sem I/O, sem Django.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)

from .enums import InvoiceStatus
from .erros import MotivoCancelamentoInvalidoError, TransicaoInvalidaError

# Transições válidas: estado atual → conjunto de destinos permitidos.
_TRANSICOES: Mapping[InvoiceStatus, frozenset[InvoiceStatus]] = {
    InvoiceStatus.PENDING: frozenset(
        {InvoiceStatus.AUTHORIZED, InvoiceStatus.REJECTED}
    ),
    InvoiceStatus.AUTHORIZED: frozenset({InvoiceStatus.CANCELED}),
    InvoiceStatus.REJECTED: frozenset(),
    InvoiceStatus.CANCELED: frozenset(),
}

MOTIVO_CANCELAMENTO_MIN = 30  # caracteres (AC-FIS-003-1)


def validar_transicao(atual: InvoiceStatus, novo: InvoiceStatus) -> None:
    """Levanta `TransicaoInvalidaError` se `atual → novo` não é permitida."""
    if novo not in _TRANSICOES.get(atual, frozenset()):
        raise TransicaoInvalidaError(
            f"transição inválida: {atual.value} → {novo.value}"
        )


def validar_motivo_cancelamento(motivo: str) -> None:
    """Motivo de cancelamento exige ≥30 caracteres (AC-FIS-003-1)."""
    if len(motivo.strip()) < MOTIVO_CANCELAMENTO_MIN:
        raise MotivoCancelamentoInvalidoError(
            f"motivo de cancelamento exige ≥{MOTIVO_CANCELAMENTO_MIN} caracteres"
        )


def snapshot_hash_nfse(
    *,
    tenant_id: str,
    origem_id: str,
    versao: int,
    tipo_servico: str,
    perfil_no_evento: str,
    valor_centavos: int,
    cliente_referencia_hash: str,
    provider_invoice_id: str | None,
    certificado_id: str | None,
    declaracao_id: str | None,
    tipo_acreditacao_vinculo: str | None,
    status: str,
) -> str:
    """Hash versionado canonicalizado do documento (ADR-0029/0064 — tamper-evidence).

    Determinístico: mesma entrada → mesmo hash. Placeholder SHA-256 (mesmo padrão
    da calibração/certificados); quando `infrastructure/.../hash_kms.py` existir,
    troca por HMAC com chave KMS. UUID/Decimal já chegam como `str` (json não
    serializa esses tipos)."""
    payload = {
        "tenant_id": tenant_id,
        "origem_id": origem_id,
        "versao": versao,
        "tipo_servico": tipo_servico,
        "perfil_no_evento": perfil_no_evento,
        "valor_centavos": valor_centavos,
        "cliente_referencia_hash": cliente_referencia_hash,
        "provider_invoice_id": provider_invoice_id,
        "certificado_id": certificado_id,
        "declaracao_id": declaracao_id,
        "tipo_acreditacao_vinculo": tipo_acreditacao_vinculo,
        "status": status,
    }
    digest = hashlib.sha256(canonicalizar_payload_para_hmac(payload)).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)
