"""DRF permission classes — `RequireAuthz` (deny-by-default).

# authz-check: skip -- este arquivo IMPLEMENTA a porta (chama get_provider().can()
# internamente); o hook detecta `has_permission` como endpoint mas aqui o
# has_permission é a própria materialização do INV-AUTHZ-001, não um bypass.

Como aplicar globalmente: já está em config/settings/base.py via
`REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = ['RequireAuthz']`
em F-B (alteração na própria fase).

Como usar por endpoint:
    class MinhaView(APIView):
        authz_action = "os.criar"

        @staticmethod
        def get_authz_resource(request):
            return {"campo": request.data.get("campo")}

`authz_action` pode também ser função `def get_authz_action(self, request) -> str`
quando depende do método HTTP.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission

from .django_provider import get_provider


class RequireAuthz(BasePermission):
    """Permission default — exige `authz_action` ou marcação pública.

    Sem nenhum dos dois = bloqueio (deny-by-default — INV-AUTHZ-001).
    """

    message = "Acesso negado"

    def has_permission(self, request, view) -> bool:  # type: ignore[no-untyped-def]
        # Caminho 1: view explicitamente pública.
        if getattr(view, "authz_public", False):
            return True

        # Caminho 2: deny-by-default — exige `authz_action`.
        action = self._extrair_acao(request, view)
        if action is None:
            # Sem ação declarada = bug do dev. Hook pega em pre-commit;
            # em runtime bloqueia.
            self.message = "View sem 'authz_action' declarada"
            return False

        from src.infrastructure.multitenant.context import (
            active_tenant_context,
            usuario_id_context,
        )

        usuario_id = usuario_id_context.get()
        tenant_id = active_tenant_context.get()
        if usuario_id is None or tenant_id is None:
            self.message = "Contexto de autorização ausente"
            return False

        resource = self._extrair_resource(request, view)
        decision = get_provider().can(
            usuario_id=usuario_id,
            action=action,
            resource=resource,
            tenant_id=tenant_id,
            purpose=getattr(view, "authz_purpose", "execucao_contrato"),
        )
        if not decision.allowed:
            self.message = f"Acesso negado: {decision.reason}"
            request._authz_decision = decision  # type: ignore[attr-defined]
            return False
        request._authz_decision = decision  # type: ignore[attr-defined]
        return True

    @staticmethod
    def _extrair_acao(request, view) -> str | None:  # type: ignore[no-untyped-def]
        if hasattr(view, "get_authz_action"):
            return view.get_authz_action(request)
        return getattr(view, "authz_action", None)

    @staticmethod
    def _extrair_resource(request, view) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        if hasattr(view, "get_authz_resource"):
            return view.get_authz_resource(request) or {}
        return {}
