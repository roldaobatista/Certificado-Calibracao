"""T-EQP-037 — Idempotency-Key no POST /equipamentos/{id}/transferir/.

Politica (reusa horizontal F-A `idempotencia`):
- ausente/invalido -> 400
- mesma chave concluida + payload identico -> replay 200 com mesmo
  transferencia_id
- mesma chave com payload divergente -> 422
- mesma chave em_processo -> 425 com Retry-After

Reusa o pattern do T-EQP-003 (etiqueta) e T-EQP-005+007 (criar).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    TransferenciaEquipamentoAceite,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


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


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"trf-idem-{sfx}", nome_fantasia="Lab Idem")
    admin = UsuarioFactory(email=f"adm-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)

    with run_in_tenant_context(tenant.id):
        cedente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cedente Idem PJ",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        cessionario = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="22333444000172",
            nome="Cessionario Idem PJ",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag="TRF-IDEM-001",
            numero_serie="NS-IDEM",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cedente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "admin": admin,
        "cedente": cedente,
        "cessionario": cessionario,
        "eq": eq,
    }


def _payload(cessionario_id, atendente_id, motivo="venda"):
    return {
        "cessionario_cliente_id": str(cessionario_id),
        "motivo_categoria": motivo,
        "aceite_cedente": {
            "tipo": "presencial_atendente",
            "usuario_id_atendente": str(atendente_id),
            "consentimento_historico_expresso": True,
        },
        "aceite_cessionario": {
            "tipo": "contrato_fisico_digitalizado",
            "usuario_id_atendente": str(atendente_id),
            "consentimento_historico_expresso": True,
        },
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_idempotency_ausente_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    # Nao seta HTTP_IDEMPOTENCY_KEY.
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        _payload(cenario["cessionario"].id, cenario["admin"].id),
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_idempotency_invalido_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = "nao-eh-uuid"
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        _payload(cenario["cessionario"].id, cenario["admin"].id),
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_idempotency_replay_mesmo_payload_retorna_mesmo_id(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    chave = str(uuid4())
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = chave
    payload = _payload(cenario["cessionario"].id, cenario["admin"].id)
    resp1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        payload,
        format="json",
    )
    assert resp1.status_code == 200
    transferencia_id_1 = resp1.json()["transferencia_id"]
    # 2a chamada com MESMA chave + mesmo payload -> replay 200.
    resp2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        payload,
        format="json",
    )
    assert resp2.status_code == 200
    assert resp2.json()["transferencia_id"] == transferencia_id_1
    # Garante que apenas 1 transferencia foi criada.
    with run_in_tenant_context(cenario["tenant"].id):
        total = TransferenciaEquipamentoAceite.objects.count()
    assert total == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_idempotency_payload_diferente_422(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    chave = str(uuid4())
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = chave
    client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        _payload(cenario["cessionario"].id, cenario["admin"].id, motivo="venda"),
        format="json",
    )
    # 2a chamada MESMA chave + motivo diferente -> 422.
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/transferir/",
        _payload(cenario["cessionario"].id, cenario["admin"].id, motivo="comodato"),
        format="json",
    )
    assert resp.status_code == 422
