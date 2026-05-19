"""US-CLI-001 — testes que cobrem o completar do AC-1 + AC-2.

Cravados pelo plano US-CLI-001 §"Sequencia revisada de tasks T-CLI-008":

1. test_aceite_lgpd_pf_obrigatorio
2. test_aceite_lgpd_pj_dispensa_com_motivo
3. test_aceite_lgpd_pj_sem_motivo_e_400
4. test_dedup_retorna_409_estruturada_com_link
5. test_dedup_cross_tenant_nao_vaza (TL1 critica)
6. test_post_cliente_grava_audit_cliente_criado_sem_pii (TL3)

Bonus:
7. test_aceite_lgpd_versao_eh_snapshot_da_constante
8. test_aceite_lgpd_ip_hash_eh_calculado_e_nao_aceito_do_payload
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.lgpd import VERSAO_VIGENTE
from src.infrastructure.clientes.models import Cliente

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
    tenant = TenantFactory(slug=f"us001-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@us001.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


@pytest.mark.django_db(transaction=True)
def test_aceite_lgpd_pf_obrigatorio(cenario):
    """PF sem aceite_lgpd_em = 400 (R3 + AC-CLI-001-2)."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PF",
            "documento": "52998224725",
            "nome": "Joao PF",
        },
        format="json",
    )
    assert response.status_code == 400, response.content
    assert "aceite_lgpd_em" in response.json()


@pytest.mark.django_db(transaction=True)
def test_aceite_lgpd_pj_dispensa_com_motivo(cenario):
    """PJ sem PF associada pode dispensar via motivo (R3 advogado)."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "PJ Sem PF LTDA",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["aceite_lgpd_em"] is None
    assert body["aceite_lgpd_dispensa_motivo"] == "pj_sem_pf_associada"


@pytest.mark.django_db(transaction=True)
def test_aceite_lgpd_pj_sem_motivo_e_400(cenario):
    """PJ sem aceite E sem motivo de dispensa = 400."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "PJ Sem Aceite Sem Motivo",
        },
        format="json",
    )
    assert response.status_code == 400, response.content
    assert "aceite_lgpd_dispensa_motivo" in response.json()


@pytest.mark.django_db(transaction=True)
def test_dedup_retorna_409_estruturada_com_link(cenario):
    """AC-CLI-001-1 — segundo POST com mesmo documento devolve 409 com link."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    primeiro = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "Primeiro",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert primeiro.status_code == 201
    primeiro_id = primeiro.json()["id"]

    segundo = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11.222.333/0001-81",  # mesmo documento, formatado
            "nome": "Duplicado",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert segundo.status_code == 409, segundo.content
    body = segundo.json()
    assert body["detail"] == "cliente_ja_existe"
    assert body["cliente_id"] == primeiro_id
    assert body["link"].endswith(f"/{primeiro_id}/")


@pytest.mark.django_db(transaction=True)
def test_dedup_cross_tenant_nao_vaza(cenario):
    """TL1 CRITICA — mesmo documento em tenants diferentes = 201 em ambos.

    Nao pode vazar via 409 que existe em outro tenant.
    """
    client_a = APIClient()
    _autenticar(client_a, cenario["admin"], cenario["tenant"])

    # POST em tenant A
    r_a = client_a.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "Em A",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert r_a.status_code == 201

    # Tenant B totalmente separado
    suffix_b = uuid4().hex[:8]
    tenant_b = TenantFactory(slug=f"b-us001-{suffix_b}")
    admin_b = UsuarioFactory(email=f"adm-b-{suffix_b}@us001.local")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    invalidate_user_cache(admin_b.id, tenant_b.id)

    client_b = APIClient()
    _autenticar(client_b, admin_b, tenant_b)

    # POST mesmo documento em tenant B — DEVE ser 201, NAO 409
    r_b = client_b.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": "11222333000181",
            "nome": "Em B",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert r_b.status_code == 201, (
        f"VAZAMENTO CROSS-TENANT: tenant B recebeu {r_b.status_code} ao "
        f"cadastrar documento que existe em tenant A. Conteudo: {r_b.content!r}"
    )


@pytest.mark.django_db(transaction=True)
def test_post_cliente_grava_audit_cliente_criado_sem_pii(cenario):
    """TL3 + AC-CLI-001-2 — POST grava action='cliente.criado' SEM CPF/CNPJ cru."""
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    documento_cru = "11222333000181"
    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PJ",
            "documento": documento_cru,
            "nome": "Audit Test",
            "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    cliente_id = response.json()["id"]

    with run_in_tenant_context(cenario["tenant"].id):
        audit = Auditoria.objects.filter(
            action="cliente.criado",
            resource_summary=cliente_id,
        ).first()
    assert audit is not None, "Audit 'cliente.criado' nao gravado"
    payload = audit.payload_jsonb
    assert payload["cliente_id"] == cliente_id
    assert payload["tipo_pessoa"] == "PJ"
    # PII NAO pode estar no payload cru
    assert "documento" not in payload, "PII vazada: campo 'documento' no payload"
    assert documento_cru not in str(payload), (
        f"PII vazada: CNPJ '{documento_cru}' aparece em algum campo do payload"
    )
    # Hash deve estar — FA-A1: versionado "vN:"+64hex (nao mais 64 cru).
    assert payload["documento_hash"], "Hash do documento ausente do payload"
    import re as _re

    assert _re.fullmatch(
        r"v[\w-]+:[0-9a-f]{64}", payload["documento_hash"]
    ), f"hash sem prefixo de versao FA-A1: {payload['documento_hash']!r}"


@pytest.mark.django_db(transaction=True)
def test_aceite_lgpd_versao_eh_snapshot_da_constante(cenario):
    """`aceite_lgpd_versao` e preenchida com VERSAO_VIGENTE automaticamente."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    agora_iso = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PF",
            "documento": "52998224725",
            "nome": "PF Versao Snapshot",
            "aceite_lgpd_em": agora_iso,
            "aceite_lgpd_origem": "balcao",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["aceite_lgpd_versao"] == VERSAO_VIGENTE


@pytest.mark.django_db(transaction=True)
def test_aceite_lgpd_ip_hash_nao_aceito_do_payload(cenario):
    """Cliente nao pode forjar ip_hash via payload (read_only)."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    agora_iso = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/v1/clientes/",
        data={
            "tipo_pessoa": "PF",
            "documento": "52998224725",
            "nome": "PF IP Forge",
            "aceite_lgpd_em": agora_iso,
            "aceite_lgpd_ip_hash": "deadbeef" * 8,  # tentativa de forge
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    # ip_hash forjado e ignorado; preenchido pelo backend
    assert body["aceite_lgpd_ip_hash"] != "deadbeef" * 8
