"""Helper unico de sanitizacao de payload de `EventoDeOS` (SEG-M3-OS-03).

INV-OS-AUD-001 declara: "payload sanitizado NA ESCRITA — helper unico
`sanitizar_payload_evento_os()`". Bug-classe `sanitizar_payload_audit`
2026-05-19 provou que sanitizacao ad-hoc espalhada por 12 call-sites
e fragil — basta 1 dev esquecer `*_hash` e vazar PII em audit imutavel 25a.

Este helper centraliza o pattern:
1. Rejeita chaves PII conhecidas (cliente_id, tecnico_id, ator_id puros,
   nome/email/documento/telefone) — raise `PayloadPIIError`.
2. Aceita `*_hash` e `*_id_estrutural` (UUIDs surrogate sao chaves tecnicas).
3. Hasheia payload sanitizado via SHA-256 hex (vetor de regressao
   deterministico cross-platform — INV-DOC-CANON-001).

Uso correto pelos use cases (Fase 5 + 8 + 10):
    payload_data, payload_hash = sanitizar_payload_evento_os({
        "atividade_id": str(atividade.id),
        "tipo": "calibracao",
        "tipo_predominante": "calibracao",
        "transitou_para_concluida": True,
    })
    repository.publicar_evento(EventoDeOSSnapshot(
        ...
        payload_hash=payload_hash,
        payload_data=payload_data,
        ...
    ))

Migracao dos 12 call-sites legados (use_cases.py *.py) eh GATE Wave A
(`GATE-OS-SANITIZER-HELPER-MIGRACAO`) — cada call-site atual ja tem
marker `# audit-pii-salt: skip -- payload sanitizado` ad-hoc; helper
disponivel pra calls novos sem quebrar contratos existentes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Chaves proibidas em payload de evento — vazariam PII em audit 25a.
_CHAVES_PII_PROIBIDAS = frozenset(
    {
        "cliente_id",  # use cliente_referencia_hash ou *_hash
        "tecnico_id",  # use tecnico_id_hash quando publicar fora bounded-context
        "ator_id",  # use actor_id_hash
        "executor_id",  # use executor_id_hash
        "nome",
        "documento",
        "cpf",
        "cnpj",
        "email",
        "telefone",
        "endereco",
        "geo_lat",  # precisao alta proibida em audit (INV-OS-GEO-001 item c)
        "geo_long",
        "razao",  # use razao_hash
        "motivo",  # use motivo_hash
        "observacao",  # texto livre — use *_hash se relevante
        "texto",  # idem
        "razao_nao_conformidade",  # use *_hash
        "causa_raiz",  # use causa_raiz_hash
        "acao_corretiva",  # use acao_corretiva_hash
    }
)


class PayloadPIIError(ValueError):
    """Payload de evento contem chave PII direta — abortar antes de gravar."""


def sanitizar_payload_evento_os(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Sanitiza payload + retorna (payload, hash_sha256_hex).

    Rejeita chaves PII proibidas com `PayloadPIIError`. Caller DEVE passar
    *_hash em vez de UUIDs/textos crus quando o campo for PII.

    Hash deterministico cross-platform: json.dumps com sort_keys + UTF-8.
    """
    chaves_violadas = set(payload.keys()) & _CHAVES_PII_PROIBIDAS
    if chaves_violadas:
        raise PayloadPIIError(
            f"sanitizar_payload_evento_os: chaves PII proibidas {chaves_violadas}. "
            "Use sufixo `_hash` ou `_id_estrutural` (UUID surrogate)."
        )
    canonico = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    payload_hash = hashlib.sha256(  # audit-pii-salt: skip -- fingerprint de payload ja sanitizado (chaves PII rejeitadas acima)
        canonico.encode("utf-8")
    ).hexdigest()
    return payload, payload_hash
