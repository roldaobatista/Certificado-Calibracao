"""API /api/v1/escopos-cmc/ — testes E2E M6 Fatia 2 (T-ECMC-031).

Cobre: cadastrar (perfil A escopo RBC) + retrieve + declarar_capacidade (perfil B,
rbc forçado False) + anti-fraude (B pedindo RBC) + revisar (nova versão preserva
anterior) + revogar + authz (atendente só lê) + Idempotency-Key obrigatória.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_DBS = ["default", "breaker_writer"]


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


def _payload(**kw):
    base = {
        "grandeza": "massa",
        "faixa_min": "0",
        "faixa_max": "1000",
        "unidade": "g",
        "cmc_forma": "ABSOLUTA",
        "cmc_valor": "0.001",
        "cmc_unidade": "g",
        "rbc_acreditado": True,
        "procedimento_id": str(uuid4()),
        "correlation_id": str(uuid4()),
    }
    base.update(kw)
    return base


def _cenario(slug_perfil_a: bool):
    sfx = uuid4().hex[:8]
    tenant = (
        TenantFactory(perfil_a=True, slug=f"ecmc-api-{sfx}")
        if slug_perfil_a
        else TenantFactory(perfil_b=True, slug=f"ecmc-api-{sfx}")
    )
    admin = UsuarioFactory(email=f"adm-{sfx}@ecmc.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@ecmc.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _post(client, url, payload):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_a_cadastra_rbc_e_retrieve():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/cadastrar/", _payload())
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["rbc_acreditado"] is True
    assert body["versao"] == 1
    g = client.get(f"/api/v1/escopos-cmc/{body['id']}/")
    assert g.status_code == 200
    assert g.json()["grandeza"] == "massa"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_sem_idempotency_key_falha():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post("/api/v1/escopos-cmc/cadastrar/", _payload(), format="json")
    assert r.status_code in (400, 428)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_cadastra_403():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/cadastrar/", _payload())
    assert r.status_code == 403


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_b_declara_capacidade_interna_rbc_false():
    c = _cenario(slug_perfil_a=False)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(
        client,
        "/api/v1/escopos-cmc/declarar-capacidade/",
        _payload(rbc_acreditado=False, procedimento_id=None),
    )
    assert r.status_code == 201, r.content
    assert r.json()["rbc_acreditado"] is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_b_pedindo_rbc_e_forcado_false_anti_fraude():
    """FAIL L6 fechado: B pedindo rbc_acreditado=True é forçado a False (ADR-0075)."""
    c = _cenario(slug_perfil_a=False)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    # procedimento_id ausente: ok, pois rbc efetivo será False (não exige método)
    r = _post(client, "/api/v1/escopos-cmc/cadastrar/", _payload(procedimento_id=None))
    assert r.status_code == 201, r.content
    assert r.json()["rbc_acreditado"] is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_revisar_cria_v2_e_encerra_v1():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/cadastrar/", _payload())
    v1_id = r.json()["id"]
    rev = _post(
        client,
        f"/api/v1/escopos-cmc/{v1_id}/revisar/",
        {
            "cmc_forma": "ABSOLUTA",
            "cmc_valor": "0.0005",
            "cmc_unidade": "g",
            "correlation_id": str(uuid4()),
        },
    )
    assert rev.status_code == 201, rev.content
    assert rev.json()["versao"] == 2
    # v1 preservada com vigência encerrada
    g = client.get(f"/api/v1/escopos-cmc/{v1_id}/")
    assert g.json()["vigencia_fim"] is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_revogar_escopo():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/cadastrar/", _payload())
    eid = r.json()["id"]
    rev = _post(
        client,
        f"/api/v1/escopos-cmc/{eid}/revogar/",
        {"motivo": "revogado por reducao de escopo CGCRE 2026"},
    )
    assert rev.status_code == 200, rev.content
    g = client.get(f"/api/v1/escopos-cmc/{eid}/")
    assert g.json()["estado"] == "REVOGADO"
