"""API /api/v1/padroes/ — testes E2E M5 P10 (fechamento).

Cobre as 3 frentes que o Roldao mandou construir (P9 PROD-PAD-01/02/03 + PERF-001):
  - VinculoAuxiliar CRUD via REST (US-PAD-007-4) + INV-PAD-007 ativado ponta-a-ponta.
  - Dossie CGCRE (US-PAD-006) com gate perfil A.
  - Carta de controle read-model (US-PAD-008-1) com gate perfil A.
  - PERF-001: baseline assertNumQueries de GET /disponiveis/.
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


def _post(client, url, payload):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


def _cenario(perfil_a: bool):
    sfx = uuid4().hex[:8]
    tenant = (
        TenantFactory(slug=f"pad-p10-{sfx}", perfil_a=True)
        if perfil_a
        else TenantFactory(slug=f"pad-p10-{sfx}")
    )
    admin = UsuarioFactory(email=f"adm-{sfx}@pad.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@pad.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


@pytest.fixture
def cenario(db):
    return _cenario(perfil_a=False)


@pytest.fixture
def cenario_a(db):
    return _cenario(perfil_a=True)


def _criar_padrao(client, **kw) -> str:
    r = _post(client, "/api/v1/padroes/cadastrar/", _payload_cadastrar(**kw))
    assert r.status_code == 201, r.content
    return r.json()["id"]


# ---------------------------------------------------------------- vinculo CRUD
@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_e_revogar_vinculo_auxiliar(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    principal = _criar_padrao(client)
    auxiliar = _criar_padrao(client, subtipo="AUXILIAR_AMBIENTAL", grandezas=["temperatura"])

    cr = _post(
        client,
        f"/api/v1/padroes/{principal}/vinculos-auxiliares/",
        {
            "padrao_auxiliar_id": auxiliar,
            "grandeza_influencia": "temperatura",
            "correlation_id": str(uuid4()),
        },
    )
    assert cr.status_code == 201, cr.content
    vinculo_id = cr.json()["id"]
    assert cr.json()["padrao_auxiliar_id"] == auxiliar
    assert cr.json()["revogado_em"] is None

    rev = _post(
        client,
        f"/api/v1/padroes/vinculos-auxiliares/{vinculo_id}/revogar/",
        {},
    )
    assert rev.status_code == 200, rev.content
    assert rev.json()["revogado_em"] is not None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_vinculo_auxiliar_invalido_quando_principal_nao_eh_auxiliar(cenario):
    """auxiliar com subtipo PRINCIPAL -> 400 (cl. 6.4.5)."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    principal = _criar_padrao(client)
    outro_principal = _criar_padrao(client)  # subtipo PRINCIPAL (default)

    cr = _post(
        client,
        f"/api/v1/padroes/{principal}/vinculos-auxiliares/",
        {
            "padrao_auxiliar_id": outro_principal,
            "grandeza_influencia": "temperatura",
            "correlation_id": str(uuid4()),
        },
    )
    assert cr.status_code == 400, cr.content


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_vinculo_sem_idempotency_key_falha(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    principal = _criar_padrao(client)
    auxiliar = _criar_padrao(client, subtipo="AUXILIAR_AMBIENTAL", grandezas=["temperatura"])
    r = client.post(
        f"/api/v1/padroes/{principal}/vinculos-auxiliares/",
        {
            "padrao_auxiliar_id": auxiliar,
            "grandeza_influencia": "temperatura",
            "correlation_id": str(uuid4()),
        },
        format="json",
    )
    assert r.status_code in (400, 428)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_atendente_nao_gere_vinculo_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    principal = _criar_padrao(client)
    auxiliar = _criar_padrao(client, subtipo="AUXILIAR_AMBIENTAL", grandezas=["temperatura"])

    cli_at = APIClient()
    _autenticar(cli_at, cenario["atendente"], cenario["tenant"])
    cr = _post(
        cli_at,
        f"/api/v1/padroes/{principal}/vinculos-auxiliares/",
        {
            "padrao_auxiliar_id": auxiliar,
            "grandeza_influencia": "temperatura",
            "correlation_id": str(uuid4()),
        },
    )
    assert cr.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_pad_007_via_rest_auxiliar_doente_bloqueia_principal(cenario):
    """INV-PAD-007 (cl. 6.4.5) ATIVADO via REST: auxiliar com rastreabilidade
    revogada bloqueia o principal vinculado em /disponiveis/."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    principal = _criar_padrao(client)
    auxiliar = _criar_padrao(client, subtipo="AUXILIAR_AMBIENTAL", grandezas=["temperatura"])
    _post(
        client,
        f"/api/v1/padroes/{principal}/vinculos-auxiliares/",
        {
            "padrao_auxiliar_id": auxiliar,
            "grandeza_influencia": "temperatura",
            "correlation_id": str(uuid4()),
        },
    )

    disp1 = client.get("/api/v1/padroes/disponiveis/")
    assert principal in disp1.json()["disponiveis"]

    # auxiliar fica doente (rastreabilidade revogada)
    rev = _post(
        client,
        f"/api/v1/padroes/{auxiliar}/revogar-rastreabilidade/",
        {"motivo": "auxiliar perdeu rastreabilidade da origem"},
    )
    assert rev.status_code == 200, rev.content

    disp2 = client.get("/api/v1/padroes/disponiveis/")
    # principal AGORA bloqueado pelo auxiliar doente (INV-PAD-007)
    assert principal not in disp2.json()["disponiveis"]
    assert auxiliar not in disp2.json()["disponiveis"]


# ---------------------------------------------------------------- dossie CGCRE
@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dossie_cgcre_perfil_a(cenario_a):
    client = APIClient()
    _autenticar(client, cenario_a["admin"], cenario_a["tenant"])
    pid = _criar_padrao(client)
    r = client.get(f"/api/v1/padroes/{pid}/dossie-cgcre/")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["padrao"]["id"] == pid
    assert "recals_externos" in body
    assert "verificacoes_intermediarias" in body
    # AC-PAD-006-1: uso em calibracoes (M4) + ancora de integridade hash-chain (ADR-0064)
    assert "uso_em_calibracoes" in body
    assert isinstance(body["uso_em_calibracoes"], list)
    assert body["ancora_integridade"]["adr"] == "ADR-0064"
    assert "head_hash" in body["ancora_integridade"]
    assert "eventos_worm" in body["ancora_integridade"]
    assert body["versao_dossie"] == "1.1"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dossie_cgcre_nao_perfil_a_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    pid = _criar_padrao(client)
    r = client.get(f"/api/v1/padroes/{pid}/dossie-cgcre/")
    assert r.status_code == 403, r.content


# ---------------------------------------------------------------- carta controle
@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_carta_controle_perfil_a(cenario_a):
    client = APIClient()
    _autenticar(client, cenario_a["admin"], cenario_a["tenant"])
    pid = _criar_padrao(client)
    r = client.get(f"/api/v1/padroes/{pid}/carta-controle/")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["padrao_id"] == pid
    # AC-PAD-008-1: sem VIs (<10 pontos em 24m) -> amostra insuficiente, limites nao plotados
    assert body["n_pontos"] == 0
    assert body["limites"] is None
    assert body["amostra_insuficiente"] is True
    assert body["pontos_minimos_decisao"] == 10


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dossie_e_carta_cross_tenant_404(cenario_a):
    """Isolamento multi-tenant: tenant B (também perfil A) NÃO vê dossiê/carta de
    padrão do tenant A — RLS esconde o padrão → montar_dossie/carta None → 404.
    Isola o TENANT (não o perfil): B é perfil A pra o gate de perfil não mascarar."""
    client_a = APIClient()
    _autenticar(client_a, cenario_a["admin"], cenario_a["tenant"])
    pid = _criar_padrao(client_a)

    cen_b = _cenario(perfil_a=True)
    client_b = APIClient()
    _autenticar(client_b, cen_b["admin"], cen_b["tenant"])
    assert client_b.get(f"/api/v1/padroes/{pid}/dossie-cgcre/").status_code == 404
    assert client_b.get(f"/api/v1/padroes/{pid}/carta-controle/").status_code == 404


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_carta_controle_nao_perfil_a_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    pid = _criar_padrao(client)
    r = client.get(f"/api/v1/padroes/{pid}/carta-controle/")
    assert r.status_code == 403, r.content


# ---------------------------------------------------------------- PERF-001
@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_disponiveis_baseline_num_queries(cenario, django_assert_max_num_queries):
    """PERF-001 / GATE-PAD-PERF-DISPONIVEIS: congela teto de queries do GET
    /disponiveis/ (N+1 bounded por limite=200). Otimizacao batch fica rastreada;
    este teste pega regressao (blow-up) sobre 3 padroes saudaveis."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    for _ in range(3):
        _criar_padrao(client)
    # Teto generoso (baseline): pega blow-up sem travar por micro-variacao.
    with django_assert_max_num_queries(60):
        r = client.get("/api/v1/padroes/disponiveis/")
    assert r.status_code == 200
    assert len(r.json()["disponiveis"]) == 3


# ---------------------------------------------------------------- BAIXOs P9
def _eventos_bus(tenant_id, acao):
    import json

    from django.db import connection
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    with run_in_tenant_context(tenant_id), connection.cursor() as cur:
        cur.execute(
            "SELECT envelope_jsonb FROM bus_outbox WHERE acao = %s AND tenant_id = %s",
            [acao, str(tenant_id)],
        )
        return [
            json.loads(row[0]) if isinstance(row[0], str) else row[0]
            for row in cur.fetchall()
        ]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_baixar_emite_evento_worm(cenario):
    """BAIXO P9: baixar emite padrao.baixado na cadeia WORM/bus."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    pid = _criar_padrao(client)
    r = _post(
        client,
        f"/api/v1/padroes/{pid}/baixar/",
        {"sucatar": False, "motivo_revogacao": "fim de vida util do padrao"},
    )
    assert r.status_code == 200, r.content
    envelopes = _eventos_bus(cenario["tenant"].id, "padrao.baixado")
    assert len(envelopes) == 1
    assert envelopes[0]["payload"]["id"] == pid


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_idempotency_replay_mesma_chave_nao_duplica(cenario):
    """BAIXO P9: re-POST com a MESMA Idempotency-Key devolve replay (sem duplicar)."""
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    payload = _payload_cadastrar()
    chave = str(uuid4())
    r1 = client.post(
        "/api/v1/padroes/cadastrar/", payload, format="json", HTTP_IDEMPOTENCY_KEY=chave
    )
    assert r1.status_code == 201, r1.content
    pid = r1.json()["id"]
    r2 = client.post(
        "/api/v1/padroes/cadastrar/", payload, format="json", HTTP_IDEMPOTENCY_KEY=chave
    )
    # Replay: mesmo recurso, sem criar um segundo padrao.
    assert r2.status_code in (200, 201)
    assert r2.json()["id"] == pid
