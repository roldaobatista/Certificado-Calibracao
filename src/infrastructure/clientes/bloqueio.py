"""Constants do bloqueio comercial de cliente (US-CLI-004).

5 motivos (R2 advogado) + 4 causation_types (TL4 tech-lead).

Justificativa minima de chars exigida no boundary (R3 implicito).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID
from uuid import uuid4 as _uuid4

# Motivos do bloqueio (R2 advogado)
MOTIVO_MANUAL_INADIMPLENCIA = "manual_inadimplencia"
MOTIVO_MANUAL_QUEBRA_CONFIANCA = "manual_quebra_confianca"
MOTIVO_MANUAL_SOLICITACAO_JURIDICO = "manual_solicitacao_juridico"
MOTIVO_MANUAL_OUTRO = "manual_outro"
MOTIVO_AUTOMATICO_INADIMPLENCIA_90D = "automatico_inadimplencia_90d"

MOTIVOS_VALIDOS: tuple[str, ...] = (
    MOTIVO_MANUAL_INADIMPLENCIA,
    MOTIVO_MANUAL_QUEBRA_CONFIANCA,
    MOTIVO_MANUAL_SOLICITACAO_JURIDICO,
    MOTIVO_MANUAL_OUTRO,
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
)

MOTIVOS_MANUAIS: frozenset[str] = frozenset(
    {
        MOTIVO_MANUAL_INADIMPLENCIA,
        MOTIVO_MANUAL_QUEBRA_CONFIANCA,
        MOTIVO_MANUAL_SOLICITACAO_JURIDICO,
        MOTIVO_MANUAL_OUTRO,
    }
)


# causation_type (TL4)
CAUSATION_TITULO_VENCIDO = "titulo_vencido"
CAUSATION_IMPORTACAO_BATCH = "importacao_batch"
CAUSATION_POLITICA_INADIMPLENCIA = "politica_inadimplencia"
CAUSATION_MANUAL_DECISAO_ADMIN = "manual_decisao_admin"

CAUSATION_TYPES_VALIDOS: tuple[str, ...] = (
    CAUSATION_TITULO_VENCIDO,
    CAUSATION_IMPORTACAO_BATCH,
    CAUSATION_POLITICA_INADIMPLENCIA,
    CAUSATION_MANUAL_DECISAO_ADMIN,
)


# Justificativa minima (PRD AC-CLI-004-1)
JUSTIFICATIVA_MIN_CHARS = 30


# =============================================================
# T-CLI-108 — payload canônico de `Cliente.Bloqueado` (AC-CLI-004-9)
# Slot `agendamentos_futuros` acordado no contrato pro consumer Wave A
# `operacao/agenda` (GATE-CLI-7). Em Marco 1 o módulo `operacao/agenda`
# ainda não existe — retorna lista vazia. Quando o módulo for criado
# em Wave A, basta plugar a consulta real em
# `consultar_agendamentos_futuros_do_cliente`.
# =============================================================


def consultar_agendamentos_futuros_do_cliente(cliente_id: UUID, tenant_id: UUID) -> list[UUID]:
    """Lista UUIDs de agendamentos futuros não-iniciados do cliente no tenant ativo.

    **Marco 1:** módulo `operacao/agenda` não existe → retorna `[]`. O slot
    `agendamentos_futuros` é preservado no payload do evento `Cliente.Bloqueado`
    pra que o consumer Wave A `operacao/agenda` (GATE-CLI-7) receba estrutura
    estável desde o primeiro bloqueio dogfooding.

    **Wave A:** quando `operacao/agenda` for criado, plugar consulta aqui
    (consume_within_tenant_context — RLS aplica). Mantida intencionalmente
    pura/sem side-effect.
    """
    return []


def montar_payload_cliente_bloqueado(
    *,
    cliente_id: UUID,
    tenant_id: UUID,
    bloqueio_id: UUID,
    motivo_categoria: str,
    justificativa_hash: str,
    causation_type: str | None,
    causation_id: UUID | None,
    usuario_id: UUID | None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Payload canônico do evento `Cliente.Bloqueado`.

    Inclui `agendamentos_futuros: list[str]` (T-CLI-108, AC-CLI-004-9) —
    slot acordado pro consumer Wave A `operacao/agenda` (GATE-CLI-7).
    NÃO carrega PII cru (justificativa vira hash HMAC versionado).
    """
    agendamentos = consultar_agendamentos_futuros_do_cliente(cliente_id, tenant_id)
    payload: dict[str, Any] = {
        "event_id": str(_uuid4()),
        "cliente_id": str(cliente_id),
        "tenant_id": str(tenant_id),
        "bloqueio_id": str(bloqueio_id),
        "motivo_categoria": motivo_categoria,
        "justificativa_hash": justificativa_hash,
        "causation_type": causation_type or None,
        "causation_id": str(causation_id) if causation_id else None,
        "usuario_id": str(usuario_id) if usuario_id else None,
        "agendamentos_futuros": [str(uid) for uid in agendamentos],
    }
    if extras:
        payload.update(extras)
    return payload
