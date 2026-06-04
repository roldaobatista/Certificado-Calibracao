"""Smoke E2E da porta REST do Marco 4 (consolidacao — fecha GATE-CAL-SEG
"10 ViewSets ACTION_MAP" + GATE-CAL-VIEWSETS-WAVE-A).

Trava a regressao do estado "esqueleto Wave A": os ViewSets M4 nao tinham
`get_authz_action`/`ACTION_MAP` e caiam em deny-by-default (`RequireAuthz`
nega tudo). Estes testes provam que a porta esta ABERTA para quem tem a
permissao e FECHADA para quem nao tem.

Padrao do smoke (alto sinal, baixo custo de fixture): a checagem de permissao
do DRF (`has_permission`) roda ANTES do handler. Logo:
  - usuario AUTORIZADO -> passa a authz -> chega no handler -> 200/201 OU erro
    de NEGOCIO (400/404/409/412), NUNCA 403. Asserir `status != 403` prova que
    a acao foi resolvida e o usuario foi permitido.
  - usuario SEM a permissao -> 403 antes de qualquer logica.
Os caminhos felizes de negocio completos ja sao cobertos pelos testes de use
case (test_m4_uc_*). Aqui o foco e a porta (authz wiring).

2 happy-paths reais ancoram a ponta-a-ponta: recepcionar (201) e retrieve (200).
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
    """Tenant + 1 usuario por perfil + Cliente PJ + Equipamento."""
    from src.infrastructure.clientes.models import Cliente, TipoPessoa
    from src.infrastructure.equipamentos.models import Equipamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"m4smoke-{sfx}")
    perfis = {
        "admin": "admin_tenant",
        "atendente": "atendente",
        "metrologista": "metrologista_bancada",
        "signatario": "signatario",
    }
    usuarios = {}
    for chave, perfil in perfis.items():
        u = UsuarioFactory(email=f"{chave}-{sfx}@m4.local")
        UsuarioPerfilTenantFactory(usuario=u, tenant=tenant, perfil=perfil)
        invalidate_user_cache(u.id, tenant.id)
        usuarios[chave] = u
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant, tipo_pessoa=TipoPessoa.PJ, documento="11222333000181",
            nome="Cliente M4 Smoke", aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equip = Equipamento.objects.create(
            tenant=tenant, tag=f"EQ-{sfx}", numero_serie=f"NS-{sfx}",
            fabricante="Toledo", modelo="Prix 4", cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {"tenant": tenant, "u": usuarios, "equip": equip}


def _client(c, perfil_chave) -> APIClient:
    client = APIClient()
    _autenticar(client, c["u"][perfil_chave], c["tenant"])
    return client


# ----------------------------------------------------------------- happy reais


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_recepcionar_happy_201_admin():
    c = _cenario()
    client = _client(c, "admin")
    payload = {
        "origem_recepcao": "AVULSA",
        "instrumento_id": str(c["equip"].id),
        "snapshot_equipamento_json": {"tag": c["equip"].tag},
        "tipo_acreditacao": "NAO_RBC",
        "correlation_id": str(uuid4()),
    }
    r = client.post(
        "/api/v1/calibracoes/recepcionar/", payload, format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert r.status_code == 201, r.content
    assert r.json()["status"] == EstadoCalibracao.RECEPCIONADA.value


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_retrieve_happy_200_admin():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    client = _client(c, "admin")
    r = client.get(f"/api/v1/calibracoes/{cal.id}/")
    assert r.status_code == 200, r.content
    assert r.json()["id"] == str(cal.id)


# ----------------------------------------------------------------- deny: porta fechada
# Cada acao que o `atendente` NAO tem deve dar 403 (deny-by-default + ACTION_MAP).


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_recepcionar_deny_metrologista_403():
    """metrologista NAO tem calibracao.recepcionar -> 403."""
    c = _cenario()
    client = _client(c, "metrologista")
    r = client.post(
        "/api/v1/calibracoes/recepcionar/",
        {
            "origem_recepcao": "AVULSA",
            "instrumento_id": str(c["equip"].id),
            "snapshot_equipamento_json": {"tag": c["equip"].tag},
            "tipo_acreditacao": "NAO_RBC",
            "correlation_id": str(uuid4()),
        },
        format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert r.status_code == 403, r.content


# Matriz de smoke: (descricao, metodo, url_template, perfil_autorizado, perfil_negado)
# url_template usa {cal} (id de uma calibracao real) e {rid} (uuid aleatorio p/
# leitura/reclamacao inexistente — authz roda ANTES do 404, entao prova a porta).
_CASOS = [
    ("configurar", "post", "/api/v1/calibracoes/{cal}/configurar/", "atendente", "signatario"),
    ("cancelar", "post", "/api/v1/calibracoes/{cal}/cancelar/", "admin", "atendente"),
    ("registrar_leitura", "post", "/api/v1/calibracoes/{cal}/registrar-leitura/", "metrologista", "atendente"),
    ("corrigir_leitura", "post", "/api/v1/leituras/{rid}/corrigir/", "metrologista", "atendente"),
    ("aprovar_revisao", "post", "/api/v1/calibracoes/{cal}/aprovar-revisao/", "signatario", "atendente"),
    ("rejeitar_revisao", "post", "/api/v1/calibracoes/{cal}/rejeitar-revisao/", "signatario", "atendente"),
    ("aprovar_2a", "post", "/api/v1/calibracoes/{cal}/aprovar-2a-conferencia/", "signatario", "atendente"),
    ("nc_abrir", "post", "/api/v1/nao-conformidades/abrir/", "metrologista", "atendente"),
    ("nc_fechar", "post", "/api/v1/nao-conformidades/{rid}/fechar/", "admin", "atendente"),
    ("reclamacao_abrir", "post", "/api/v1/reclamacoes/abrir/", "atendente", "metrologista"),
    ("reclamacao_atribuir", "post", "/api/v1/reclamacoes/{rid}/atribuir-rt/", "admin", "atendente"),
    ("reclamacao_responder", "post", "/api/v1/reclamacoes/{rid}/responder/", "signatario", "atendente"),
]


@pytest.mark.parametrize("nome,metodo,url,perfil_ok,perfil_nao", _CASOS)
@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_porta_authz_resolve(nome, metodo, url, perfil_ok, perfil_nao):
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    url_final = url.format(cal=cal.id, rid=uuid4())
    extra = {"HTTP_IDEMPOTENCY_KEY": str(uuid4())}

    # AUTORIZADO: passa a authz -> handler -> nunca 403 (200/201/400/404/409/412).
    cli_ok = _client(c, perfil_ok)
    r_ok = getattr(cli_ok, metodo)(url_final, {}, format="json", **extra)
    assert r_ok.status_code != 403, (
        f"{nome}: {perfil_ok} deveria PASSAR a authz, recebeu 403 "
        f"(ACTION_MAP nao resolveu a acao?) -> {r_ok.content!r}"
    )

    # SEM PERMISSAO: 403 antes de qualquer logica.
    cli_nao = _client(c, perfil_nao)
    r_nao = getattr(cli_nao, metodo)(url_final, {}, format="json", **extra)
    assert r_nao.status_code == 403, (
        f"{nome}: {perfil_nao} NAO deveria ter a permissao, recebeu "
        f"{r_nao.status_code} -> {r_nao.content!r}"
    )
