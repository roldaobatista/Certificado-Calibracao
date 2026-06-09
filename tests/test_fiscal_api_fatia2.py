"""API /api/v1/fiscal/nfse/ — testes E2E Fatia 2 (T-FIS-033).

Cobre: emitir (perfil A + cert RBC happy / perfil A + NAO_RBC D-FIS-6 / perfil B +
cert RBC → 403 AC-FIS-001-8) + retrieve + cross-tenant 404 (INV-FIS-006) +
Idempotency-Key obrigatória + replay + dupla origem 409 (D-FIS-3) + network_timeout
503 (D-FIS-3) + PENDING→AUTHORIZED via consultar + cancelar 200 + authz (atendente
não emite).

A trava de perfil roda no use case (ADR-0073). O vínculo `tipo_acreditacao` é lido
server-side do certificado — aqui o leitor é substituído (monkeypatch) para exercitar
os cenários de perfil sem materializar um Certificado completo do M8.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from src.domain.fiscal.enums import TipoAcreditacaoVinculo
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


def _cenario(*, perfil_a: bool):
    sfx = uuid4().hex[:8]
    tenant = (
        TenantFactory(perfil_a=True, slug=f"fis-api-{sfx}")
        if perfil_a
        else TenantFactory(perfil_b=True, slug=f"fis-api-{sfx}")
    )
    admin = UsuarioFactory(email=f"adm-{sfx}@fis.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@fis.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _payload(**kw):
    base = {
        "origem_id": str(uuid4()),
        "tipo_servico": "calibracao",
        "amount_centavos": 25000,
        "issuer_taxid": "11222333000181",
        "customer_taxid": "98765432000110",
        "customer_name": "Cliente Exemplo Ltda",
        "cliente_referencia_hash": "ref-hash-abc",
        "service_description": "Calibração de balança",
        "service_code": "14.01",
        "correlation_id": str(uuid4()),
        "certificado_id": str(uuid4()),
    }
    base.update(kw)
    return base


def _patch_vinculo(monkeypatch, valor: TipoAcreditacaoVinculo | None) -> None:
    monkeypatch.setattr(
        "src.infrastructure.fiscal.views.ler_tipo_acreditacao",
        lambda *, tenant_id, certificado_id: valor,
    )


def _post(client, url, payload, key=None):
    return client.post(
        url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4())
    )


# === emitir happy + retrieve ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_a_emite_rbc_e_retrieve(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["status"] == "AUTHORIZED"
    assert body["tipo_acreditacao_vinculo"] == "RBC"
    g = client.get(f"/api/v1/fiscal/nfse/{body['nfse_id']}/")
    assert g.status_code == 200
    assert g.json()["origem_id"] == body["origem_id"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_a_emite_nao_rbc_d_fis_6(monkeypatch):
    # D-FIS-6: lab acreditado pode faturar calibração não-RBC.
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.NAO_RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 201, r.content


# === perfil incompatível (AC-FIS-001-8) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_perfil_b_rejeita_cert_rbc_403(monkeypatch):
    c = _cenario(perfil_a=False)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 403, r.content


# === authz ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_emite_403(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 403


# === idempotência ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_sem_idempotency_key_falha(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post("/api/v1/fiscal/nfse/emitir/", _payload(), format="json")
    assert r.status_code in (400, 428)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_idempotency_replay_mesmo_nfse_id(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    p = _payload()
    key = str(uuid4())
    r1 = _post(client, "/api/v1/fiscal/nfse/emitir/", p, key=key)
    r2 = _post(client, "/api/v1/fiscal/nfse/emitir/", p, key=key)
    assert r1.status_code == 201
    assert r1.json()["nfse_id"] == r2.json()["nfse_id"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_dupla_origem_409(monkeypatch):
    # Mesma origem, chaves diferentes → 1ª 201, 2ª 409 (D-FIS-3).
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    origem = str(uuid4())
    r1 = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload(origem_id=origem))
    r2 = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload(origem_id=origem))
    assert r1.status_code == 201
    assert r2.status_code == 409


# === transporte (D-FIS-3) ===


@override_settings(FISCAL_PROVIDER_MOCK_MODO="network_timeout")
@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_network_timeout_503_sem_persistir(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 503, r.content


# === PENDING → AUTHORIZED via consultar ===


@override_settings(FISCAL_PROVIDER_MOCK_MODO="pending_then_authorize")
@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_pending_resolve_via_consultar(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    assert r.status_code == 201
    nfse_id = r.json()["nfse_id"]
    assert r.json()["status"] == "PENDING"
    q = client.post(f"/api/v1/fiscal/nfse/{nfse_id}/consultar/", {}, format="json")
    assert q.status_code == 200
    assert q.json()["status"] == "AUTHORIZED"


# === cancelar ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_authorized_200(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    nfse_id = r.json()["nfse_id"]
    motivo = "cancelamento por erro de digitação no valor do serviço prestado"
    cc = _post(
        client, f"/api/v1/fiscal/nfse/{nfse_id}/cancelar/", {"motivo": motivo}
    )
    assert cc.status_code == 200, cc.content
    assert cc.json()["status"] == "CANCELED"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_motivo_curto_400(monkeypatch):
    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    nfse_id = r.json()["nfse_id"]
    cc = _post(client, f"/api/v1/fiscal/nfse/{nfse_id}/cancelar/", {"motivo": "curto"})
    assert cc.status_code == 400


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_prazo_expirado_422(monkeypatch):
    # AC-FIS-003-2: cancelamento fora da janela de 24h → 422.
    from datetime import UTC as _UTC
    from datetime import datetime as _dt
    from datetime import timedelta as _td

    c = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/fiscal/nfse/emitir/", _payload())
    nfse_id = r.json()["nfse_id"]
    # Avança o relógio do servidor +25h só no cancelamento (a nota foi emitida agora).
    futuro = _dt.now(_UTC) + _td(hours=25)

    class _Clock:
        @staticmethod
        def now(tz=None):
            return futuro

    monkeypatch.setattr("src.infrastructure.fiscal.views.datetime", _Clock)
    motivo = "cancelamento tardio fora da janela legal de 24 horas ja permitida"
    cc = _post(client, f"/api/v1/fiscal/nfse/{nfse_id}/cancelar/", {"motivo": motivo})
    assert cc.status_code == 422, cc.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_cross_tenant_404(monkeypatch):
    # AC-FIS-003-3: tenant B não cancela nota do tenant A (RLS → 404 não-vazante).
    c_a = _cenario(perfil_a=True)
    c_b = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client_a = APIClient()
    _autenticar(client_a, c_a["admin"], c_a["tenant"])
    r = _post(client_a, "/api/v1/fiscal/nfse/emitir/", _payload())
    nfse_id = r.json()["nfse_id"]
    client_b = APIClient()
    _autenticar(client_b, c_b["admin"], c_b["tenant"])
    motivo = "tentativa de cancelamento cross-tenant que deve ser barrada pela RLS"
    cc = _post(client_b, f"/api/v1/fiscal/nfse/{nfse_id}/cancelar/", {"motivo": motivo})
    assert cc.status_code == 404, cc.content


# === cross-tenant (INV-FIS-006) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cross_tenant_retrieve_404(monkeypatch):
    c_a = _cenario(perfil_a=True)
    c_b = _cenario(perfil_a=True)
    _patch_vinculo(monkeypatch, TipoAcreditacaoVinculo.RBC)
    client_a = APIClient()
    _autenticar(client_a, c_a["admin"], c_a["tenant"])
    r = _post(client_a, "/api/v1/fiscal/nfse/emitir/", _payload())
    nfse_id = r.json()["nfse_id"]
    # Tenant B não enxerga a nota do tenant A.
    client_b = APIClient()
    _autenticar(client_b, c_b["admin"], c_b["tenant"])
    g = client_b.get(f"/api/v1/fiscal/nfse/{nfse_id}/")
    assert g.status_code == 404
