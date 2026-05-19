"""Testes E2E do TenantMiddleware — exige PG vivo (RLS bootstrap).

Middleware le UsuarioPerfilTenant com policy 'upt_self_select' (precisa de
app.usuario_id setado). Testes confirmam o fluxo completo.
"""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse
from src.infrastructure.multitenant.connection import run_as_system

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

pytestmark = pytest.mark.tenant_isolation


@pytest.mark.django_db(transaction=True)
class TestMiddlewareFluxoCompleto:
    def test_usuario_com_1_tenant_unico_resolve_default(self, client: Client) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory(password="senha-teste-12-chars")
            UsuarioPerfilTenantFactory(usuario=u, tenant=t, perfil="admin_tenant")

        client.force_login(u)
        # Como F-A nao expoe endpoints protegidos ainda, testa via path publico
        # confirmando que middleware nao crasha com user logado.
        # Wave A vai adicionar testes em endpoints reais (ex: GET /api/v1/calibracoes/).
        response = client.get(reverse("schema"))
        assert response.status_code in (200, 301, 302)

    def test_usuario_sem_perfil_em_tenant_recebe_403(self, client: Client) -> None:
        """Usuario sem perfil em tenant ativo nao acessa endpoint protegido.

        Skip removido 2026-05-18 noite final: agora usa `/api/v1/clientes/`
        do modulo clientes (Wave A · Marco 1 fechado).
        """
        from django_otp import DEVICE_ID_SESSION_KEY
        from django_otp.plugins.otp_totp.models import TOTPDevice

        with run_as_system():
            u = UsuarioFactory(password="senha-teste-12-chars")
            device, _ = TOTPDevice.objects.get_or_create(
                user=u, name="default", defaults={"confirmed": True}
            )

        client.force_login(u)
        session = client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        response = client.get("/api/v1/clientes/")
        # Sem perfil em tenant ativo -> middleware nega.
        assert response.status_code in (401, 403)
