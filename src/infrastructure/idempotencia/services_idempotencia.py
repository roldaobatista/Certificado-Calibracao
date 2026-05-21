"""Service de idempotencia (T-EQP-003 / P-EQP-T6).

API publica:
- `avaliar_chave_idempotencia(...)` -> `Avaliacao` sealed type.
- `concluir_chave(chave_id, response_status, response_body_resumo)`.
- `falhar_chave(chave_id, response_status)`.

Estados retornados:
- `ErroValidacao(http_status, detalhe)`:
    400 sem header / header nao-UUID
    409 chave expirada (criada_em+24h < now)
    422 mesma chave + payload_hash diferente
    425 chave em_processo (outra request ainda nao concluiu)
- `Replay(response_status, response_body_resumo)`: replay deterministico.
- `NovoProcessamento(chave_id)`: caller executa a operacao, depois chama
  `concluir_chave` ou `falhar_chave`.

Concorrencia: INSERT em `breaker_writer` (autocommit) — registro `em_processo`
fica visivel pra outras requests IMEDIATAMENTE, sem precisar do COMMIT da
transacao principal. Mesmo padrao de `audit/breaker.py` (T-CLI-104).
UNIQUE `(tenant_id, endpoint, chave)` detecta corrida: 2a request pega
IntegrityError, faz SELECT pra ver estado da 1a.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal
from uuid import UUID

from django.db import IntegrityError, connections
from django.utils import timezone

from src.infrastructure.audit.canonicalizar import canonicalizar

from .models import ChaveIdempotencia, StatusChaveIdempotencia

TTL_CHAVE = timedelta(hours=24)
"""TTL fixo da chave (P-EQP-T6). Apos expira_em, replay retorna 409."""

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# -----------------------------------------------------------------
# Tipos de retorno (sealed via Literal discriminator)
# -----------------------------------------------------------------
@dataclass(frozen=True)
class ErroValidacao:
    """Erro que vira HTTP response no caller."""

    tipo: Literal["erro"] = "erro"
    http_status: int = 400
    codigo: str = ""
    detalhe: str = ""
    headers: dict[str, str] | None = None


@dataclass(frozen=True)
class Replay:
    """1a chamada ja concluiu; caller deve devolver a mesma resposta."""

    tipo: Literal["replay"] = "replay"
    response_status: int = 200
    response_body_resumo: dict[str, Any] | None = None


@dataclass(frozen=True)
class NovoProcessamento:
    """Chave registrada como `em_processo`; caller executa operacao."""

    tipo: Literal["novo"] = "novo"
    chave_id: UUID | None = None


Avaliacao = ErroValidacao | Replay | NovoProcessamento


# -----------------------------------------------------------------
# Helpers privados
# -----------------------------------------------------------------
def _validar_header_uuid(valor: str | None) -> UUID | ErroValidacao:
    """Header `Idempotency-Key` deve ser UUID v4 canonico."""
    if not valor:
        return ErroValidacao(
            http_status=400,
            codigo="idempotency_key_ausente",
            detalhe="Header Idempotency-Key obrigatorio neste endpoint.",
        )
    if not _UUID_RE.match(valor.strip()):
        return ErroValidacao(
            http_status=400,
            codigo="idempotency_key_invalido",
            detalhe="Header Idempotency-Key deve ser UUID (formato 8-4-4-4-12).",
        )
    return UUID(valor.strip())


def _calcular_payload_hash(payload: dict[str, Any]) -> str:
    """SHA256-hex do payload canonicalizado.

    NAO e hash de PII — e fingerprint de PAYLOAD da requisicao (sem dados
    pessoais; campos como `equipamento_id` UUID, `chave` UUID, endpoint
    string). Usado pra detectar "mesma chave + payload diferente" -> 422.
    Sal por tenant nao se aplica.
    """
    canon = canonicalizar(payload).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()  # audit-pii-salt: skip -- fingerprint de payload (UUIDs/endpoint), nao PII


# -----------------------------------------------------------------
# API publica
# -----------------------------------------------------------------
def avaliar_chave_idempotencia(
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    chave_header: str | None,
    payload: dict[str, Any],
) -> Avaliacao:
    """Decide se a chamada e nova/replay/erro/concorrencia.

    Caller (view) reage:
    - `ErroValidacao` -> retorna HTTP com `http_status` + body `{detalhe}`.
    - `Replay` -> caller pode RE-EXECUTAR operacao determinante (ex:
      re-renderizar PDF) usando dados do `response_body_resumo`, ou
      simplesmente devolver 200 com o resumo.
    - `NovoProcessamento` -> caller executa operacao + chama `concluir_chave`.
    """
    header_uuid = _validar_header_uuid(chave_header)
    if isinstance(header_uuid, ErroValidacao):
        return header_uuid

    payload_hash = _calcular_payload_hash(payload)
    agora = timezone.now()

    existente: ChaveIdempotencia | None = (
        ChaveIdempotencia.objects.filter(
            tenant_id=tenant_id, endpoint=endpoint, chave=header_uuid
        ).first()
    )
    if existente is not None:
        return _avaliar_existente(existente, payload_hash, agora)

    # Tentativa de INSERT via conexao autocommit (visibilidade imediata
    # pra outras requests concorrentes).
    try:
        chave_id = _inserir_em_processo(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=endpoint,
            chave=header_uuid,
            payload_hash=payload_hash,
            criada_em=agora,
        )
    except IntegrityError:
        # Corrida: outra request inseriu entre o SELECT e o INSERT.
        # Re-le e avalia.
        existente = ChaveIdempotencia.objects.get(
            tenant_id=tenant_id, endpoint=endpoint, chave=header_uuid
        )
        return _avaliar_existente(existente, payload_hash, agora)

    return NovoProcessamento(chave_id=chave_id)


def _avaliar_existente(
    existente: ChaveIdempotencia,
    payload_hash_atual: str,
    agora: Any,
) -> Avaliacao:
    """Aplica a politica P-EQP-T6 a uma chave ja existente."""
    if existente.payload_hash != payload_hash_atual:
        return ErroValidacao(
            http_status=422,
            codigo="idempotency_key_payload_divergente",
            detalhe=(
                "Header Idempotency-Key ja foi usado com payload diferente "
                "neste endpoint. Gere uma nova chave para esta requisicao."
            ),
        )
    if existente.status == StatusChaveIdempotencia.EM_PROCESSO:
        return ErroValidacao(
            http_status=425,
            codigo="idempotency_key_em_processo",
            detalhe=(
                "Requisicao anterior com esta chave ainda esta em "
                "processamento. Tente novamente em alguns segundos."
            ),
            headers={"Retry-After": "1"},
        )
    if existente.expira_em < agora:
        return ErroValidacao(
            http_status=409,
            codigo="idempotency_key_expirada",
            detalhe=(
                "Header Idempotency-Key expirou (TTL 24h). Gere uma nova "
                "chave para reemitir esta operacao."
            ),
        )
    # Terminal (concluida ou falhada) + payload igual + dentro da janela -> replay.
    return Replay(
        response_status=existente.response_status or 200,
        response_body_resumo=existente.response_body_resumo or {},
    )


def _inserir_em_processo(
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    chave: UUID,
    payload_hash: str,
    criada_em: Any,
) -> UUID:
    """INSERT via `breaker_writer` (autocommit) com tenant context.

    Levanta `IntegrityError` se UNIQUE `(tenant_id, endpoint, chave)` violada.
    Visibilidade imediata pra outras requests (mesmo padrao audit/breaker.py).
    """
    expira_em = criada_em + TTL_CHAVE
    conn = connections["breaker_writer"]
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("SET LOCAL app.active_tenant_id = %s", [str(tenant_id)])
            cur.execute("SET LOCAL app.tenant_ids = %s", [str(tenant_id)])
            cur.execute(
                """
                INSERT INTO idempotencia_chave (
                    id, tenant_id, endpoint, chave, payload_hash, usuario_id,
                    status, criada_em, expira_em
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, %s, %s,
                    'em_processo', %s, %s
                )
                RETURNING id
                """,
                [
                    str(tenant_id),
                    endpoint,
                    str(chave),
                    payload_hash,
                    str(usuario_id),
                    criada_em,
                    expira_em,
                ],
            )
            row = cur.fetchone()
            cur.execute("COMMIT")
            assert row is not None
            return UUID(str(row[0]))
        except Exception:
            cur.execute("ROLLBACK")
            raise


def concluir_chave(
    *,
    chave_id: UUID,
    tenant_id: UUID,
    response_status: int,
    response_body_resumo: dict[str, Any],
) -> None:
    """Transiciona `em_processo` -> `concluida` (autocommit, visivel imediato).

    Idempotente do lado do service: chamar de novo apos terminal levanta
    `Exception` do trigger PG (P-EQP-T6).
    """
    _atualizar_terminal(
        chave_id=chave_id,
        tenant_id=tenant_id,
        novo_status="concluida",
        response_status=response_status,
        response_body_resumo=response_body_resumo,
    )


def falhar_chave(
    *,
    chave_id: UUID,
    tenant_id: UUID,
    response_status: int,
) -> None:
    """Transiciona `em_processo` -> `falhada` (autocommit)."""
    _atualizar_terminal(
        chave_id=chave_id,
        tenant_id=tenant_id,
        novo_status="falhada",
        response_status=response_status,
        response_body_resumo={},
    )


def _atualizar_terminal(
    *,
    chave_id: UUID,
    tenant_id: UUID,
    novo_status: str,
    response_status: int,
    response_body_resumo: dict[str, Any],
) -> None:
    """UPDATE em `breaker_writer` (autocommit) — sobrevive a rollback de view."""
    conn = connections["breaker_writer"]
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("SET LOCAL app.active_tenant_id = %s", [str(tenant_id)])
            cur.execute("SET LOCAL app.tenant_ids = %s", [str(tenant_id)])
            cur.execute(
                """
                UPDATE idempotencia_chave
                SET status = %s,
                    response_status = %s,
                    response_body_resumo = %s::jsonb,
                    concluida_em = now()
                WHERE id = %s
                """,
                [
                    novo_status,
                    response_status,
                    json.dumps(response_body_resumo, default=str),
                    str(chave_id),
                ],
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
