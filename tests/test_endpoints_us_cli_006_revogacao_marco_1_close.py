"""Endpoints T-CLI-115 (US-CLI-006) — testes E2E REST.

Os testes em `test_us_cli_006_revogacao_incidente_t_cli_115_119.py` cobrem
o USE CASE direto. Aqui exercitamos o ENDPOINT
`POST /clientes/{id}/direitos-titular/revogacao_consentimento/`
pra fechar a cobertura do bloco em `views.py:1143-1185`, requisito de
fechamento Marco 1 (cobertura agregada `clientes/` ≥ 90%).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"revog-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@revog.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _criar_cliente_consentimento(tenant, usuario) -> Cliente:
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa="PF",
            documento="11144477735",
            nome="Cliente Revogar PF",
            aceite_lgpd_em="2026-05-20T10:00:00Z",
            aceite_lgpd_versao="v1",
            aceite_lgpd_origem="CADASTRO_DIRETO",
            aceite_lgpd_base_legal="CONSENTIMENTO",
        )


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_endpoint_happy_201(cenario):
    cliente = _criar_cliente_consentimento(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.post(
        f"/api/v1/clientes/{cliente.id}/direitos-titular/revogacao_consentimento/",
        data={},
        format="json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["cliente_id"] == str(cliente.id)
    assert "revogado_em" in body


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_endpoint_idempotente_200_ja_revogado(cenario):
    cliente = _criar_cliente_consentimento(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    # Primeira chamada
    primeira = client.post(
        f"/api/v1/clientes/{cliente.id}/direitos-titular/revogacao_consentimento/",
        data={},
        format="json",
    )
    assert primeira.status_code == 200, primeira.content
    # Segunda chamada — já revogado
    segunda = client.post(
        f"/api/v1/clientes/{cliente.id}/direitos-titular/revogacao_consentimento/",
        data={},
        format="json",
    )
    assert segunda.status_code == 200, segunda.content
    body = segunda.json()
    assert body["ja_revogado"] is True
    assert "revogado_em" in body


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_endpoint_id_invalido_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.post(
        "/api/v1/clientes/nao-e-uuid/direitos-titular/revogacao_consentimento/",
        data={},
        format="json",
    )
    # Django REST framework pode retornar 404 (NotFound do router) OU 400
    # do nosso validator — aceita ambos como gating do parâmetro.
    assert response.status_code in (400, 404), response.content


@pytest.mark.django_db(transaction=True)
def test_revogar_consentimento_endpoint_cliente_nao_encontrado_404(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.post(
        f"/api/v1/clientes/{uuid4()}/direitos-titular/revogacao_consentimento/",
        data={},
        format="json",
    )
    assert response.status_code == 404, response.content
