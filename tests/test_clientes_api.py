"""API /api/v1/clientes/ — testes E2E (Wave A · Marco 1).

Matriz authz seed pelo proprio modulo (migration 0003_seed_authz_acoes):
    admin_tenant            -> criar, ler, atualizar, deletar
    tecnico                 -> ler
    rt_signatario           -> ler
    cliente_externo_leitura -> ler

Cobre:
- INV-AUTHZ-001: cada acao passa pelo provider (admin permite tudo;
  cliente_externo_leitura so le; tecnico nao deleta).
- INV-TENANT-001: usuario do tenant A nunca enxerga cliente do tenant B.
- INV-024 + ADR-0017: CNPJ alfanumerico aceito; DV invalido rejeitado.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _autenticar(client: APIClient, usuario, tenant, com_mfa: bool = True) -> None:
    """force_login cria sessao Django (necessario pra TenantMiddleware ler request.user).
    Injeta header X-Afere-Active-Tenant.

    `com_mfa=True`: cria + verifica TOTP device (necessario pros perfis sensiveis
    passarem pelo MfaRequiredMiddleware — SEC-MFA-001).
    """
    if com_mfa:
        from django_otp.plugins.otp_totp.models import TOTPDevice

        device, _ = TOTPDevice.objects.get_or_create(
            user=usuario,
            name="default",
            defaults={"confirmed": True},
        )
        if not device.confirmed:
            device.confirmed = True
            device.save()
        # OTPMiddleware verifica DEVICE_ID_SESSION_KEY pra is_verified() retornar True
        from django_otp import DEVICE_ID_SESSION_KEY
        client.force_login(usuario)
        session = client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
    else:
        client.force_login(usuario)
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"api-{suffix}")
    admin_u = UsuarioFactory(email=f"adm-{suffix}@cli.local")
    leitor_u = UsuarioFactory(email=f"ler-{suffix}@cli.local")
    tecnico_u = UsuarioFactory(email=f"tec-{suffix}@cli.local")
    UsuarioPerfilTenantFactory(usuario=admin_u, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=leitor_u, tenant=tenant, perfil="cliente_externo_leitura")
    UsuarioPerfilTenantFactory(usuario=tecnico_u, tenant=tenant, perfil="tecnico")
    for u in (admin_u, leitor_u, tecnico_u):
        invalidate_user_cache(u.id, tenant.id)
    return {
        "tenant": tenant,
        "admin": admin_u,
        "leitor": leitor_u,
        "tecnico": tecnico_u,
    }


@pytest.mark.django_db(transaction=True)
def test_inv_authz_001_admin_cria_cliente_pj_201(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11.222.333/0001-81",
            "nome": "Empresa Teste LTDA",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["documento"] == "11222333000181"


@pytest.mark.django_db(transaction=True)
def test_inv_authz_001_leitor_tenta_criar_e_recebe_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["leitor"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "Tentativa",
        },
        format="json",
    )
    assert response.status_code == 403, response.content


@pytest.mark.django_db(transaction=True)
def test_inv_authz_001_tecnico_tenta_deletar_e_recebe_403(cenario):
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        c = Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="X",
        )

    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])

    response = client.delete(f"/api/v1/clientes/{c.id}/")
    assert response.status_code == 403, response.content


@pytest.mark.django_db(transaction=True)
def test_adr_0017_cnpj_alfanumerico_aceito_via_api(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "12.ABC.345/01DE-35",
            "nome": "Empresa Alfa LTDA",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    assert response.json()["documento"] == "12ABC34501DE35"


@pytest.mark.django_db(transaction=True)
def test_inv_036_dv_invalido_rejeita_via_api(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000199",
            "nome": "Errado",
        },
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    assert "documento" in body


@pytest.mark.django_db(transaction=True)
def test_inv_tenant_001_cliente_de_a_nao_aparece_em_listagem_de_b(cenario):
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Em A",
        )

    suffix_b = uuid4().hex[:8]
    tenant_b = TenantFactory(slug=f"b-api-{suffix_b}")
    admin_b = UsuarioFactory(email=f"adm-b-{suffix_b}@cli.local")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    invalidate_user_cache(admin_b.id, tenant_b.id)

    client = APIClient()
    _autenticar(client, admin_b, tenant_b)

    response = client.get("/api/v1/clientes/")
    assert response.status_code == 200
    body = response.json()
    items = body if isinstance(body, list) else body.get("results", [])
    assert items == [], f"VAZAMENTO: admin_b viu {items}"


@pytest.mark.django_db(transaction=True)
def test_inv_authz_001_leitor_consegue_listar(cenario):
    """cliente_externo_leitura tem clientes.ler — GET 200."""
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Visivel",
        )

    client = APIClient()
    _autenticar(client, cenario["leitor"], cenario["tenant"])

    response = client.get("/api/v1/clientes/")
    assert response.status_code == 200, response.content
