"""Endpoints de health (F-C2) — liveness vs readiness.

- `/livez`  (liveness)  — processo de pe; NAO checa dependencia. K8s reinicia o
  pod so se isto falhar (evita reinicio em cascata quando o banco oscila).
- `/readyz` (readiness) — checa DB (SELECT 1) + cache/Redis. 503 se alguma
  dependencia critica esta fora (K8s tira o pod do balanceador sem matar).
- `/healthz` (legado, docker-compose) — alias de liveness, preservado.

Todos `@public` (sem auth) e no bypass do TenantMiddleware
(PUBLIC_PATHS_PREFIX) — nao exigem tenant context. O `SELECT 1` nao toca tabela
com RLS, entao roda sem `active_tenant_id`.
"""

from __future__ import annotations

from typing import Any

from django.core.cache import cache
from django.db import connections
from django.http import HttpRequest, JsonResponse

from src.infrastructure.authz.decorators import public
from src.infrastructure.observabilidade.desligamento import esta_desligando


@public
def livez(_request: HttpRequest) -> JsonResponse:
    """Liveness — o processo responde. Sem checagem de dependencia.

    NAO reflete o drain: durante o graceful shutdown o processo continua VIVO
    (so esta drenando) — matar via liveness abortaria requests em voo. Quem
    tira do balanceador e o /readyz.
    """
    return JsonResponse({"status": "ok"})


# Alias legado mantido pra docker-compose / configs existentes.
healthz = livez


def _checar_db() -> tuple[bool, str]:
    try:
        with connections["default"].cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True, "ok"
    except Exception as exc:  # — readiness reporta, nao propaga
        return False, f"erro: {type(exc).__name__}"


def _checar_cache() -> tuple[bool, str]:
    try:
        cache.set("readyz:ping", "1", timeout=5)
        ok = cache.get("readyz:ping") == "1"
        return (ok, "ok" if ok else "erro: valor inesperado")
    except Exception as exc:
        return False, f"erro: {type(exc).__name__}"


@public
def readyz(_request: HttpRequest) -> JsonResponse:
    """Readiness — apto a receber trafego (DB + cache OK). 503 se degradado.

    Drain (F-C2 Fatia C): se o processo recebeu SIGTERM, responde 503 "draining"
    ANTES de checar dependencia — o balanceador para de mandar trafego e os
    requests em voo terminam dentro da graceful-timeout do gunicorn.
    """
    if esta_desligando():
        return JsonResponse(
            {"status": "draining", "checks": {}},
            status=503,
        )
    db_ok, db_detalhe = _checar_db()
    cache_ok, cache_detalhe = _checar_cache()
    pronto = db_ok and cache_ok
    corpo: dict[str, Any] = {
        "status": "ready" if pronto else "degraded",
        "checks": {"db": db_detalhe, "cache": cache_detalhe},
    }
    return JsonResponse(corpo, status=200 if pronto else 503)
