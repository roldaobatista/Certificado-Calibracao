"""API /api/v1/contas-receber/ — testes E2E Fatia 2a (T-CR-037).

Cobre (Fatia 2a — núcleo manual, sem gateway/webhook):
  - criar manual perfil A + categoria RBC → 201
  - criar manual perfil B + categoria RBC → 403 (INV-FIN-PERFIL-001)
  - criar sem Idempotency-Key → 400/428
  - replay mesma key → mesmo titulo_id
  - criar manual perfil A → categoria derivada automaticamente (RBC)
  - baixar manual total → estado pago + Pagamento + evento publicado
  - baixar manual parcial → estado parcialmente_pago
  - cancelar título sem pagamento → 200
  - cancelar com pagamento → 409 (TituloComPagamentoParcial)
  - cross-tenant retrieve → 404 (INV-TENANT-001/003)
  - authz sem papel (atendente) → 403 em escrita

Fora de escopo desta fatia (Fatia 2b):
  emitir-boleto / emitir-pix-recorrente / webhook / override-bloqueio
"""

from __future__ import annotations

from datetime import date, timedelta
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

_VENCIMENTO_FUTURO = (date.today() + timedelta(days=30)).isoformat()


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


def _cenario(*, perfil_a: bool = True, perfil_b: bool = False):
    sfx = uuid4().hex[:8]
    if perfil_a:
        tenant = TenantFactory(perfil_a=True, slug=f"cr-api-{sfx}")
    elif perfil_b:
        tenant = TenantFactory(perfil_b=True, slug=f"cr-api-{sfx}")
    else:
        tenant = TenantFactory(slug=f"cr-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@cr.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@cr.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _payload_criar(**kw):
    # hash_original exige ≥32 chars (ReferenciaPIIAnonimizavel — molde HMAC hex)
    base = {
        "cliente_referencia_hash": uuid4().hex,  # 32 chars hexadecimal
        "cliente_key_id": "v1",
        "valor_centavos": 15000,
        "data_vencimento": _VENCIMENTO_FUTURO,
        "meio": "boleto",
    }
    base.update(kw)
    return base


def _post(client, url, payload, key=None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


# ===== criar manual happy path =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_perfil_a_categoria_rbc_201():
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    p = _payload_criar(categoria_receita="CALIBRACAO_RBC")
    r = _post(client, "/api/v1/contas-receber/criar/", p)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["estado"] == "emitido"
    assert body["categoria_receita"] == "CALIBRACAO_RBC"
    assert body["perfil_no_evento"] == "A"
    assert body["origem"] == "manual"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_perfil_a_categoria_derivada_rbc():
    """Perfil A sem categoria → derivada automaticamente como CALIBRACAO_RBC (D-CR-5)."""
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    p = _payload_criar()  # sem categoria_receita
    r = _post(client, "/api/v1/contas-receber/criar/", p)
    assert r.status_code == 201, r.content
    assert r.json()["categoria_receita"] == "CALIBRACAO_RBC"


# ===== INV-FIN-PERFIL-001 =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_perfil_b_categoria_rbc_403():
    """Perfil B + CALIBRACAO_RBC → 403 (INV-FIN-PERFIL-001 / D-CR-5)."""
    c = _cenario(perfil_a=False, perfil_b=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    p = _payload_criar(categoria_receita="CALIBRACAO_RBC")
    r = _post(client, "/api/v1/contas-receber/criar/", p)
    assert r.status_code == 403, r.content


# ===== authz =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_cria_403():
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar())
    assert r.status_code == 403


# ===== idempotência =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_sem_idempotency_key_falha():
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post("/api/v1/contas-receber/criar/", _payload_criar(), format="json")
    assert r.status_code in (400, 428)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_idempotency_replay_mesmo_titulo_id():
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    p = _payload_criar()
    key = str(uuid4())
    r1 = _post(client, "/api/v1/contas-receber/criar/", p, key=key)
    r2 = _post(client, "/api/v1/contas-receber/criar/", p, key=key)
    assert r1.status_code == 201, r1.content
    assert r1.json()["titulo_id"] == r2.json()["titulo_id"]


# ===== retrieve / list =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_retrieve_titulo_criado():
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar())
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]
    g = client.get(f"/api/v1/contas-receber/{titulo_id}/")
    assert g.status_code == 200
    assert g.json()["titulo_id"] == titulo_id


# ===== cross-tenant (INV-TENANT-001/003) =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cross_tenant_retrieve_404():
    c_a = _cenario(perfil_a=True)
    c_b = _cenario(perfil_a=True)
    client_a = APIClient()
    _autenticar(client_a, c_a["admin"], c_a["tenant"])
    r = _post(client_a, "/api/v1/contas-receber/criar/", _payload_criar())
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]

    client_b = APIClient()
    _autenticar(client_b, c_b["admin"], c_b["tenant"])
    g = client_b.get(f"/api/v1/contas-receber/{titulo_id}/")
    assert g.status_code == 404, g.content


# ===== baixar manual =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_baixar_manual_total_estado_pago():
    """Baixar o valor integral → estado pago + Pagamento criado."""
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    # Cria título de 15000 centavos
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar(valor_centavos=15000))
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]
    # Baixa o valor integral
    payload_baixar = {
        "valor_centavos": 15000,
        "data_pagamento": date.today().isoformat(),
    }
    rb = _post(client, f"/api/v1/contas-receber/{titulo_id}/baixar-manual/", payload_baixar)
    assert rb.status_code == 200, rb.content
    body = rb.json()
    assert body["estado"] == "pago", body
    assert body["pagamento_id"] is not None
    assert body["valor_pago"] == 15000
    # Verifica persistência via retrieve
    g = client.get(f"/api/v1/contas-receber/{titulo_id}/")
    assert g.json()["estado"] == "pago"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_baixar_manual_parcial_estado_parcialmente_pago():
    """Baixar valor menor → estado parcialmente_pago."""
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar(valor_centavos=20000))
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]
    payload_baixar = {
        "valor_centavos": 5000,
        "data_pagamento": date.today().isoformat(),
    }
    rb = _post(client, f"/api/v1/contas-receber/{titulo_id}/baixar-manual/", payload_baixar)
    assert rb.status_code == 200, rb.content
    assert rb.json()["estado"] == "parcialmente_pago"


# ===== cancelar =====


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_titulo_sem_pagamento_200():
    """Cancelar título sem nenhum pagamento → 200."""
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar())
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]
    rc = _post(
        client,
        f"/api/v1/contas-receber/{titulo_id}/cancelar/",
        {"razao": "cancelamento de teste"},
    )
    assert rc.status_code == 200, rc.content
    assert rc.json()["estado"] == "cancelado"
    assert rc.json()["cancelado_em"] is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_titulo_com_pagamento_409():
    """Cancelar título com pagamento parcial → 409 (TituloComPagamentoParcial)."""
    c = _cenario(perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/contas-receber/criar/", _payload_criar(valor_centavos=10000))
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]
    # Baixa parcial
    _post(
        client,
        f"/api/v1/contas-receber/{titulo_id}/baixar-manual/",
        {"valor_centavos": 3000, "data_pagamento": date.today().isoformat()},
    )
    # Tenta cancelar → deve falhar
    rc = _post(
        client,
        f"/api/v1/contas-receber/{titulo_id}/cancelar/",
        {"razao": "tentativa de cancelar com pagamento"},
    )
    assert rc.status_code == 409, rc.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_cancela_403():
    """Atendente sem papel cancelar → 403."""
    c = _cenario(perfil_a=True)
    client_adm = APIClient()
    _autenticar(client_adm, c["admin"], c["tenant"])
    r = _post(client_adm, "/api/v1/contas-receber/criar/", _payload_criar())
    assert r.status_code == 201
    titulo_id = r.json()["titulo_id"]

    client_ate = APIClient()
    _autenticar(client_ate, c["atendente"], c["tenant"])
    rc = _post(
        client_ate,
        f"/api/v1/contas-receber/{titulo_id}/cancelar/",
        {"razao": "cancelamento por atendente"},
    )
    assert rc.status_code == 403
