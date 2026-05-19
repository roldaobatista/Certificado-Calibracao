"""FB-C2 + FB-A7 — materialização do INV-AUTHZ-001 na borda DRF.

`RequireAuthz.has_permission` é onde a porta vira "permitido/negado" pra
toda view DRF (DEFAULT_PERMISSION_CLASSES). Antes só era testado via
`provider.can()` direto (FB-A7) e a válvula pública estava QUEBRADA por
nome de atributo divergente (FB-C2: `@public` setava `_authz_public`,
permission lia `authz_public`).

Matriz: público→True, sem action→False, denied→False, allowed→True.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIRequestFactory
from src.infrastructure.authz.decorators import PublicEndpoint, public
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.authz.permissions import RequireAuthz
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

pytestmark = pytest.mark.tenant_isolation

_factory = APIRequestFactory()


class _ViewComMixin(PublicEndpoint):
    """CBV DRF pública via mixin (caminho FB-C2 que estava quebrado)."""


@public
def _view_funcao_publica(request):  # pragma: no cover - alvo de marcação
    return None


class _ViewFuncaoPublica:
    """Função `@public` exposta como handler do método (DRF @api_view-like)."""

    get = staticmethod(_view_funcao_publica)


class _ViewSemAction:
    """Sem `authz_action` nem marcação → deny-by-default."""


class _ViewComAction:
    def __init__(self, action: str) -> None:
        self.authz_action = action


def test_publico_via_mixin_retorna_true() -> None:
    """FB-C2: PublicEndpoint (CBV) reconhecido — antes era NEGADO."""
    req = _factory.get("/healthz")
    assert RequireAuthz().has_permission(req, _ViewComMixin()) is True


def test_publico_via_funcao_decorada_retorna_true() -> None:
    """FB-C2: @public no handler do método HTTP é reconhecido."""
    req = _factory.get("/healthz")
    assert RequireAuthz().has_permission(req, _ViewFuncaoPublica()) is True


def test_sem_action_retorna_false() -> None:
    """Deny-by-default: view sem authz_action nem marcação pública."""
    req = _factory.get("/x")
    assert RequireAuthz().has_permission(req, _ViewSemAction()) is False


@pytest.mark.django_db(transaction=True)
def test_denied_retorna_false() -> None:
    """tecnico NÃO pode fatura.estornar → has_permission False."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"tn-ra-{suffix}")
    usuario = UsuarioFactory(email=f"tec-{suffix}@ra.local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil="tecnico")
    invalidate_user_cache(usuario.id, tenant.id)

    req = _factory.post("/faturas/estornar")
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        assert RequireAuthz().has_permission(req, _ViewComAction("fatura.estornar")) is False


@pytest.mark.django_db(transaction=True)
def test_allowed_retorna_true() -> None:
    """admin_tenant PODE os.criar → has_permission True."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"tn-ra-{suffix}")
    usuario = UsuarioFactory(email=f"adm-{suffix}@ra.local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(usuario.id, tenant.id)

    req = _factory.post("/os")
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        assert RequireAuthz().has_permission(req, _ViewComAction("os.criar")) is True
