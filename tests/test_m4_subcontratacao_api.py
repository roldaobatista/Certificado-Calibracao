"""API /api/v1/calibracoes/{id}/subcontratar + registrar-recebimento-subcontratado
— testes E2E M4 T-CAL-129 (US-CAL-017 cl. 6.6).

Cobre o pipeline REST end-to-end (CONFIGURADA → AGUARDANDO_SUBCONTRATADO →
RECEBIDA_DO_SUBCONTRATADO) com calibração PG-real:
- subcontratar 200 (estado muda + evento WORM no mesmo atomic);
- subcontratar em estado inválido (APROVADA) → 409;
- subcontratar eh_pais_estrangeiro=True sem DPA → 412 (LGPD art. 33, AC-CAL-017-8);
- registrar-recebimento 200;
- separação de funções: recebedor == executor → 409 (INV-CAL-FRAUDE-RECEB-001 cl. 6.2.5);
- authz: atendente sem permissão → 403;
- idempotência (replay com mesma chave devolve mesmo resultado).
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
_MOTIVO_OK = (
    "subcontratacao por indisponibilidade do padrao interno conforme NC registrada"
)
_SNAPSHOT_CERT = {
    "numero_cert_externo": "EXT-2026-001",
    "data_servico": "2026-06-01",
    "grandeza": "massa",
    "faixa_min": "0",
    "faixa_max": "1000",
    "escopo_subcontratado": "RBC massa 0-1000g",
    "rt_subcontratado": "RT externo CRQ 12345",
}


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
    tenant = TenantFactory(slug=f"subc-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@subc.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@subc.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=atendente, tenant=tenant, perfil="atendente"
    )
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Subc API",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equip = Equipamento.objects.create(
            tenant=tenant,
            tag=f"EQ-{sfx}",
            numero_serie=f"NS-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "admin": admin,
        "atendente": atendente,
        "equip": equip,
    }


def _subcontratar(client, cal_id, *, idem=None, **extra):
    payload = {
        "revision_esperada": 0,
        "subcontratado_id": str(uuid4()),
        "aceite_subcontratacao_id": str(uuid4()),
        "motivo_canonicalizado": _MOTIVO_OK,
        **extra,
    }
    return client.post(
        f"/api/v1/calibracoes/{cal_id}/subcontratar/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idem or str(uuid4()),
    )


def _registrar_recebimento(client, cal_id, *, idem=None, revision=1):
    payload = {
        "revision_esperada": revision,
        "certificado_subcontratado_snapshot_json": _SNAPSHOT_CERT,
    }
    return client.post(
        f"/api/v1/calibracoes/{cal_id}/registrar-recebimento-subcontratado/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idem or str(uuid4()),
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_subcontratar_200_muda_estado():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _subcontratar(client, cal.id)
    assert r.status_code == 200, r.content
    assert r.json()["status"] == EstadoCalibracao.AGUARDANDO_SUBCONTRATADO.value


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_subcontratar_estado_invalido_409():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.APROVADA
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _subcontratar(client, cal.id)
    assert r.status_code == 409, r.content
    assert r.json()["codigo"] == "EstadoInvalido"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_subcontratar_estrangeiro_sem_dpa_412():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _subcontratar(client, cal.id, eh_pais_estrangeiro=True)
    assert r.status_code == 412, r.content
    assert "TransferenciaInternacional" in r.json()["codigo"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_registrar_recebimento_200():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"],
        c["equip"],
        status=EstadoCalibracao.AGUARDANDO_SUBCONTRATADO,
        subcontratado_id=uuid4(),
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _registrar_recebimento(client, cal.id, revision=0)
    assert r.status_code == 200, r.content
    assert r.json()["status"] == EstadoCalibracao.RECEBIDA_DO_SUBCONTRATADO.value


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_registrar_recebimento_separacao_funcoes_409():
    """Recebedor (admin logado) == executor da calibração → 409 (cl. 6.2.5)."""
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"],
        c["equip"],
        status=EstadoCalibracao.AGUARDANDO_SUBCONTRATADO,
        subcontratado_id=uuid4(),
        executor_id=c["admin"].id,
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _registrar_recebimento(client, cal.id, revision=0)
    assert r.status_code == 409, r.content
    assert r.json()["codigo"] == "SeparacaoFuncoesViolada"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_subcontratar_authz_atendente_403():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _subcontratar(client, cal.id)
    assert r.status_code == 403, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_subcontratar_idempotencia_replay():
    c = _cenario()
    cal = criar_calibracao_em_estado(
        c["tenant"], c["equip"], status=EstadoCalibracao.CONFIGURADA
    )
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    idem = str(uuid4())
    # Replay exige payload IDENTICO (mesma chave + mesmo fingerprint). Fixamos
    # subcontratado_id/aceite_subcontratacao_id pra nao divergir entre as chamadas.
    subc_id = str(uuid4())
    aceite_id = str(uuid4())
    r1 = _subcontratar(
        client,
        cal.id,
        idem=idem,
        subcontratado_id=subc_id,
        aceite_subcontratacao_id=aceite_id,
    )
    assert r1.status_code == 200, r1.content
    r2 = _subcontratar(
        client,
        cal.id,
        idem=idem,
        subcontratado_id=subc_id,
        aceite_subcontratacao_id=aceite_id,
    )
    assert r2.status_code == 200, r2.content
    assert r1.json()["id"] == r2.json()["id"]
    assert r1.json()["revision"] == r2.json()["revision"]
