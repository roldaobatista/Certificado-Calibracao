"""API /api/v1/padroes/ — testes E2E M5 P5 (T-PAD-041).

Cobre: cadastrar (US-PAD-001) + retrieve + disponiveis (porta) + ciclo de recal
via REST (envio/retorno/aprovar — exercita o GUC ponta-a-ponta) + revogar
rastreabilidade (C-5) + authz (atendente so le) + Idempotency-Key obrigatoria.
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


def _payload_cadastrar(**kw):
    base = {
        "numero_serie": f"PAD-{uuid4().hex[:8]}",
        "fabricante": "Mettler",
        "modelo": "XPR",
        "subtipo": "PRINCIPAL",
        "grandezas": ["massa"],
        "faixas": [{"inferior": "0", "superior": "1000", "unidade": "g"}],
        "incertezas_certificado": [
            {"valor": "0.001", "fator_k": "2", "nivel_confianca": "0.9545", "unidade": "g"}
        ],
        "vinculacao": "INMETRO",
        "classe": "E2",
        "validade_certificado_rastreabilidade": "2027-01-01",
        "proximo_recal": "2027-01-01",
        "intervalo_recal_meses": 12,
        "intervalo_vi_meses": 3,
        "criterio_intervalo": "cl. 6.4.7 historico de estabilidade",
        "correlation_id": str(uuid4()),
    }
    base.update(kw)
    return base


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"pad-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@pad.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@pad.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _post(client, url, payload):
    return client.post(
        url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4())
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cadastrar_e_retrieve(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    r = _post(client, "/api/v1/padroes/cadastrar/", _payload_cadastrar())
    assert r.status_code == 201, r.content
    pid = r.json()["id"]
    assert r.json()["estado"] == "EM_USO"
    g = client.get(f"/api/v1/padroes/{pid}/")
    assert g.status_code == 200
    assert g.json()["id"] == pid


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cadastrar_sem_idempotency_key_falha(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    r = client.post(
        "/api/v1/padroes/cadastrar/", _payload_cadastrar(), format="json"
    )
    assert r.status_code in (400, 428)  # Idempotency-Key obrigatoria


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_atendente_nao_cadastra_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["atendente"], cenario["tenant"])
    r = _post(client, "/api/v1/padroes/cadastrar/", _payload_cadastrar())
    assert r.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rbc_sem_perfil_a_bloqueia_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    # tenant default nao e perfil A -> vinculacao RBC deve falhar (INV-PAD-005)
    r = _post(
        client, "/api/v1/padroes/cadastrar/", _payload_cadastrar(vinculacao="RBC")
    )
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ciclo_recal_via_rest(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    pid = _post(client, "/api/v1/padroes/cadastrar/", _payload_cadastrar()).json()["id"]

    env = _post(client, f"/api/v1/padroes/{pid}/recal-envio/", {"lab_externo": "Lab RBC"})
    assert env.status_code == 201, env.content
    assert env.json()["estado"] == "EM_RECAL_EXTERNO"
    recal_id = env.json()["recal_id"]

    ret = _post(
        client,
        f"/api/v1/padroes/recal/{recal_id}/retorno/",
        {
            "status": "RETORNADO",
            "incertezas_novas": [
                {"valor": "0.0005", "fator_k": "2", "nivel_confianca": "0.9545", "unidade": "g"}
            ],
            "validade_nova": "2028-07-01",
            "valor_convencional_novo": "1.0",
        },
    )
    assert ret.status_code == 200, ret.content
    assert ret.json()["estado"] == "RECAL_RETORNADO_PENDENTE_APROVACAO"

    apr = _post(
        client,
        f"/api/v1/padroes/recal/{recal_id}/aprovar/",
        {"aprovado": True, "proximo_recal_novo": "2028-06-01"},
    )
    assert apr.status_code == 200, apr.content
    assert apr.json()["estado"] == "EM_USO"
    # incertezas atualizadas via GUC -> proximo_recal mudou
    assert apr.json()["proximo_recal"] == "2028-06-01"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_rastreabilidade_remove_de_disponiveis(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    pid = _post(client, "/api/v1/padroes/cadastrar/", _payload_cadastrar()).json()["id"]

    disp1 = client.get("/api/v1/padroes/disponiveis/")
    assert disp1.status_code == 200
    assert pid in disp1.json()["disponiveis"]

    rev = _post(
        client,
        f"/api/v1/padroes/{pid}/revogar-rastreabilidade/",
        {"motivo": "origem perdeu acreditacao CGCRE"},
    )
    assert rev.status_code == 200, rev.content
    assert rev.json()["rastreabilidade_origem_revogada"] is True

    disp2 = client.get("/api/v1/padroes/disponiveis/")
    assert pid not in disp2.json()["disponiveis"]  # bloqueado pela porta
