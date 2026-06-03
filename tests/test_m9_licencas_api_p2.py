"""API /api/v1/licencas/ — testes E2E M9 Fatia 2 (T-LIC-044). PG-real.

Cobre: cadastrar (ALVARA não-bloqueante) + retrieve + Idempotency-Key obrigatória +
CGCRE perfil D → 403 (defesa L6) + promover B→A (cadastra Licenca + popula o cache
`Tenant.acreditacao_vigencia_fim` — FECHA GATE-CER-CGCRE-VIG-DATA-POPULAR) +
idempotência da promoção + renovar + modo emergencial (com bloqueio pré-inserido).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
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
_JUST = "liberacao emergencial por atraso na renovacao da ART do signatario " + "x" * 50


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


def _cenario(perfil: str):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"lic-api-{sfx}", **{f"perfil_{perfil.lower()}": True})
    admin = UsuarioFactory(email=f"adm-{sfx}@lic.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _post(client, url, payload):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


def _cad_payload(**kw):
    base = {
        "tipo": "ALVARA",
        "numero": "ALV-1",
        "orgao_emissor": "Prefeitura",
        "vigencia_inicio": "2026-01-01",
        "vigencia_fim": "2027-01-01",
        "anexo_id": str(uuid4()),
        "anexo_sha256": "a" * 64,
        "correlation_id": str(uuid4()),
    }
    base.update(kw)
    return base


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_alvara_e_retrieve():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/licencas/cadastrar/", _cad_payload())
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["bloqueante"] is False
    assert body["status"] in ("VIGENTE", "VENCE_EM_BREVE", "VENCIDO")
    g = client.get(f"/api/v1/licencas/{body['id']}/")
    assert g.status_code == 200
    assert g.json()["tipo"] == "ALVARA"
    assert len(g.json()["revisoes"]) == 1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_sem_idempotency_key_falha():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post("/api/v1/licencas/cadastrar/", _cad_payload(), format="json")
    assert r.status_code == 400


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cgcre_perfil_d_rejeitado_403():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(
        client, "/api/v1/licencas/cadastrar/",
        _cad_payload(
            tipo="ACREDITACAO_CGCRE", numero="CRL-D", orgao_emissor="CGCRE",
            escopo="massa 0..10kg",
        ),
    )
    assert r.status_code == 403, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_promover_b_para_a_popula_cache_e_fecha_gate():
    c = _cenario("b")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    nova_vig = "2030-12-31"
    r = _post(
        client, "/api/v1/licencas/promover-perfil-a/",
        {
            "perfil_novo": "A",
            "numero": "CRL-0420",
            "orgao_emissor": "CGCRE",
            "vigencia_inicio": "2026-01-01",
            "vigencia_fim": nova_vig,
            "escopo": "massa 0..10kg; volume 0..1L",
            "numero_cgcre": "CRL-0420",
            "assinatura_a3_id": str(uuid4()),
            "motivo": "promocao a perfil A apos auditoria CGCRE concluida com sucesso " + "y" * 50,
            "auditor_cgcre": "Auditor Fulano",
            "anexo_id": str(uuid4()),
            "anexo_sha256": "b" * 64,
            "correlation_id": str(uuid4()),
        },
    )
    assert r.status_code == 201, r.content
    assert r.json()["promovido"] is True
    # FECHA GATE-CER-CGCRE-VIG-DATA-POPULAR: o cache que o M8 lê está populado.
    c["tenant"].refresh_from_db()
    assert c["tenant"].perfil_regulatorio == "A"
    assert c["tenant"].acreditacao_vigencia_fim == date(2030, 12, 31)


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_promover_idempotente_nao_repromove():
    c = _cenario("b")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    payload = {
        "perfil_novo": "A", "numero": "CRL-9", "orgao_emissor": "CGCRE",
        "vigencia_inicio": "2026-01-01", "vigencia_fim": "2030-12-31",
        "escopo": "massa", "numero_cgcre": "CRL-9", "assinatura_a3_id": str(uuid4()),
        "motivo": "promocao perfil A auditoria concluida " + "z" * 70,
        "auditor_cgcre": "Auditor", "anexo_id": str(uuid4()),
        "anexo_sha256": "c" * 64, "correlation_id": str(uuid4()),
    }
    r1 = _post(client, "/api/v1/licencas/promover-perfil-a/", payload)
    assert r1.status_code == 201, r1.content
    # Mesma chave natural, nova Idempotency-Key → use case detecta no-op (promovido=False).
    r2 = _post(client, "/api/v1/licencas/promover-perfil-a/", payload)
    assert r2.status_code == 201, r2.content
    assert r2.json()["promovido"] is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_renovar_cria_revisao():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/licencas/cadastrar/", _cad_payload(numero="ALV-REN"))
    doc_id = r.json()["id"]
    rr = _post(
        client, f"/api/v1/licencas/{doc_id}/renovar/",
        {
            "nova_vigencia_inicio": "2027-01-01",
            "nova_vigencia_fim": "2028-01-01",
            "anexo_id": str(uuid4()),
            "anexo_sha256": "d" * 64,
            "motivo": "RENOVACAO",
            "correlation_id": str(uuid4()),
        },
    )
    assert rr.status_code == 201, rr.content
    assert rr.json()["numero_revisao"] == 2


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_acionar_emergencial_com_bloqueio_ativo():
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        BloqueioOperacional,
    )

    c = _cenario("a")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    # Cadastra uma ART (bloqueante) e abre um bloqueio ativo manualmente.
    r = _post(
        client, "/api/v1/licencas/cadastrar/",
        _cad_payload(tipo="ART", numero="ART-77", orgao_emissor="CREA"),
    )
    assert r.status_code == 201, r.content
    doc_id = r.json()["id"]
    # Insere o bloqueio direto — precisa do contexto de tenant (RLS de INSERT compara
    # com current_setting('app.active_tenant_id')::uuid; fora de contexto vira ''::uuid).
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    with run_in_tenant_context(c["tenant"].id):
        BloqueioOperacional.objects.create(
            tenant_id=c["tenant"].id,
            documento_id=doc_id,
            tipo_documento="ART",
            operacao_bloqueada="assinatura_certificado",
            data_inicio_bloqueio=datetime(2026, 6, 1, tzinfo=UTC),
        )
    er = _post(
        client, f"/api/v1/licencas/{doc_id}/acionar-emergencial/",
        {
            "operacao_executada": "assinatura_certificado",
            "justificativa": _JUST,
            "assinatura_a3_id": str(uuid4()),
            "janela_dias": 5,
            "correlation_id": str(uuid4()),
        },
    )
    assert er.status_code == 201, er.content
    assert er.json()["libera_apenas_nao_rbc"] is False  # ART não é CGCRE


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_acionar_emergencial_sem_bloqueio_409():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/licencas/cadastrar/", _cad_payload(numero="ALV-NB"))
    doc_id = r.json()["id"]
    er = _post(
        client, f"/api/v1/licencas/{doc_id}/acionar-emergencial/",
        {
            "operacao_executada": "x",
            "justificativa": _JUST,
            "assinatura_a3_id": str(uuid4()),
            "janela_dias": 3,
            "correlation_id": str(uuid4()),
        },
    )
    assert er.status_code == 409, er.content
