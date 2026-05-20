"""T-CLI-104 — circuit breaker observado para `AcessoDadosCliente`.

`registrar_acesso_dados_cliente_com_breaker(...)` é o wrapper que TODO
endpoint que loga visualização de PII (visão 360, dedup compare,
importação) DEVE usar. Ele:

1. Chama `registrar_acesso_dados_cliente` original (fail-loud preservado).
2. Grava UM evento `(tenant_id, ts, ok)` em `breaker_acesso_pii_evento`
   via conexão paralela autocommit `breaker_writer`.
3. Se a gravação principal levantou: grava `ok=False` ANTES de relançar.
   A conexão autocommit garante que esse evento SOBREVIVE ao rollback
   do request HTTP do caller (CRÍTICO T2 review tech-lead).

Avaliação do limiar (sliding window 5min + threshold OR) acontece no
management command `avaliar_circuit_breaker_acesso_pii` (Wave A pluga
em cron).

Contrato fail-loud (LGPD art. 37): NÃO há fallback "permitir sem
registro" se a gravação principal falhar.

# tests-coverage: tests/test_breaker_acesso_pii_t_cli_104.py
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import connections

from src.infrastructure.audit.models import AcessoDadosCliente
from src.infrastructure.audit.services import registrar_acesso_dados_cliente


def registrar_acesso_dados_cliente_com_breaker(
    *,
    tenant_id: UUID,
    usuario_id: UUID | None,
    cliente_id: UUID | None,
    finalidade: str,
    categoria_dado_acessado: str | None = None,
    recurso: dict[str, Any] | None = None,
    ip_hash: str = "",
) -> AcessoDadosCliente:
    """Wrapper de `registrar_acesso_dados_cliente` com observação de breaker.

    Sempre grava 1 linha em `breaker_acesso_pii_evento` (ok=True ou
    ok=False), via conexão paralela autocommit `breaker_writer`. Em
    falha da gravação principal, propaga a exceção (fail-loud).
    """
    kwargs: dict[str, Any] = {
        "tenant_id": tenant_id,
        "usuario_id": usuario_id,
        "cliente_id": cliente_id,
        "finalidade": finalidade,
        "recurso": recurso,
        "ip_hash": ip_hash,
    }
    if categoria_dado_acessado is not None:
        kwargs["categoria_dado_acessado"] = categoria_dado_acessado
    try:
        acesso = registrar_acesso_dados_cliente(**kwargs)
    except Exception:
        _gravar_evento_breaker(tenant_id=tenant_id, ok=False)
        raise
    _gravar_evento_breaker(tenant_id=tenant_id, ok=True)
    return acesso


def _gravar_evento_breaker(*, tenant_id: UUID, ok: bool) -> None:
    """INSERT em `breaker_acesso_pii_evento` via conexão paralela autocommit.

    `breaker_writer` tem `ATOMIC_REQUESTS=False` → autocommit (cada
    statement = transação implícita). INSERT aqui SOBREVIVE ao rollback
    do `default` (request HTTP do caller) — fail-loud + breaker
    observado preservados.

    **Segurança (FAIL 1+2 auditor 2026-05-20):**

    A policy RLS INSERT exige `tenant_id = current_setting('app.
    active_tenant_id')` SEMPRE (sem ramo permissivo `modo_sistema='1'
    → qualquer tenant_id`). Defesa em profundidade contra forja:
    mesmo um caller mal-intencionado passando `tenant_id` de outro
    tenant é rejeitado pelo banco, porque a policy compara com o
    `app.active_tenant_id` que o wrapper seta a partir do MESMO
    argumento.

    Abrimos transação EXPLÍCITA (`BEGIN; SET LOCAL ...; INSERT;
    COMMIT`) — `SET LOCAL` vive APENAS até COMMIT/ROLLBACK. Mata o
    vetor "session-level vaza entre requests via pool reuse" do
    auditor FAIL 2. Em qualquer cenário de falha (libpq erro, kill,
    OOM, exceção Python), o `SET LOCAL` morre junto com a tx.
    """
    conn = connections["breaker_writer"]
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("SET LOCAL app.active_tenant_id = %s", [str(tenant_id)])
            cur.execute(
                "INSERT INTO breaker_acesso_pii_evento "
                "(id, tenant_id, ts, ok) "
                "VALUES (gen_random_uuid(), %s, now(), %s)",
                [str(tenant_id), ok],
            )
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
