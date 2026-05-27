"""T-CLI-105 / SANEA-08 — Helper único de evento de auditoria.

Decisão arquitetural cravada em P2 do Marco 1 (tech-lead §D):

> `src/infrastructure/audit/event_helpers.py` com função
> `publicar_evento(*, acao, escopo, payload, causation_id, tenant_id,
> cadeia=True, outbox=True) -> EventoPublicado`. Garantias não-negociáveis:
>  1. Aplica `sanitizar_payload_audit` em ESCRITA (resolve `SEC-SANITIZE-001`).
>  2. Valida `tenant_id` == contexto ativo (raise `TenantMismatch`).
>  3. Cadeia + outbox no MESMO `transaction.atomic` do chamador.
>  4. Idempotente em `(causation_id, acao)`.

Quando NÃO usar o helper (3 exceções legítimas — hook
`event-helper-unico.sh` faz allowlist):
- Dentro de `src/infrastructure/audit/` e `src/infrastructure/multitenant/`
  (circular import + a primitiva mora aqui).
- Testes que exercitam a primitiva (`tests/test_*hash_chain*.py`,
  `tests/test_*registrar_em_cadeia*.py`).
- Management commands de migração one-off (com comentário
  `# audit-immutability: skip -- <razão>`).

T-CLI-107: outbox transacional implementado. `publicar_evento(outbox=True)`
faz INSERT em `bus_outbox` no MESMO `transaction.atomic` do caller. UNIQUE
`(causation_id, acao)` + `ON CONFLICT DO NOTHING` garante idempotência. O
worker `processar_outbox_em_contexto_tenant` (outbox_worker.py) drena.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from django.db import DatabaseError, OperationalError, connection

from src.infrastructure.audit.acoes_canonicas import assert_acao_canonica
from src.infrastructure.audit.services import sanitizar_payload_audit

logger = logging.getLogger(__name__)

# Onda 3 saneamento (2026-05-23) — envelope v10 canonico (catalogo eventos +
# auditoria projeto-inteiro 10 lentes — lente 7 C7-01).
ENVELOPE_SCHEMA_VERSION_DEFAULT = 1

Escopo = Literal["auditoria", "authz"]


class TenantMismatch(RuntimeError):
    """tenant_id passado ao helper diverge do contexto ativo (`app.active_tenant_id`)."""


class OutboxNaoImplementado(NotImplementedError):
    """Mantido por compat de import (T-CLI-105 levantava). T-CLI-107 implementou —
    NUNCA é levantado em runtime; manter classe pra detecção em testes legados.
    """


@dataclass(frozen=True)
class EventoPublicado:
    """Resultado de `publicar_evento`: identificador da linha gravada na cadeia
    + flag de outbox.
    """

    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def publicar_evento(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,  # -- usado em T-CLI-107 (chave de idempotência outbox); aqui só recebe pra contrato
    tenant_id: UUID | None,
    escopo: Escopo = "auditoria",
    cadeia: bool = True,
    outbox: bool = True,
    usuario_id: UUID | None = None,
    resource_summary: str = "",
) -> EventoPublicado:
    """Publica um evento de domínio com garantias 1..4 da decisão arquitetural.

    Parâmetros:
    - `acao`: identificador semântico (`cliente.criado`, `cliente.mesclado`...).
    - `payload`: dict com o conteúdo do evento. **Sanitizado em escrita** pelo
      helper (`sanitizar_payload_audit`) — chamador NÃO precisa pré-sanitizar.
    - `causation_id`: UUID que liga o evento à request/comando original.
      Em T-CLI-107 vira chave de idempotência do outbox.
    - `tenant_id`: UUID do tenant ou None (cadeia sistema). Validado contra
      contexto ativo (`app.active_tenant_id`) — `TenantMismatch` se diverge.
    - `escopo`: `"auditoria"` (cadeia F-A genérica) ou `"authz"` (cadeia
      `AuthorizationDecision` da F-B). Aqui só `"auditoria"` é suportado em
      T-CLI-105; `"authz"` levanta `NotImplementedError` até T-CLI-107.
    - `cadeia=True`: grava elo na hash chain (F-A `registrar_auditoria`).
    - `outbox=True`: enfileira no bus_outbox transacional (T-CLI-107) —
      levanta `OutboxNaoImplementado` até a tabela existir.
    - `usuario_id`, `resource_summary`: passados pra `registrar_auditoria`.

    Garantia 3 (atomicidade): o helper NÃO abre transação própria. Chamador
    responsável por `transaction.atomic()` — cadeia + outbox ficam no mesmo
    bloco transacional do caller (= invariante INV-INT-010).
    """
    if escopo != "auditoria":
        raise NotImplementedError(
            f"escopo='{escopo}' depende de T-CLI-107 (bus_outbox + worker em F-A)"
        )

    # BLOQ-A1 advogado: valida acao contra enum canonico (defesa em
    # profundidade — banco tambem valida via CHECK constraint).
    assert_acao_canonica(acao)

    # Garantia 2: tenant_id == contexto ativo (modo_sistema OU active_tenant_id)
    _validar_tenant_no_contexto(tenant_id)

    # Garantia 1: sanitização em ESCRITA (SEC-SANITIZE-001 — corrige o anti-
    # padrão do bug do flake visão-360 que sanitizava só na LEITURA).
    payload_sanitizado: dict[str, Any] = sanitizar_payload_audit(payload)

    cadeia_linha_id: UUID | None = None
    if cadeia:
        from src.infrastructure.audit.services import registrar_auditoria

        elo = registrar_auditoria(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            action=acao,
            resource_summary=resource_summary or acao,
            payload=payload_sanitizado,
        )
        cadeia_linha_id = elo.id

    outbox_enfileirado = False
    if outbox:
        outbox_enfileirado = _inserir_no_outbox(
            causation_id=causation_id,
            acao=acao,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            payload_sanitizado=payload_sanitizado,
            resource_summary=resource_summary or acao,
        )

    if cadeia_linha_id is None and not outbox_enfileirado:
        # Defesa: chamador pediu `cadeia=False, outbox=False` (ou outbox=True
        # com idempotencia atingida sem cadeia) — não publicou nada novo.
        if not cadeia and not outbox:
            raise ValueError(
                "publicar_evento(cadeia=False, outbox=False) não faz sentido — "
                "passe cadeia=True OU outbox=True."
            )

    # Pra contrato estavel (chamador conta com cadeia_linha_id != None
    # quando cadeia=True), retornamos UUID vazio quando cadeia=False —
    # o caller sabe pelo fim do retorno.
    return EventoPublicado(
        cadeia_linha_id=cadeia_linha_id or UUID(int=0),
        outbox_enfileirado=outbox_enfileirado,
    )


def _inserir_no_outbox(
    *,
    causation_id: UUID,
    acao: str,
    tenant_id: UUID | None,
    usuario_id: UUID | None,
    payload_sanitizado: dict[str, Any],
    resource_summary: str,
) -> bool:
    """T-CLI-107 — INSERT em bus_outbox no `transaction.atomic` do CALLER.

    Idempotente em `(causation_id, acao)` via ON CONFLICT DO NOTHING.
    Retorna True se inseriu, False se idempotencia atingiu linha pre-existente.

    Onda 3 saneamento (2026-05-23) — envelope v10 canonico:
      - event_id: UUID unico do evento (idempotencia cross-consumer)
      - _schema_version: versao do schema do payload (consumer compat)
      - occurred_at: timestamp UTC-aware quando evento OCORREU (vs gravado_em)
      - correlation_id: cadeia forense end-to-end (lido de
        current_setting('app.correlation_id') quando disponivel)
      - actor: pequena descricao do ator (usuario_id ou 'sistema')
    """
    event_id = uuid4()
    occurred_at = datetime.now(UTC)
    correlation_id = _obter_correlation_id()
    perfil_no_evento = _obter_perfil_tenant()  # INT-03 Onda PRE-A.4 — SAN-PERFIL Sprint 4 propaga pro bus
    actor = str(usuario_id) if usuario_id else "sistema"

    envelope = {
        "event_id": str(event_id),
        "_schema_version": ENVELOPE_SCHEMA_VERSION_DEFAULT,
        "event_name": acao,
        "occurred_at": occurred_at.isoformat(),
        "correlation_id": correlation_id,
        "actor": actor,
        "perfil_no_evento": perfil_no_evento,  # INT-03 — A/B/C/D ou None (sistema/sem perfil)
        "acao": acao,  # compat M1/M2 — manter durante 1 release
        "payload": payload_sanitizado,
        "causation_id": str(causation_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "usuario_id": str(usuario_id) if usuario_id else None,
        "resource_summary": resource_summary,
    }
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO bus_outbox "
            "(id, causation_id, acao, envelope_jsonb, tenant_id, criado_em, tentativas) "
            "VALUES (gen_random_uuid(), %s, %s, %s::jsonb, %s, now(), 0) "
            "ON CONFLICT (causation_id, acao) DO NOTHING "
            "RETURNING id",
            [str(causation_id), acao, json.dumps(envelope), tenant_id],
        )
        row = cur.fetchone()
    return row is not None


def _obter_correlation_id() -> str | None:
    """Le correlation_id de current_setting('app.correlation_id', true).

    Pre-2026-05-23 (Marco 1/2) nao setava esse setting — retornar None nesse caso
    nao quebra retrocompat. Onda 3 saneamento promove `correlation_id` para
    obrigatorio em endpoints novos via middleware (a criar Marco 3).
    """
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT current_setting('app.correlation_id', true)")
            row = cur.fetchone()
            valor = row[0] if row else None
            return valor if valor else None
    except (DatabaseError, OperationalError) as exc:
        # F-A-M5 (Onda 2 saneamento — 2026-05-22): except específico em vez de
        # `except Exception` que engolia tudo. Causa-raiz: contexto PG ainda
        # nao aberto / setting nao definido / connection morta.
        # Outras exceptions sao bugs reais — propagar (nao mascarar).
        logger.warning(
            "correlation_id indisponivel via current_setting: %s (%s)",
            exc.__class__.__name__,
            exc,
        )
        return None


def _obter_perfil_tenant() -> str | None:
    """INT-03 (Onda PRE-A.4 — auditoria 10 lentes pré-Wave A).

    Le perfil_regulatorio do tenant ATUAL via current_setting('app.perfil_tenant', true).
    Sprint 4 SAN-PERFIL setou esse GUC em `setar_contexto_pg_na_conexao`.
    Retorna 'A'|'B'|'C'|'D'|None. None aceito em modo sistema OU em contextos
    pre-SAN-PERFIL onde tenant ainda nao tem perfil (migration historica).

    Defesa probatoria: snapshot do perfil no MOMENTO da publicacao do evento —
    consumer cross-modulo Wave A nao precisa consultar tenant atual (que pode
    ter mudado em transicao D→C→B→A).
    """
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT current_setting('app.perfil_tenant', true)")
            row = cur.fetchone()
            valor = row[0] if row else None
            return valor if valor in ("A", "B", "C", "D") else None
    except (DatabaseError, OperationalError) as exc:
        logger.warning(
            "perfil_tenant indisponivel via current_setting: %s (%s)",
            exc.__class__.__name__,
            exc,
        )
        return None


def _validar_tenant_no_contexto(tenant_id: UUID | None) -> None:
    """Garantia 2: bloqueia chamador que tente publicar evento de outro tenant
    OU sem contexto. Modo sistema (`tenant_id=None` com `app.modo_sistema='1'`)
    é caso legítimo.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT current_setting('app.active_tenant_id', true), "
            "current_setting('app.modo_sistema', true)"
        )
        ativo, modo_sistema = cur.fetchone()

    if tenant_id is None:
        if modo_sistema != "1":
            raise TenantMismatch(
                "publicar_evento(tenant_id=None) exige modo_sistema=1 "
                "(run_as_system); contexto atual não está em modo sistema."
            )
        return

    if modo_sistema == "1":
        raise TenantMismatch(
            "publicar_evento com tenant_id em contexto modo_sistema=1 — "
            "use tenant_id=None pra cadeia sistema."
        )

    if not ativo:
        raise TenantMismatch(
            "publicar_evento sem app.active_tenant_id no contexto — "
            "envolva chamada em run_in_tenant_context."
        )

    if str(tenant_id) != ativo:
        raise TenantMismatch(
            f"publicar_evento(tenant_id={tenant_id}) diverge do contexto "
            f"ativo (app.active_tenant_id={ativo})."
        )
