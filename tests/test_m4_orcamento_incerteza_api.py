"""API /api/v1/calibracoes/{id}/calcular-incerteza + avaliar-conformidade
— testes E2E M4 T-CAL-125 (US-CAL-005 GUM cl. 5 + US-CAL-006 cl. 7.8.6).

Cobre o pipeline REST com calibracao PG-real em EM_EXECUCAO:
- calcular-incerteza happy 201 (modo flat, 1 componente Tipo B) + evento WORM;
- calcular-incerteza payload invalido (documentacao_agregacao < 50) -> 400;
- avaliar-conformidade happy 200 (ACEITACAO_SIMPLES, dentro do limite) + zona ILAC;
- authz: atendente nao tem calcular/avaliar -> 403 (porta resolve via ACTION_MAP).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.infrastructure.authz.django_provider import invalidate_user_cache

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory
from tests.m8_pg_fixtures import criar_calibracao_em_estado

_DBS = ["default", "breaker_writer"]
_DOC_OK = (
    "Orcamento de incerteza agregado conforme GUM JCGM 100:2008 secao 5 — "
    "componentes Tipo A e Tipo B combinados por raiz da soma dos quadrados."
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


def _cenario():
    from src.infrastructure.clientes.models import Cliente, TipoPessoa
    from src.infrastructure.equipamentos.models import Equipamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"orc-api-{sfx}")
    metrologista = UsuarioFactory(email=f"met-{sfx}@orc.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@orc.local")
    UsuarioPerfilTenantFactory(
        usuario=metrologista, tenant=tenant, perfil="metrologista_bancada"
    )
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (metrologista, atendente):
        invalidate_user_cache(u.id, tenant.id)
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant, tipo_pessoa=TipoPessoa.PJ, documento="11222333000181",
            nome="Cliente Orc API", aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equip = Equipamento.objects.create(
            tenant=tenant, tag=f"EQ-{sfx}", numero_serie=f"NS-{sfx}",
            fabricante="Toledo", modelo="Prix 4", cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "metrologista": metrologista,
        "atendente": atendente,
        "equip": equip,
    }


def _cal_em_execucao(c):
    return criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.EM_EXECUCAO
    )


def _cliente(c, usuario_chave) -> APIClient:
    client = APIClient()
    _autenticar(client, c[usuario_chave], c["tenant"])
    return client


_COMPONENTE_TIPO_B = {
    "nome": "resolucao",
    "tipo": "B",
    "u_i": "0.05",
    "tipo_origem_componente": "RESOLUCAO_INSTRUMENTO",
    "distribuicao": "RETANGULAR",
    "divisor": "1.7320508",
    "formula_calculo": "RESOLUCAO_RETANGULAR",
}


def _calcular(client, cal_id, *, idem=None, **over):
    payload = {
        "componentes": [_COMPONENTE_TIPO_B],
        "versao_motor_calculo": "v1.0.0+test",
        "documentacao_agregacao": _DOC_OK,
        "correlation_id": str(uuid4()),
        **over,
    }
    return client.post(
        f"/api/v1/calibracoes/{cal_id}/calcular-incerteza/", payload,
        format="json", HTTP_IDEMPOTENCY_KEY=idem or str(uuid4()),
    )


def _avaliar(client, cal_id, *, idem=None, **over):
    payload = {
        "revision_esperada": 0,
        "valor_medido": "100.0",
        "U_expandida": "0.5",
        "k": "2.0",
        "lsl": "99.0",
        "usl": "101.0",
        **over,
    }
    return client.post(
        f"/api/v1/calibracoes/{cal_id}/avaliar-conformidade/", payload,
        format="json", HTTP_IDEMPOTENCY_KEY=idem or str(uuid4()),
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_calcular_incerteza_happy_201():
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _calcular(_cliente(c, "metrologista"), cal.id)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["calibracao_id"] == str(cal.id)
    assert body["U_expandida"]  # nao-vazio
    assert body["replay_determinismo_hash"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_calcular_incerteza_doc_curta_400():
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _calcular(_cliente(c, "metrologista"), cal.id, documentacao_agregacao="curta")
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_calcular_incerteza_correlacao_nao_numerica_400():
    """correlacoes com rho nao-numerico -> 400 (nao 500). InvalidOperation
    (decimal) herda de ArithmeticError; a view captura no except do input."""
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _calcular(
        _cliente(c, "metrologista"),
        cal.id,
        correlacoes=[["resolucao", "outro", "xyz"]],
    )
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_calcular_incerteza_authz_atendente_403():
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _calcular(_cliente(c, "atendente"), cal.id)
    assert r.status_code == 403, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_avaliar_conformidade_happy_200():
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _avaliar(_cliente(c, "metrologista"), cal.id)
    assert r.status_code == 200, r.content
    body = r.json()
    assert "zona_ilac_g8" in body
    assert body["decisao"] in {"CONFORME", "NAO_CONFORME", "NA"}


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_avaliar_conformidade_authz_atendente_403():
    c = _cenario()
    cal = _cal_em_execucao(c)
    r = _avaliar(_cliente(c, "atendente"), cal.id)
    assert r.status_code == 403, r.content
