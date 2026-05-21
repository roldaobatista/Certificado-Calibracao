"""T-CLI-108 — payload canônico de Cliente.Bloqueado.

AC-CLI-004-9: payload do evento carrega `agendamentos_futuros: List[UUID]`
pro consumer Wave A `operacao/agenda` (GATE-CLI-7). Marco 1: slot acordado,
lista vazia (módulo agenda ainda não existe).
AC-CLI-004-7: emissão via `publicar_evento(outbox=True)` — sai pelo outbox
transacional, NÃO `registrar_auditoria` direto (débito técnico fechado).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.bloqueio import (
    MOTIVO_MANUAL_INADIMPLENCIA,
    consultar_agendamentos_futuros_do_cliente,
    montar_payload_cliente_bloqueado,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

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


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"payload-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@payload.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _criar_cliente(tenant, usuario) -> Cliente:
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Payload Teste",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )


# =============================================================
# Testes puros do helper de payload
# =============================================================
def test_payload_inclui_slot_agendamentos_futuros_vazio_em_marco_1():
    """Em Marco 1 a lista é vazia (operacao/agenda ainda não existe)."""
    cliente_id = uuid4()
    tenant_id = uuid4()
    bloqueio_id = uuid4()

    payload = montar_payload_cliente_bloqueado(
        cliente_id=cliente_id,
        tenant_id=tenant_id,
        bloqueio_id=bloqueio_id,
        motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
        justificativa_hash="v1:" + "a" * 64,
        causation_type=None,
        causation_id=None,
        usuario_id=None,
    )

    assert "agendamentos_futuros" in payload
    assert payload["agendamentos_futuros"] == []
    assert payload["cliente_id"] == str(cliente_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["bloqueio_id"] == str(bloqueio_id)


def test_payload_extras_preservados():
    payload = montar_payload_cliente_bloqueado(
        cliente_id=uuid4(),
        tenant_id=uuid4(),
        bloqueio_id=uuid4(),
        motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
        justificativa_hash="v1:" + "b" * 64,
        causation_type=None,
        causation_id=None,
        usuario_id=None,
        extras={"dias_vencido": 95, "automatico": True},
    )
    assert payload["dias_vencido"] == 95
    assert payload["automatico"] is True
    # Slot canônico preservado mesmo com extras
    assert payload["agendamentos_futuros"] == []


def test_consultar_agendamentos_futuros_marco_1_retorna_vazio():
    """Contrato em Marco 1 — quando módulo operacao/agenda chegar em Wave A,
    plugar consulta real aqui."""
    agendamentos = consultar_agendamentos_futuros_do_cliente(uuid4(), uuid4())
    assert agendamentos == []


def test_payload_serializa_uuids_como_str():
    cid = uuid4()
    tid = uuid4()
    bid = uuid4()
    causid = uuid4()
    uid = uuid4()
    payload = montar_payload_cliente_bloqueado(
        cliente_id=cid,
        tenant_id=tid,
        bloqueio_id=bid,
        motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
        justificativa_hash="v1:" + "c" * 64,
        causation_type="manual_decisao_admin",
        causation_id=causid,
        usuario_id=uid,
    )
    assert payload["cliente_id"] == str(cid)
    assert payload["tenant_id"] == str(tid)
    assert payload["bloqueio_id"] == str(bid)
    assert payload["causation_id"] == str(causid)
    assert payload["usuario_id"] == str(uid)
    # event_id é UUID válido
    UUID(payload["event_id"])  # raises se inválido


# =============================================================
# Teste end-to-end via endpoint /bloquear/ — payload chega ao bus_outbox
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_bloquear_publica_payload_com_agendamentos_futuros(cenario):
    """E2E — POST /bloquear/ usa publicar_evento(outbox=True);
    payload na cadeia (Auditoria) carrega `agendamentos_futuros`."""
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data={
            "motivo_categoria": MOTIVO_MANUAL_INADIMPLENCIA,
            "justificativa": "Cliente nao pagou 3 faturas e ignorou contatos repetidos",
            "confirmacao_comunicacao_previa": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.content

    with run_in_tenant_context(cenario["tenant"].id):
        audit = Auditoria.objects.filter(
            action="cliente.bloqueado", resource_summary=str(cliente.id)
        ).first()
    assert audit is not None
    payload = audit.payload_jsonb
    assert "agendamentos_futuros" in payload
    assert payload["agendamentos_futuros"] == []
    assert payload["motivo_categoria"] == MOTIVO_MANUAL_INADIMPLENCIA


@pytest.mark.django_db(transaction=True)
def test_bloquear_enfileira_no_bus_outbox(cenario):
    """T-CLI-107/108 — emissão entra no bus_outbox transacional (AC-CLI-004-7)."""
    from django.db import connection

    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    response = client.post(
        f"/api/v1/clientes/{cliente.id}/bloquear/",
        data={
            "motivo_categoria": MOTIVO_MANUAL_INADIMPLENCIA,
            "justificativa": "Cliente nao pagou 3 faturas e ignorou contatos repetidos",
            "confirmacao_comunicacao_previa": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.content

    import json as _json

    with run_in_tenant_context(cenario["tenant"].id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox "
                "WHERE acao = 'cliente.bloqueado' "
                "  AND tenant_id = %s",
                [cenario["tenant"].id],
            )
            row = cur.fetchone()
    assert row is not None, "Evento cliente.bloqueado não foi enfileirado no outbox"
    raw = row[0]
    envelope = raw if isinstance(raw, dict) else _json.loads(raw)
    assert envelope["acao"] == "cliente.bloqueado"
    assert "agendamentos_futuros" in envelope["payload"]
    assert envelope["payload"]["agendamentos_futuros"] == []
