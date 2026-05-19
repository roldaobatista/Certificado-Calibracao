"""Smoke tests do TenantMiddleware — verifica bypass de paths publicos.

Testes profundos (fuzzing cross-tenant com pool concorrente) ficam no Marco 6,
que exige PG vivo com RLS aplicada (`docker compose up` rodando).
"""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from src.infrastructure.multitenant.middleware import (
    PUBLIC_PATHS_PREFIX,
    TenantMiddleware,
)


def _stub_view(request):  # type: ignore[no-untyped-def]
    return HttpResponse("ok")


@pytest.fixture
def factory() -> RequestFactory:
    return RequestFactory()


class TestBypass:
    """Endpoints publicos NAO devem ser bloqueados pelo middleware."""

    @pytest.mark.parametrize("path", PUBLIC_PATHS_PREFIX)
    def test_paths_publicos_bypass(self, factory: RequestFactory, path: str) -> None:
        request = factory.get(path + "/algo")
        request.user = AnonymousUser()
        middleware = TenantMiddleware(_stub_view)
        response = middleware(request)
        assert response.status_code == 200

    def test_admin_bypass(self, factory: RequestFactory) -> None:
        request = factory.get("/admin/login/")
        request.user = AnonymousUser()
        middleware = TenantMiddleware(_stub_view)
        response = middleware(request)
        assert response.status_code == 200


class TestAuthRequired:
    def test_anonimo_em_path_protegido_devolve_401(self, factory: RequestFactory) -> None:
        request = factory.get("/api/v1/algo/")
        request.user = AnonymousUser()
        middleware = TenantMiddleware(_stub_view)
        response = middleware(request)
        assert response.status_code == 401
        assert b"Autenticacao obrigatoria" in response.content
