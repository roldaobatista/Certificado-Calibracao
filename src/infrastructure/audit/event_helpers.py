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

Outbox transacional (`outbox=True`) ainda não está implementado — depende
de T-CLI-107 (tabela `bus_outbox`). Chamadas com `outbox=True` levantam
`OutboxNaoImplementado` até T-CLI-107; chamadas com `outbox=False`
publicam apenas na cadeia F-A (caminho viável já em Marco 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from django.db import connection

from src.infrastructure.audit.services import sanitizar_payload_audit

Escopo = Literal["auditoria", "authz"]


class TenantMismatch(RuntimeError):
    """tenant_id passado ao helper diverge do contexto ativo (`app.active_tenant_id`)."""


class OutboxNaoImplementado(NotImplementedError):
    """`outbox=True` depende de T-CLI-107 (tabela bus_outbox)."""


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

    if outbox:
        # T-CLI-107 — tabela bus_outbox + INSERT idempotente em (causation_id, acao)
        raise OutboxNaoImplementado(
            "outbox=True depende de T-CLI-107 (bus_outbox). "
            "Use outbox=False enquanto a tabela não existir."
        )

    if cadeia_linha_id is None:
        # Defesa: chamador pediu `cadeia=False, outbox=False` — não publicou nada.
        raise ValueError(
            "publicar_evento(cadeia=False, outbox=False) não faz sentido — "
            "passe cadeia=True OU outbox=True."
        )

    return EventoPublicado(
        cadeia_linha_id=cadeia_linha_id,
        outbox_enfileirado=False,
    )


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
