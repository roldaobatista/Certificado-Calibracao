# authz-check: skip -- este arquivo DEFINE a válvula pública (@public /
# PublicEndpoint) e o helper is_public que materializam a exceção legítima
# do INV-AUTHZ-001; não é um endpoint. Mesmo precedente de permissions.py.

"""Decorators + helpers que fazem a porta `AuthorizationProvider` valer
na borda da aplicação (INV-AUTHZ-001).

Padrões em F-B:
- `@public` — marca view como SEM autorização. Hook `authz-check.sh` aceita.
- `@requires_authz(action, get_resource=...)` — chama `can()` antes da view
  rodar; retorna 403 se denied. Caso de uso típico em views regulares
  Django (não DRF).

DRF tem o caminho próprio em `permissions.py` (RequireAuthz).

INV-AUTHZ-001 só vale se uma das duas vier marcada — view sem nenhum
decorator e sem `RequireAuthz` é rejeitada pelo hook em pre-commit.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse

from .django_provider import get_provider

# authz-check: skip -- definição da válvula pública (não é endpoint)
# FB-C2: nome canônico ÚNICO do marcador público. `@public` (função),
# `PublicEndpoint` (mixin CBV/DRF) e `is_public` (consumidores: middleware,
# RequireAuthz, hook) usam ESTE atributo — nada de `authz_public` divergente.
ATTR_PUBLIC = "_authz_public"


def public(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Marca view explicitamente pública (sem `can()`).

    Único caminho legítimo pra view não passar pelo provider — hook
    `authz-check.sh` valida que esta marcação está presente.

    Uso típico: health checks, schema OpenAPI público, página de
    login, callback de webhook autenticado por HMAC (autorização vem da
    assinatura HMAC, não do provider).

    Para views DRF baseadas em classe (APIView/ViewSet) use o mixin
    `PublicEndpoint` — `@public` em função não propaga atributo pra
    classe (era o bug FB-C2).
    """
    setattr(view_func, ATTR_PUBLIC, True)
    return view_func


class PublicEndpoint:
    """Mixin pra APIView/ViewSet DRF explicitamente publica (FB-C2).

    Equivalente CBV do `@public`. `RequireAuthz` reconhece via `is_public`.
    Uso: `class HealthView(PublicEndpoint, APIView): ...`
    """

    _authz_public = True


def requires_authz(
    action: str,
    get_resource: Callable[[HttpRequest], dict[str, Any]] | None = None,
    purpose: str = "execucao_contrato",
) -> Callable[[Callable[..., HttpResponse]], Callable[..., HttpResponse]]:
    """Chama `AuthorizationProvider.can()` antes da view; 403 se denied.

    `get_resource` recebe o request e devolve dict pro ABAC. Se omitido,
    resource = {} (RBAC puro).

    Tenant_id sai do contexto multi-tenant (active_tenant). Se contexto
    não estiver setado (path público), levantam 403 — view com
    `@requires_authz` exige tenant.
    """

    def decorator(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            from src.infrastructure.multitenant.context import (
                active_tenant_context,
                usuario_id_context,
            )

            usuario_id = usuario_id_context.get()
            tenant_id = active_tenant_context.get()
            if usuario_id is None or tenant_id is None:
                return JsonResponse(
                    {"detail": "Contexto de autorização ausente"},
                    status=403,
                )

            resource = get_resource(request) if get_resource else {}
            decision = get_provider().can(
                usuario_id=usuario_id,
                action=action,
                resource=resource,
                tenant_id=tenant_id,
                purpose=purpose,
            )
            if not decision.allowed:
                return JsonResponse(
                    {
                        "detail": "Acesso negado",
                        "reason": decision.reason,
                    },
                    status=403,
                )
            # Anexa decisão ao request pra view inspecionar se quiser
            request._authz_decision = decision  # type: ignore[attr-defined]
            return view_func(request, *args, **kwargs)

        wrapper._authz_action = action  # type: ignore[attr-defined]
        return wrapper

    return decorator


# authz-check: skip -- helper da válvula pública (não é endpoint)
def is_public(view: Any, request: Any = None) -> bool:
    """Marcador público resolvido — FONTE ÚNICA (FB-C2).

    Reconhece `_authz_public` em qualquer forma legítima: função decorada
    com `@public`; classe/instância DRF com mixin `PublicEndpoint` (ou
    atributo `_authz_public = True`); função DRF embrulhada (atributo via
    `view.cls`); ou o handler do método HTTP corrente quando `request`
    é fornecido. Antes do FB-C2 cada consumidor lia um nome diferente
    (`authz_public` vs `_authz_public`) → toda view pública DRF era NEGADA.
    """
    if getattr(view, ATTR_PUBLIC, False):
        return True
    cls = getattr(view, "cls", None)
    if cls is not None and getattr(cls, ATTR_PUBLIC, False):
        return True
    if request is not None:
        metodo = getattr(request, "method", "") or ""
        handler = getattr(view, metodo.lower(), None)
        if handler is not None and getattr(handler, ATTR_PUBLIC, False):
            return True
    return False
