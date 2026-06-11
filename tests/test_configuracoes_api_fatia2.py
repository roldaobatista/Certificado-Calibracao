"""API /api/v1/configuracoes/ — testes E2E Fatia 2 (T-CFG-030..034).

Cobre: atualizar empresa (upsert 201/200 + retrieve) + authz (atendente 403) +
filial (sem empresa 422; 2ª matriz 422 INV-037) + imposto (cadastrar 201;
sobreposto 422; encerrar vigência one-shot 200→409) + série (regime DERIVADO do
tipo ADR-0080 — payload não tem o campo; duplicada 409; reset anual TL-07 via
`{ano}` no formato) + reservar-numero (buracos-aceitos consome 1,2; gap-less
reserva densa; Idempotency-Key obrigatória + replay) + cross-tenant 404.
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

CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"


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


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"cfg-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@cfg.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@cfg.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _client_admin(c) -> APIClient:
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    return client


def _post(client, url, payload, key=None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


def _payload_empresa(**kw):
    base = {
        "razao_social": "Balanças Solution LTDA",
        "cnpj": CNPJ_A,
        "regime_tributario": "simples_nacional",
    }
    base.update(kw)
    return base


def _payload_imposto(**kw):
    base = {
        "tipo": "iss",
        "aliquota": "5.0000",
        "vigencia_inicio": "2026-01-01T00:00:00Z",
    }
    base.update(kw)
    return base


# === empresa (US-CFG-001) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atualizar_empresa_upsert_e_retrieve():
    client = _client_admin(_cenario())
    r1 = _post(client, "/api/v1/configuracoes/empresa/atualizar/", _payload_empresa())
    assert r1.status_code == 201, r1.content
    r2 = _post(
        client,
        "/api/v1/configuracoes/empresa/atualizar/",
        _payload_empresa(razao_social="Balanças Solution Calibrações LTDA"),
    )
    assert r2.status_code == 200, r2.content
    assert r2.json()["id"] == r1.json()["id"]  # upsert preserva id
    g = client.get("/api/v1/configuracoes/empresa/atual/")
    assert g.status_code == 200
    assert g.json()["razao_social"] == "Balanças Solution Calibrações LTDA"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cnpj_invalido_400():
    client = _client_admin(_cenario())
    r = _post(
        client,
        "/api/v1/configuracoes/empresa/atualizar/",
        _payload_empresa(cnpj="11111111111111"),  # sequência trivial — VO rejeita
    )
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_atualiza_403():
    c = _cenario()
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/configuracoes/empresa/atualizar/", _payload_empresa())
    assert r.status_code == 403


# === filial (INV-037) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_filial_sem_empresa_422():
    client = _client_admin(_cenario())
    r = _post(
        client,
        "/api/v1/configuracoes/empresa/adicionar-filial/",
        {"cnpj": CNPJ_B, "nome": "Filial Cuiabá", "eh_matriz": True},
    )
    assert r.status_code == 422, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_segunda_matriz_422():
    client = _client_admin(_cenario())
    assert (
        _post(client, "/api/v1/configuracoes/empresa/atualizar/", _payload_empresa()).status_code
        == 201
    )
    r1 = _post(
        client,
        "/api/v1/configuracoes/empresa/adicionar-filial/",
        {"cnpj": CNPJ_A, "nome": "Matriz Cuiabá", "eh_matriz": True},
    )
    assert r1.status_code == 201, r1.content
    r2 = _post(
        client,
        "/api/v1/configuracoes/empresa/adicionar-filial/",
        {"cnpj": CNPJ_B, "nome": "Outra Matriz", "eh_matriz": True},
    )
    assert r2.status_code == 422, r2.content
    g = client.get("/api/v1/configuracoes/empresa/filiais/")
    assert g.status_code == 200
    assert len(g.json()["filiais"]) == 1


# === editar filial (conserto M6 da auditoria P9) ===

CNPJ_C = "34238864000168"  # DV válido — 3ª filial dos cenários de edição


def _cenario_duas_filiais(client):
    """Empresa + matriz (CNPJ_A) + filial comum (CNPJ_B). Retorna (matriz, comum)."""
    assert (
        _post(client, "/api/v1/configuracoes/empresa/atualizar/", _payload_empresa()).status_code
        == 201
    )
    m = _post(
        client,
        "/api/v1/configuracoes/empresa/adicionar-filial/",
        {"cnpj": CNPJ_A, "nome": "Matriz Cuiabá", "eh_matriz": True},
    )
    assert m.status_code == 201, m.content
    f = _post(
        client,
        "/api/v1/configuracoes/empresa/adicionar-filial/",
        {"cnpj": CNPJ_B, "nome": "Filial Rondonópolis", "eh_matriz": False},
    )
    assert f.status_code == 201, f.content
    return m.json(), f.json()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_filial_nome_200():
    client = _client_admin(_cenario())
    _, comum = _cenario_duas_filiais(client)
    r = _post(
        client,
        f"/api/v1/configuracoes/empresa/filiais/{comum['id']}/editar/",
        {"cnpj": CNPJ_B, "nome": "Filial Rondonópolis Renomeada", "eh_matriz": False},
    )
    assert r.status_code == 200, r.content
    g = client.get("/api/v1/configuracoes/empresa/filiais/")
    nomes = {f["id"]: f["nome"] for f in g.json()["filiais"]}
    assert nomes[comum["id"]] == "Filial Rondonópolis Renomeada"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_filial_troca_atomica_de_matriz():
    client = _client_admin(_cenario())
    matriz, comum = _cenario_duas_filiais(client)
    # Marcar a comum como matriz desmarca a anterior na MESMA transação.
    r = _post(
        client,
        f"/api/v1/configuracoes/empresa/filiais/{comum['id']}/editar/",
        {"cnpj": CNPJ_B, "nome": "Filial Rondonópolis", "eh_matriz": True},
    )
    assert r.status_code == 200, r.content
    g = client.get("/api/v1/configuracoes/empresa/filiais/")
    matrizes = [f for f in g.json()["filiais"] if f["eh_matriz"]]
    assert len(matrizes) == 1  # INV-037 — exatamente 1 matriz no resultante
    assert matrizes[0]["id"] == comum["id"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_filial_desmarcar_unica_matriz_422():
    client = _client_admin(_cenario())
    matriz, _ = _cenario_duas_filiais(client)
    r = _post(
        client,
        f"/api/v1/configuracoes/empresa/filiais/{matriz['id']}/editar/",
        {"cnpj": CNPJ_A, "nome": "Matriz Cuiabá", "eh_matriz": False},
    )
    assert r.status_code == 422, r.content  # tenant nunca fica sem matriz


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_filial_inexistente_404():
    client = _client_admin(_cenario())
    _cenario_duas_filiais(client)
    r = _post(
        client,
        f"/api/v1/configuracoes/empresa/filiais/{uuid4()}/editar/",
        {"cnpj": CNPJ_C, "nome": "Fantasma", "eh_matriz": False},
    )
    assert r.status_code == 404, r.content


# === imposto (US-CFG-003) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_imposto_e_sobreposicao_422():
    client = _client_admin(_cenario())
    r1 = _post(client, "/api/v1/configuracoes/impostos/cadastrar/", _payload_imposto())
    assert r1.status_code == 201, r1.content
    # Mesma (tipo, filial NULL) com vigência aberta sobreposta → 422.
    r2 = _post(
        client,
        "/api/v1/configuracoes/impostos/cadastrar/",
        _payload_imposto(aliquota="7.0000", vigencia_inicio="2026-06-01T00:00:00Z"),
    )
    assert r2.status_code == 422, r2.content
    lista = client.get("/api/v1/configuracoes/impostos/")
    assert lista.status_code == 200
    assert len(lista.json()["impostos"]) == 1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_encerrar_vigencia_one_shot_200_depois_409():
    client = _client_admin(_cenario())
    r1 = _post(client, "/api/v1/configuracoes/impostos/cadastrar/", _payload_imposto())
    imposto_id = r1.json()["id"]
    r2 = _post(
        client,
        f"/api/v1/configuracoes/impostos/{imposto_id}/encerrar-vigencia/",
        {"fim": "2026-06-01T00:00:00Z"},
    )
    assert r2.status_code == 200, r2.content
    assert r2.json()["vigencia_fim"] is not None
    r3 = _post(
        client,
        f"/api/v1/configuracoes/impostos/{imposto_id}/encerrar-vigencia/",
        {"fim": "2026-07-01T00:00:00Z"},
    )
    assert r3.status_code == 409, r3.content
    # Alíquota nova passa a valer só pra documentos futuros (AC-CFG-003-2):
    # nova linha encadeada na sequência da vigência encerrada é aceita.
    r4 = _post(
        client,
        "/api/v1/configuracoes/impostos/cadastrar/",
        _payload_imposto(aliquota="7.0000", vigencia_inicio="2026-06-01T00:00:00Z"),
    )
    assert r4.status_code == 201, r4.content


# === série (US-CFG-002 / ADR-0080) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_serie_regime_derivado_do_tipo():
    client = _client_admin(_cenario())
    r_os = _post(
        client,
        "/api/v1/configuracoes/series/criar/",
        {"tipo": "os", "prefixo": "OS", "regime_numeracao": "gap_less"},  # campo IGNORADO
    )
    assert r_os.status_code == 201, r_os.content
    assert r_os.json()["regime_numeracao"] == "buracos_aceitos"  # derivado, não payload
    r_fat = _post(
        client,
        "/api/v1/configuracoes/series/criar/",
        {"tipo": "fatura", "prefixo": "FAT"},
    )
    assert r_fat.status_code == 201
    assert r_fat.json()["regime_numeracao"] == "gap_less"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_serie_duplicada_409_e_replay_idempotente():
    client = _client_admin(_cenario())
    key = str(uuid4())
    payload = {"tipo": "recibo", "prefixo": "REC"}
    r1 = _post(client, "/api/v1/configuracoes/series/criar/", payload, key=key)
    assert r1.status_code == 201, r1.content
    # Replay da MESMA chave devolve a mesma resposta (IDEMP-001).
    r2 = _post(client, "/api/v1/configuracoes/series/criar/", payload, key=key)
    assert r2.status_code == 201
    assert r2.json()["id"] == r1.json()["id"]
    # Chave nova + mesma série → 409 (TL-06).
    r3 = _post(client, "/api/v1/configuracoes/series/criar/", payload)
    assert r3.status_code == 409, r3.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reservar_numero_buracos_aceitos_e_formatado():
    client = _client_admin(_cenario())
    serie = _post(
        client, "/api/v1/configuracoes/series/criar/", {"tipo": "os", "prefixo": "OS"}
    ).json()
    url = f"/api/v1/configuracoes/series/{serie['id']}/reservar-numero/"
    r1 = _post(client, url, {})
    assert r1.status_code == 201, r1.content
    assert r1.json()["sequencial"] == 1
    assert r1.json()["numero_formatado"] == "OS-000001"
    r2 = _post(client, url, {})
    assert r2.json()["sequencial"] == 2


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reservar_numero_gap_less_denso():
    client = _client_admin(_cenario())
    serie = _post(
        client, "/api/v1/configuracoes/series/criar/", {"tipo": "fatura", "prefixo": "FAT"}
    ).json()
    url = f"/api/v1/configuracoes/series/{serie['id']}/reservar-numero/"
    r1 = _post(client, url, {})
    assert r1.status_code == 201, r1.content
    assert r1.json()["sequencial"] == 1
    assert r1.json()["regime_numeracao"] == "gap_less"
    r2 = _post(client, url, {})
    assert r2.json()["sequencial"] == 2


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reset_anual_derivado_do_formato_ano():
    client = _client_admin(_cenario())
    serie = _post(
        client,
        "/api/v1/configuracoes/series/criar/",
        {"tipo": "orcamento", "prefixo": "ORC", "formato": "{prefixo}-{ano}-{seq}"},
    ).json()
    assert serie["reset_anual"] is True  # TL-07 — derivado do {ano}
    url = f"/api/v1/configuracoes/series/{serie['id']}/reservar-numero/"
    r = _post(client, url, {})
    assert r.status_code == 201, r.content
    assert r.json()["ano"] is not None
    assert f"-{r.json()['ano']}-" in r.json()["numero_formatado"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reservar_sem_idempotency_key_falha():
    client = _client_admin(_cenario())
    serie = _post(
        client, "/api/v1/configuracoes/series/criar/", {"tipo": "os", "prefixo": "OS"}
    ).json()
    r = client.post(
        f"/api/v1/configuracoes/series/{serie['id']}/reservar-numero/", {}, format="json"
    )
    assert r.status_code in (400, 422, 428), r.content


# === cross-tenant (INV-TENANT-001) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_serie_cross_tenant_404():
    c1 = _cenario()
    client1 = _client_admin(c1)
    serie = _post(
        client1, "/api/v1/configuracoes/series/criar/", {"tipo": "os", "prefixo": "OS"}
    ).json()
    c2 = _cenario()
    client2 = _client_admin(c2)
    r = client2.get(f"/api/v1/configuracoes/series/{serie['id']}/")
    assert r.status_code == 404
