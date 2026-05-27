"""Helper canonico de consulta ao perfil regulatorio do tenant ativo.

T-SAN-PERFIL-017 (Sprint 2 ADR-0067).

Padrao **fail-closed** com ContextVar primario + fallback DB com timeout 50ms.
Eliminando N+1 — o predicate so consulta o banco se o ContextVar estiver vazio
(situacao excepcional fora de request HTTP normal — ex: job procrastinate sem
TenantMiddleware na cadeia).

Uso oficial:

    from src.infrastructure.authz.perfil_tenant_helper import tenant_perfil_e

    # Em qualquer predicate authz / use case que decide rituais ISO 17025:
    allowed, reason = tenant_perfil_e({"A"})
    if not allowed:
        raise PermissionDenied(reason)

Origem: AC-SAN-PERFIL-002-1 + AC-002-5 + AC-002-7 + AC-002-8 + INV-TENANT-PERFIL-001.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable
from uuid import UUID

from django.db import connection

from src.infrastructure.multitenant.context import (
    active_tenant_context,
    perfil_tenant_context,
)

logger = logging.getLogger(__name__)


# Timeout do fallback DB em milissegundos (AC-002-5). PG hiccup maior que isso
# devolve fail-closed em vez de propagar pra request inteira.
_TIMEOUT_FALLBACK_MS = 50


def obter_perfil_tenant_corrente() -> str:
    """Retorna o perfil regulatorio do tenant ativo no request atual.

    Sequencia:
    1. Le ContextVar `perfil_tenant_context` (cache populado pelo middleware).
    2. Cache hit (string nao-vazia entre 'A'/'B'/'C'/'D') = retorna direto.
    3. Cache miss (default "") = fallback DB com timeout 50ms.
    4. Falha de DB OU tenant nao encontrado OU perfil NULL = retorna "".

    Caller decide gravidade:
    - tenant_perfil_e() trata "" como DENY com reason `tenant_perfil_indisponivel`.

    Returns:
        "A" / "B" / "C" / "D" / "" (indisponivel/erro).
    """
    perfil_cacheado = perfil_tenant_context.get()
    if perfil_cacheado:
        return perfil_cacheado

    # Cache miss — pode ser job sem TenantMiddleware ou request com
    # active_tenant_context vazio. Tentar fallback DB.
    active_tenant = active_tenant_context.get()
    if active_tenant is None:
        return ""

    return _consultar_perfil_no_db(active_tenant)


def _consultar_perfil_no_db(tenant_id: UUID) -> str:
    """Fallback DB com `statement_timeout` de 50ms (AC-002-5).

    NAO usa retry/circuit-breaker. Falha = "".
    """
    try:
        with connection.cursor() as cur:
            # Timeout dentro da propria transacao — protege contra PG hiccup
            # que de outro modo derrubaria a request.
            cur.execute(f"SET LOCAL statement_timeout = {_TIMEOUT_FALLBACK_MS}")
            cur.execute(
                "SELECT perfil_regulatorio FROM tenants WHERE id = %s",
                [str(tenant_id)],
            )
            row = cur.fetchone()
            if row is None or row[0] is None:
                # Estado invalido pos-backfill — loga ERROR (AC-002-5).
                logger.error(
                    "tenant_perfil_corrente: tenant %s sem perfil_regulatorio "
                    "(NULL no banco). Estado invalido pos-backfill — investigar.",
                    tenant_id,
                )
                return ""
            return row[0]
    except Exception as e:  # noqa: BLE001 -- defensivo helper fail-closed, qualquer erro DB vira "" (predicate trata)
        logger.warning(
            "tenant_perfil_corrente: fallback DB falhou para tenant %s: %s. "
            "Retornando '' (predicate decide fail-closed).",
            tenant_id,
            e,
        )
        return ""


def tenant_perfil_e(perfis_aceitos: Iterable[str]) -> tuple[bool, str]:
    """Predicate canonico de validacao de perfil regulatorio.

    AC-SAN-PERFIL-002-1 + INV-TENANT-PERFIL-001 + INV-004.

    Args:
        perfis_aceitos: iteravel de chars ('A', 'B', 'C', 'D').

    Returns:
        (True, "") se perfil atual ∈ perfis_aceitos AND tenant nao esta
            em suspensao temporaria (AC-002-7).
        (False, reason) com reason em:
            - "tenant_perfil_indisponivel" se ContextVar vazio e DB falhou.
            - "tenant_perfil_nao_definido" se DB retornou linha mas perfil NULL.
            - "tenant_perfil_nao_autorizado: {atual} ∉ {aceitos}" se perfil
              nao esta no conjunto.
            - "tenant_acreditacao_suspensa: ate {data}" se perfil='A' mas
              acreditacao em janela de suspensao (AC-002-7).

    Fail-closed: timeout/erro/NULL = nega. Nunca fail-open.
    """
    perfis_set = set(perfis_aceitos)

    perfil_atual = obter_perfil_tenant_corrente()
    if not perfil_atual:
        return False, "tenant_perfil_indisponivel"

    if perfil_atual not in perfis_set:
        return (
            False,
            f"tenant_perfil_nao_autorizado: {perfil_atual} ∉ {sorted(perfis_set)}",
        )

    # AC-002-7 — perfil 'A' com suspensao temporaria ativa = DENY.
    # So aplica quando o conjunto de perfis aceitos inclui apenas A
    # (faz sentido: se tenant_perfil_e({"A","B","C"}) for chamado e o tenant
    # esta suspenso, ele ainda e 'A' valido — outras politicas podem permitir).
    if perfil_atual == "A" and perfis_set == {"A"}:
        suspensa_ate = _consultar_suspensao_corrente()
        if suspensa_ate is not None and dt.date.today() < suspensa_ate:
            return (
                False,
                f"tenant_acreditacao_suspensa: ate {suspensa_ate.isoformat()}",
            )

    return True, ""


def _consultar_suspensao_corrente() -> dt.date | None:
    """Le `acreditacao_suspensa_ate` do tenant ativo, ou None se nao suspenso."""
    active_tenant = active_tenant_context.get()
    if active_tenant is None:
        return None
    try:
        with connection.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {_TIMEOUT_FALLBACK_MS}")
            cur.execute(
                "SELECT acreditacao_suspensa_ate FROM tenants WHERE id = %s",
                [str(active_tenant)],
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:  # noqa: BLE001 -- fail-closed conservador: erro vira "suspenso" pra nao liberar perfil A com leitura quebrada
        # Se nao conseguir ler suspensao, fail-closed: assume suspenso ate
        # amanha (bloqueia operacao critica). Conservador.
        return dt.date.today() + dt.timedelta(days=1)
