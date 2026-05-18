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

from functools import wraps
from typing import Any, Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

from .django_provider import get_provider


def public(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Marca view explicitamente pública (sem `can()`).

    Único caminho legítimo pra view não passar pelo provider — hook
    `authz-check.sh` valida que esta marcação está presente.

    Uso típico: health checks, schema OpenAPI público, página de
    login, callback de webhook autenticado por HMAC (autorização vem da
    assinatura HMAC, não do provider).
    """
    view_func._authz_public = True  # type: ignore[attr-defined]
    return view_func


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


def is_public(view_func: Callable[..., HttpResponse]) -> bool:
    """Util pra middleware / hooks consultarem."""
    return getattr(view_func, "_authz_public", False)
