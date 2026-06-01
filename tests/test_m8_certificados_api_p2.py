"""API /api/v1/certificados/ — testes E2E M8 Fatia 2b (T-CER-049).

Cobre o pipeline REST end-to-end (calibração APROVADA real → adapters de leitura →
reconciliação → numeração → snapshot WORM → evento → retrieve):
- emitir RBC perfil A (com escopo CMC confirmado; U>=CMC → RBC_OK) — fecha
  GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC end-to-end;
- perfil A SEM escopo: ponto não-RBC sem decisão RT → 422 (fail-closed, nada persistido);
- perfil A com decisão RT EMITIR_NAO_RBC → 201 NÃO-RBC com ressalva;
- não-RBC perfil B (sem cmc injetado);
- read-path retrieve devolve cmc_no_ponto/classificação DO SNAPSHOT;
- idempotência (replay com mesma chave); authz (atendente 403); reemissão versionada.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory
from tests.m8_pg_fixtures import (
    criar_calibracao_aprovada,
    criar_escopo_cmc_confirmado,
    criar_leituras,
    criar_orcamento_incerteza,
    criar_ponto_orcamento,
)

_DBS = ["default", "breaker_writer"]
_MOTIVO_OK = "correcao de metadado a pedido formal do cliente conforme NC registrada 2026"


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


def _cenario(*, perfil_a: bool = True):
    from src.infrastructure.clientes.models import Cliente, TipoPessoa
    from src.infrastructure.equipamentos.models import Equipamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    sfx = uuid4().hex[:8]
    kwargs = {"slug": f"cert-api-{sfx}"}
    kwargs["perfil_a" if perfil_a else "perfil_b"] = True
    tenant = TenantFactory(**kwargs)
    admin = UsuarioFactory(email=f"adm-{sfx}@cert.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@cert.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant, tipo_pessoa=TipoPessoa.PJ, documento="11222333000181",
            nome="Cliente Cert API", aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equip = Equipamento.objects.create(
            tenant=tenant, tag=f"EQ-{sfx}", numero_serie=f"NS-{sfx}", fabricante="Toledo",
            modelo="Prix 4", cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "A" if perfil_a else "B"},
        )
    return {"tenant": tenant, "admin": admin, "atendente": atendente, "equip": equip}


def _calibracao_com_ponto(tenant, equip, *, U="0.8"):
    """Calibração APROVADA + 1 ponto (100g) com 2 leituras + orçamento (U)."""
    cal = criar_calibracao_aprovada(tenant, equip)
    criar_leituras(tenant, cal, ponto="100", valores=["100.0", "100.2"])
    orc = criar_orcamento_incerteza(tenant, cal)
    criar_ponto_orcamento(tenant, orc, ponto="100", U=U)
    return cal


def _emitir(client, calibracao_id, idem=None, corr=None, **extra):
    payload = {
        "calibracao_id": str(calibracao_id),
        "correlation_id": corr or str(uuid4()),
        **extra,
    }
    return client.post(
        "/api/v1/certificados/emitir/", payload, format="json",
        HTTP_IDEMPOTENCY_KEY=idem or str(uuid4()),
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_rbc_perfil_a_e_retrieve_le_snapshot():
    c = _cenario(perfil_a=True)
    criar_escopo_cmc_confirmado(c["tenant"], cmc_valor=Decimal("0.5"))  # CMC 0.5 <= U 0.8
    cal = _calibracao_com_ponto(c["tenant"], c["equip"], U="0.8")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _emitir(client, cal.id)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["tipo_acreditacao"] == "RBC"
    assert body["pontos"][0]["classificacao"] == "RBC_OK"
    assert Decimal(body["pontos"][0]["cmc_no_ponto"]) == Decimal("0.5")
    # read-path: retrieve devolve o cmc_no_ponto DO SNAPSHOT (não reconsulta)
    g = client.get(f"/api/v1/certificados/{body['id']}/")
    assert g.status_code == 200
    assert Decimal(g.json()["pontos"][0]["cmc_no_ponto"]) == Decimal("0.5")
    assert g.json()["tipo_acreditacao"] == "RBC"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_perfil_a_sem_escopo_sem_decisao_422():
    c = _cenario(perfil_a=True)
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])  # sem escopo → SEM_CMC
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _emitir(client, cal.id)
    assert r.status_code == 422, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_perfil_a_com_decisao_nao_rbc():
    c = _cenario(perfil_a=True)
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    dec = client.post(
        "/api/v1/certificados/decidir-ponto/",
        {
            "calibracao_id": str(cal.id), "ponto_calibracao": "100",
            "classificacao": "SEM_CMC", "decisao_rt": "EMITIR_NAO_RBC_NO_PONTO",
            "categoria_motivo": "OUTRO",
            "justificativa": "ponto reportado sem selo RBC fora do escopo acreditado",
            "ressalva_nao_rbc": "ponto nao coberto pela acreditacao RBC vigente",
            "correlation_id": str(uuid4()),
        },
        format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert dec.status_code == 201, dec.content
    r = _emitir(client, cal.id)
    assert r.status_code == 201, r.content
    assert r.json()["tipo_acreditacao"] == "NAO_RBC"
    assert r.json()["pontos"][0]["ressalva_nao_rbc"].startswith("ponto nao coberto")


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_nao_rbc_perfil_b():
    c = _cenario(perfil_a=False)  # perfil B — cmc não é injetado
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _emitir(client, cal.id)
    assert r.status_code == 201, r.content
    assert r.json()["tipo_acreditacao"] == "NAO_RBC"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_idempotencia_replay():
    c = _cenario(perfil_a=False)
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    idem, corr = str(uuid4()), str(uuid4())
    r1 = _emitir(client, cal.id, idem=idem, corr=corr)
    assert r1.status_code == 201, r1.content
    r2 = _emitir(client, cal.id, idem=idem, corr=corr)  # replay — mesma chave+payload
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_emite_403():
    c = _cenario(perfil_a=False)
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _emitir(client, cal.id)
    assert r.status_code == 403


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_emitir_calibracao_inexistente_404():
    c = _cenario(perfil_a=False)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _emitir(client, uuid4())
    assert r.status_code == 404


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reemitir_v2_substitui_v1():
    c = _cenario(perfil_a=False)
    cal = _calibracao_com_ponto(c["tenant"], c["equip"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    v1 = _emitir(client, cal.id)
    assert v1.status_code == 201, v1.content
    v1_id = v1.json()["id"]
    rr = client.post(
        f"/api/v1/certificados/{v1_id}/reemitir/",
        {"motivo": _MOTIVO_OK, "correlation_id": str(uuid4())},
        format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert rr.status_code == 201, rr.content
    assert rr.json()["versao"] == 2
    assert rr.json()["versao_anterior_id"] == v1_id
    # v1 preservada (WORM) e marcada substituida
    g = client.get(f"/api/v1/certificados/{v1_id}/")
    assert g.json()["status"] == "substituida"
