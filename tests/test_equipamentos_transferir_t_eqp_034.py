"""T-EQP-034+035+036+040 — endpoint POST /equipamentos/{id}/transferir/.

Cobre:
- AC-EQP-004-1: 3 vias aceite + cria TransferenciaEquipamentoAceite +
  efetiva quando ambos aceites validos.
- AC-EQP-004-2 (INV-050): cessionario outro tenant -> 422 generico
  (sem oracle cross-tenant).
- AC-EQP-004-3 (INV-INT-010): cedente/cessionario bloqueado -> 412.
- AC-EQP-004-7: evento `equipamento.transferido` payload sanitizado.
- INV-AUTHZ-001: perfil sem `equipamentos.transferir` -> 403.
- Cessionario igual ao cedente -> 400.
- motivo='outro' sem detalhe -> 400.
- Aceite parcial -> 201 PENDENTE (sem efetivar).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import (
    Cliente,
    ClienteBloqueio,
    TipoPessoa,
)
from src.infrastructure.equipamentos.models import (
    Equipamento,
    StatusTransferencia,
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
    # T-EQP-037: Idempotency-Key default — cada client tem uma chave
    # nova por teste (pytest cria APIClient novo por @django_db).
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"trf-a-{sfx}", nome_fantasia="Lab A")
    tenant_b = TenantFactory(slug=f"trf-b-{sfx}", nome_fantasia="Lab B")
    admin_a = UsuarioFactory(email=f"adm-a-{sfx}@e.local")
    admin_b = UsuarioFactory(email=f"adm-b-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-a-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=leitor_a, tenant=tenant_a, perfil="cliente_externo_leitura"
    )
    for u, t in [(admin_a, tenant_a), (admin_b, tenant_b), (leitor_a, tenant_a)]:
        invalidate_user_cache(u.id, t.id)

    with run_in_tenant_context(tenant_a.id):
        cedente = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cedente PJ",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        cessionario = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="22333444000172",
            nome="Cessionario PJ",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_a = Equipamento.objects.create(
            tenant=tenant_a,
            tag="TRF-A-001",
            numero_serie="NS-TRF-A",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cedente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    with run_in_tenant_context(tenant_b.id):
        cliente_b = Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento="33444555000163",
            nome="Cliente do Outro Tenant",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "leitor_a": leitor_a,
        "cedente": cedente,
        "cessionario": cessionario,
        "cliente_b": cliente_b,
        "eq_a": eq_a,
    }


def _idem_header():
    """Header padrao Idempotency-Key UUID (T-EQP-037)."""
    return {"HTTP_IDEMPOTENCY_KEY": str(uuid4())}


def _payload_completo(cessionario_id, atendente_id, motivo="venda"):
    return {
        "cessionario_cliente_id": str(cessionario_id),
        "motivo_categoria": motivo,
        "aceite_cedente": {
            "tipo": "presencial_atendente",
            "usuario_id_atendente": str(atendente_id),
            "observacao": "Atendente confirma ciencia do termo.",
            "consentimento_historico_expresso": True,
        },
        "aceite_cessionario": {
            "tipo": "contrato_fisico_digitalizado",
            "usuario_id_atendente": str(atendente_id),
            "observacao": "Contrato escaneado anexo.",
            "consentimento_historico_expresso": True,
        },
    }


# ----------------------------------------------------------------------
# Happy
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_transferencia_completa_efetiva_e_publica_evento(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["status"] == "efetivada"
    assert body["foi_efetivada"] is True
    with run_in_tenant_context(cenario["tenant_a"].id):
        cenario["eq_a"].refresh_from_db()
        assert cenario["eq_a"].cliente_atual_id == cenario["cessionario"].id
        eventos = list(Auditoria.objects.filter(action="equipamento.transferido"))
    assert len(eventos) == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_aceite_parcial_fica_pendente_sem_efetivar(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    payload = _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id)
    payload["aceite_cessionario"] = {}  # so cedente
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        payload,
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["status"] == "pendente"
    assert body["foi_efetivada"] is False
    with run_in_tenant_context(cenario["tenant_a"].id):
        cenario["eq_a"].refresh_from_db()
        # NAO atualizou cliente_atual_id ainda.
        assert cenario["eq_a"].cliente_atual_id == cenario["cedente"].id


# ----------------------------------------------------------------------
# INV-050 cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_050_cessionario_outro_tenant_422_sem_oracle(cenario):
    """admin do tenant_a tenta transferir pra cliente do tenant_b ->
    422 generico. Nao distingue 'nao existe' de 'existe em outro tenant'."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cliente_b"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 422
    assert "nao encontrado" in resp.json()["detail"]


# ----------------------------------------------------------------------
# INV-INT-010 bloqueio comercial
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_int_010_cessionario_bloqueado_412(cenario):
    """cessionario com bloqueio ativo -> 412 com motivo estavel."""
    with run_in_tenant_context(cenario["tenant_a"].id):
        ClienteBloqueio.objects.create(
            tenant=cenario["tenant_a"],
            cliente=cenario["cessionario"],
            motivo_categoria="automatico_inadimplencia_90d",
            justificativa_bruta=(
                "Cliente inadimplente em multiplos titulos vencidos do ciclo "
                "fiscal 2026 conforme analise comercial interna."
            ),
            confirmacao_comunicacao_previa=True,
        )
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 412
    body = resp.json()
    assert body["lado"] == "cessionario"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_int_010_cedente_bloqueado_412(cenario):
    """cedente com bloqueio -> 412."""
    with run_in_tenant_context(cenario["tenant_a"].id):
        ClienteBloqueio.objects.create(
            tenant=cenario["tenant_a"],
            cliente=cenario["cedente"],
            motivo_categoria="automatico_inadimplencia_90d",
            justificativa_bruta=(
                "Cedente inadimplente conforme ciclo D+90 — bloqueio "
                "automatico aplicado pelo job de inadimplencia."
            ),
            confirmacao_comunicacao_previa=True,
        )
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 412
    body = resp.json()
    assert body["lado"] == "cedente"


# ----------------------------------------------------------------------
# Validacoes simples
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cessionario_igual_cedente_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cedente"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_outro_sem_detalhe_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    payload = _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id, motivo="outro")
    payload["motivo_detalhe"] = ""
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        payload,
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_categoria_invalido_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    payload = _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id)
    payload["motivo_categoria"] = "nao_existe"
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        payload,
        format="json",
    )
    assert resp.status_code == 400


# ----------------------------------------------------------------------
# Authz
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_perfil_sem_transferir_toma_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    assert resp.status_code == 403


# ----------------------------------------------------------------------
# Evento payload sanitizado
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_payload_nao_vaza_cliente_ids_crus(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        evento = Auditoria.objects.get(action="equipamento.transferido")
    payload_str = str(evento.payload_jsonb)
    assert str(cenario["cedente"].id) not in payload_str
    assert str(cenario["cessionario"].id) not in payload_str
    assert evento.payload_jsonb.get("cedente_id_hash")
    assert evento.payload_jsonb.get("cessionario_id_hash")
    assert evento.payload_jsonb["motivo_categoria"] == "venda"


# ----------------------------------------------------------------------
# RLS cross-tenant - transferencia invisivel
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_transferencia_invisivel_outro_tenant(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_b"].id):
        visiveis = TransferenciaEquipamentoAceite.objects.count()
    assert visiveis == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transferencia_efetivada_aparece_no_status(cenario):
    """Defesa: TransferenciaEquipamentoAceite.status == efetivada."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/transferir/",
        _payload_completo(cenario["cessionario"].id, cenario["admin_a"].id),
        format="json",
    )
    transferencia_id = resp.json()["transferencia_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        t = TransferenciaEquipamentoAceite.objects.get(id=transferencia_id)
    assert t.status == StatusTransferencia.EFETIVADA
    assert t.efetivada_em is not None
