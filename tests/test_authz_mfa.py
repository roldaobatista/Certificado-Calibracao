"""MFA TOTP obrigatorio pros perfis sensiveis (SEC-MFA-001).

F-B nao roda o fluxo HTTP completo; testamos a logica do middleware
direto: usuario com perfil sensivel + sem TOTP verificado = 401.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.test import RequestFactory
from src.infrastructure.authz.middleware import (
    PERFIS_SENSIVEIS,
    MfaRequiredMiddleware,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _make_request(path: str = "/api/os/", user=None):
    rf = RequestFactory()
    request = rf.get(path)
    request.user = user
    return request


class _FakeUserMFAOff:
    """Stub minimal — django-otp expoe is_verified() em request.user."""

    def __init__(self, pk, mfa_obrigatorio=False):
        self.pk = pk
        self.id = pk
        self.is_authenticated = True
        self.mfa_obrigatorio = mfa_obrigatorio

    def is_verified(self) -> bool:
        return False


class _FakeUserMFAOn(_FakeUserMFAOff):
    def is_verified(self) -> bool:
        return True


@pytest.mark.django_db(transaction=True)
def test_sec_mfa_001_usuario_mfa_obrigatorio_sem_otp_e_401():
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"mfa-{suffix}")
    usuario = UsuarioFactory(email=f"mfa-{suffix}@local")
    user = _FakeUserMFAOff(pk=usuario.id, mfa_obrigatorio=True)

    mw = MfaRequiredMiddleware(lambda r: None)  # type: ignore[arg-type]  # test double: get_response e callable, nao precisa tipar HttpResponse
    request = _make_request(user=user)

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        response = mw(request)

    assert response is not None
    assert response.status_code == 401
    assert b"mfa_required_user" in response.content


@pytest.mark.django_db(transaction=True)
def test_sec_mfa_001_perfil_sensivel_sem_otp_e_401():
    """Sem flag mfa_obrigatorio mas perfil sensivel = MFA exigido."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"mfa-{suffix}")
    usuario = UsuarioFactory(email=f"sens-{suffix}@local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil="admin_tenant")
    user = _FakeUserMFAOff(pk=usuario.id, mfa_obrigatorio=False)

    mw = MfaRequiredMiddleware(lambda r: None)  # type: ignore[arg-type]  # test double: get_response e callable, nao precisa tipar HttpResponse
    request = _make_request(user=user)

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        response = mw(request)

    assert response is not None
    assert response.status_code == 401
    assert b"mfa_required_perfil_sensivel" in response.content


@pytest.mark.django_db(transaction=True)
def test_sec_mfa_001_perfil_nao_sensivel_passa_sem_otp():
    """Tecnico sem flag mfa_obrigatorio nao exige TOTP."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"mfa-{suffix}")
    usuario = UsuarioFactory(email=f"tec-{suffix}@local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil="tecnico")
    user = _FakeUserMFAOff(pk=usuario.id, mfa_obrigatorio=False)

    chamado = {"passou": False}

    def next_view(request):
        chamado["passou"] = True
        return "ok"

    mw = MfaRequiredMiddleware(next_view)  # type: ignore[arg-type]  # test double: get_response e callable, nao precisa tipar HttpResponse
    request = _make_request(user=user)

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        response = mw(request)

    assert chamado["passou"], "Tecnico devia passar; nao e perfil sensivel"
    assert response == "ok"


@pytest.mark.django_db(transaction=True)
def test_sec_mfa_001_perfil_sensivel_com_otp_passa():
    """admin_tenant com TOTP verificado passa."""
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"mfa-{suffix}")
    usuario = UsuarioFactory(email=f"adm-{suffix}@local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant, perfil="admin_tenant")
    user = _FakeUserMFAOn(pk=usuario.id, mfa_obrigatorio=True)

    chamado = {"passou": False}

    def next_view(request):
        chamado["passou"] = True
        return "ok"

    mw = MfaRequiredMiddleware(next_view)  # type: ignore[arg-type]  # test double: get_response e callable, nao precisa tipar HttpResponse
    request = _make_request(user=user)

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        response = mw(request)

    assert chamado["passou"]
    assert response == "ok"


def test_perfis_sensiveis_inclui_admin_rt_financeiro():
    """Lista fechada — protege contra remocao acidental por refactor."""
    assert "admin_tenant" in PERFIS_SENSIVEIS
    assert "rt_signatario" in PERFIS_SENSIVEIS
    assert "financeiro" in PERFIS_SENSIVEIS
