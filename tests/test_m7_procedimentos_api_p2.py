"""API /api/v1/procedimentos-calibracao/ — testes E2E M7 Fatia 2b (T-PROC-036).

Cobre: cadastrar (RASCUNHO) + retrieve + publicar (RASCUNHO->PUBLICADO + controle
documental) + revisar (nova versão) + publicar v2 supersede v1 + vigente (porta
via REST) + revogar + authz (atendente só lê) + Idempotency-Key obrigatória +
anexo sha256 server-side.
"""

from __future__ import annotations

import base64
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.application.metrologia.procedimentos_calibracao.anexo_storage import (
    sha256_server_side,
)
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


def _payload_cad(**kw):
    base = {
        "codigo": f"PC-{uuid4().hex[:6]}",
        "titulo": "Calibração de massa",
        "grandeza": "massa",
        "faixa_min": "0",
        "faixa_max": "1000",
        "unidade": "g",
        "metodo_norma": "OIML R76",
        "tipo_metodo": "NORMALIZADO",
        "correlation_id": str(uuid4()),
    }
    base.update(kw)
    return base


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"proc-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@proc.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@proc.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _post(client, url, payload):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


def _publicar(client, pid, numero="Rev. 01"):
    return _post(
        client,
        f"/api/v1/procedimentos-calibracao/{pid}/publicar/",
        {"numero_revisao": numero, "aprovado_por_id": str(uuid4()), "aprovado_por_nome_snapshot": "RT Fulano"},
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastra_rascunho_e_retrieve():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad())
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["estado"] == "RASCUNHO" and body["versao"] == 1
    g = client.get(f"/api/v1/procedimentos-calibracao/{body['id']}/")
    assert g.status_code == 200 and g.json()["grandeza"] == "massa"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_sem_idempotency_key_falha():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post("/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad(), format="json")
    assert r.status_code in (400, 428)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_cadastra_403():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad())
    assert r.status_code == 403


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_publica_e_resolve_vigente():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    cad = _post(client, "/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad())
    pid = cad.json()["id"]
    pub = _publicar(client, pid)
    assert pub.status_code == 200, pub.content
    assert pub.json()["estado"] == "PUBLICADO"
    # porta vigente_em via REST: faixa contida resolve
    v = client.get("/api/v1/procedimentos-calibracao/vigente/?grandeza=massa&faixa_min=10&faixa_max=20&unidade=g")
    assert v.status_code == 200, v.content
    assert v.json()["id"] == pid
    # faixa fora -> 404 (fail-closed)
    v2 = client.get("/api/v1/procedimentos-calibracao/vigente/?grandeza=massa&faixa_min=900&faixa_max=5000&unidade=g")
    assert v2.status_code == 404


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_revisa_e_publica_v2_supersede_v1():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    cad = _post(client, "/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad())
    v1 = cad.json()["id"]
    _publicar(client, v1)
    rev = _post(
        client,
        f"/api/v1/procedimentos-calibracao/{v1}/revisar/",
        {"titulo": "Massa rev", "metodo_norma": "OIML R76", "tipo_metodo": "NORMALIZADO", "correlation_id": str(uuid4())},
    )
    assert rev.status_code == 201, rev.content
    v2 = rev.json()["id"]
    assert rev.json()["versao"] == 2
    pub2 = _publicar(client, v2, numero="Rev. 02")
    assert pub2.status_code == 200, pub2.content
    assert pub2.json()["anterior_encerrada_id"] == v1
    # v1 preservada (WORM) com vigência encerrada
    g = client.get(f"/api/v1/procedimentos-calibracao/{v1}/")
    assert g.json()["vigencia_fim"] is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_revoga_procedimento():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    cad = _post(client, "/api/v1/procedimentos-calibracao/cadastrar/", _payload_cad())
    pid = cad.json()["id"]
    rev = _post(
        client,
        f"/api/v1/procedimentos-calibracao/{pid}/revogar/",
        {"motivo": "revogado por revisao normativa 2026"},
    )
    assert rev.status_code == 200, rev.content
    g = client.get(f"/api/v1/procedimentos-calibracao/{pid}/")
    assert g.json()["estado"] == "REVOGADO"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_anexo_pdf_sha256_recalculado_server_side():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    pdf_bytes = b"%PDF-1.4 conteudo de procedimento controlado"
    b64 = base64.b64encode(pdf_bytes).decode()
    r = _post(
        client,
        "/api/v1/procedimentos-calibracao/cadastrar/",
        _payload_cad(anexo_pdf_base64=b64),
    )
    assert r.status_code == 201, r.content
    # sha256 do procedimento == sha256 recalculado server-side do binario
    assert r.json()["anexo_pdf_sha256"] == sha256_server_side(pdf_bytes)
