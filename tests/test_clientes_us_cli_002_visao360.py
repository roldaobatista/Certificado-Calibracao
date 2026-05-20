"""US-CLI-002 — testes da visao 360 + log de acesso INV-013 (7 cenarios T-CLI-040)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.db.utils import InternalError, ProgrammingError
from rest_framework.test import APIClient
from src.infrastructure.audit.models import AcessoDadosCliente
from src.infrastructure.audit.services import registrar_auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
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
    tenant = TenantFactory(slug=f"v360-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@v360.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _criar_cliente(tenant, usuario) -> Cliente:
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente V360",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_013_visao_360_grava_acesso_antes_de_responder(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.get(f"/api/v1/clientes/{cliente.id}/visao-360/?finalidade=executar_os")
    assert response.status_code == 200, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        acessos = AcessoDadosCliente.objects.filter(cliente_id=cliente.id)
        assert acessos.count() == 1
        a = acessos.first()
        assert a.finalidade == "executar_os"
        assert a.usuario_id == cenario["admin"].id
        # R1 advogado — recurso sem PII cru
        assert "11222333000181" not in str(a.recurso)
        assert str(cliente.id) in str(a.recurso)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_retorna_eventos_em_ordem_reversa(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    # Cria 3 eventos no auditoria do cliente
    with run_in_tenant_context(cenario["tenant"].id):
        for i in range(3):
            registrar_auditoria(
                tenant_id=cenario["tenant"].id,
                action=f"cliente.evento_{i}",
                resource_summary=str(cliente.id),
                payload={"cliente_id": str(cliente.id), "n": i},
            )

    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.get(
        f"/api/v1/clientes/{cliente.id}/visao-360/?finalidade=atendimento_pos_venda"
    )
    assert response.status_code == 200
    items = response.json()["eventos"]
    assert len(items) >= 3
    # Ordem reversa por timestamp
    timestamps = [i["timestamp"] for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_filtra_eventos_de_outros_clientes(cenario):
    cliente_a = _criar_cliente(cenario["tenant"], cenario["admin"])
    # Cria outro cliente + evento NO MESMO TENANT
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        cliente_b = Cliente.objects.create(
            tenant=cenario["tenant"],
            tipo_pessoa=TipoPessoa.PJ,
            documento="33000167000101",
            nome="Cliente B V360",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    with run_in_tenant_context(cenario["tenant"].id):
        registrar_auditoria(
            tenant_id=cenario["tenant"].id,
            action="cliente.evento_a",
            resource_summary=str(cliente_a.id),
            payload={"cliente_id": str(cliente_a.id), "tag": "A"},
        )
        registrar_auditoria(
            tenant_id=cenario["tenant"].id,
            action="cliente.evento_b",
            resource_summary=str(cliente_b.id),
            payload={"cliente_id": str(cliente_b.id), "tag": "B"},
        )

    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    response = client.get(
        f"/api/v1/clientes/{cliente_a.id}/visao-360/?finalidade=auditoria_interna"
    )
    items = response.json()["eventos"]
    # So eventos do A
    for it in items:
        assert it["payload"]["cliente_id"] == str(cliente_a.id)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_isolamento_cross_tenant(cenario):
    """RLS bloqueia leitura de auditoria de outro tenant."""
    # Cria cliente em A + evento
    cliente_a = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id):
        registrar_auditoria(
            tenant_id=cenario["tenant"].id,
            action="cliente.privado_a",
            resource_summary=str(cliente_a.id),
            payload={"cliente_id": str(cliente_a.id)},
        )

    # Tenant B + admin_b
    suffix_b = uuid4().hex[:8]
    tenant_b = TenantFactory(slug=f"b-v360-{suffix_b}")
    admin_b = UsuarioFactory(email=f"adm-b-{suffix_b}@v360.local")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    invalidate_user_cache(admin_b.id, tenant_b.id)

    client = APIClient()
    _autenticar(client, admin_b, tenant_b)
    # Tenta acessar visao 360 do cliente_a a partir do tenant B
    response = client.get(
        f"/api/v1/clientes/{cliente_a.id}/visao-360/?finalidade=investigacao_incidente"
    )
    # RLS faz Cliente.objects.get() falhar → 404
    assert response.status_code == 404


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_finalidade_obrigatoria(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    # sem query param finalidade
    response = client.get(f"/api/v1/clientes/{cliente.id}/visao-360/")
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "finalidade_obrigatoria_e_enum"

    # com finalidade fora do enum
    response = client.get(f"/api/v1/clientes/{cliente.id}/visao-360/?finalidade=motivo_inventado")
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_acessos_dados_cliente_imutavel_via_trigger_pg(cenario):
    """Trigger PG bloqueia UPDATE/DELETE em acessos_dados_cliente."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    client.get(f"/api/v1/clientes/{cliente.id}/visao-360/?finalidade=executar_os")

    with run_in_tenant_context(cenario["tenant"].id):
        a = AcessoDadosCliente.objects.filter(cliente_id=cliente.id).first()
        assert a is not None

        # UPDATE bloqueado
        with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
            with transaction.atomic():
                a.finalidade = "atendimento_pos_venda"
                a.save(update_fields=["finalidade"])

        # DELETE bloqueado
        with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
            with transaction.atomic():
                a.delete()


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_acessos_recurso_payload_sem_pii_cru(cenario):
    """R1 advogado — `recurso` jamais contem CPF/CNPJ/email/telefone."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    client.get(f"/api/v1/clientes/{cliente.id}/visao-360/?finalidade=emitir_documento_fiscal")

    with run_in_tenant_context(cenario["tenant"].id):
        a = AcessoDadosCliente.objects.filter(cliente_id=cliente.id).first()
        recurso_str = str(a.recurso)
        # Nada de CPF/CNPJ/email/telefone
        assert cliente.documento not in recurso_str
        assert cliente.nome not in recurso_str
