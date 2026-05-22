"""T-EQP-039 + T-EQP-041 — consentimento historico granular do cedente
(US-EQP-004 fase 3 / P-EQP-R6 / AC-EQP-004-6 + AC-EQP-004-8).

Cobre:
- T-EQP-039 concessao: efetivacao de transferencia grava 1 registro de
  `ConsentimentoHistoricoEquipamento` no MESMO bloco transacional, com
  nivel derivado do `aceite_cedente.nivel_consentimento_historico` (3
  niveis: nada/resumo/completo) ou do legacy boolean.
- T-EQP-039 evento: payload sanitizado de
  `equipamento.consentimento_historico_concedido` (cedente_id_hash,
  nunca UUID cru).
- T-EQP-041 revogacao: endpoint POST grava revogacao + publica
  `equipamento.consentimento_historico_revogado`; justificativa em
  CLARO nao persiste — apenas hash.
- T-EQP-041 one-shot: segunda revogacao retorna 412 (trigger PG +
  service).
- Validacoes: justificativa curta / com PII -> 400.
- Authz: perfil sem `equipamentos.revogar_consentimento_historico` ->
  403.
- Cross-tenant: consentimento de outro tenant invisivel + 404.
- Trigger PG: UPDATE direto em campo CORE bloqueado.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    ConsentimentoHistoricoEquipamento,
    Equipamento,
    NivelConsentimentoHistorico,
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
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"cons-a-{sfx}", nome_fantasia="Lab A")
    tenant_b = TenantFactory(slug=f"cons-b-{sfx}", nome_fantasia="Lab B")
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
            tag="CONS-A-001",
            numero_serie="NS-CONS-A",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cedente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "leitor_a": leitor_a,
        "cedente": cedente,
        "cessionario": cessionario,
        "eq_a": eq_a,
    }


def _payload_transferencia(
    cessionario_id, atendente_id, nivel: str = "completo"
):
    return {
        "cessionario_cliente_id": str(cessionario_id),
        "motivo_categoria": "venda",
        "aceite_cedente": {
            "tipo": "presencial_atendente",
            "usuario_id_atendente": str(atendente_id),
            "observacao": "Atendente confirma ciencia do termo.",
            "nivel_consentimento_historico": nivel,
        },
        "aceite_cessionario": {
            "tipo": "contrato_fisico_digitalizado",
            "usuario_id_atendente": str(atendente_id),
            "observacao": "Contrato escaneado anexo.",
            "consentimento_historico_expresso": True,
        },
    }


def _transferir(client, equipamento_id, payload):
    return client.post(
        f"/api/v1/equipamentos/{equipamento_id}/transferir/",
        payload,
        format="json",
    )


# ====================================================================
# T-EQP-039 — concessao automatica em transferencia efetivada
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transferencia_efetivada_grava_consentimento_nivel_completo(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = _transferir(
        client,
        cenario["eq_a"].id,
        _payload_transferencia(
            cenario["cessionario"].id, cenario["admin_a"].id, nivel="completo"
        ),
    )
    assert resp.status_code == 200, resp.content

    with run_in_tenant_context(cenario["tenant_a"].id):
        consents = list(
            ConsentimentoHistoricoEquipamento.objects.filter(
                equipamento_id=cenario["eq_a"].id
            )
        )
    assert len(consents) == 1
    assert consents[0].nivel == NivelConsentimentoHistorico.COMPLETO.value
    assert consents[0].cedente_cliente_id == cenario["cedente"].id
    assert consents[0].revogado_em is None
    assert consents[0].via_concessao == "presencial_atendente"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transferencia_efetivada_grava_consentimento_nivel_resumo(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = _transferir(
        client,
        cenario["eq_a"].id,
        _payload_transferencia(
            cenario["cessionario"].id, cenario["admin_a"].id, nivel="resumo"
        ),
    )
    assert resp.status_code == 200, resp.content
    with run_in_tenant_context(cenario["tenant_a"].id):
        c = ConsentimentoHistoricoEquipamento.objects.get(
            equipamento_id=cenario["eq_a"].id
        )
    assert c.nivel == NivelConsentimentoHistorico.RESUMO.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transferencia_efetivada_grava_consentimento_nivel_nada(cenario):
    """Cedente declara expressamente que NAO compartilha — registro
    existe assim mesmo (prova LGPD)."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = _transferir(
        client,
        cenario["eq_a"].id,
        _payload_transferencia(
            cenario["cessionario"].id, cenario["admin_a"].id, nivel="nada"
        ),
    )
    assert resp.status_code == 200, resp.content
    with run_in_tenant_context(cenario["tenant_a"].id):
        c = ConsentimentoHistoricoEquipamento.objects.get(
            equipamento_id=cenario["eq_a"].id
        )
    assert c.nivel == NivelConsentimentoHistorico.NADA.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_concedido_payload_nao_vaza_cedente_id_cru(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    _transferir(
        client,
        cenario["eq_a"].id,
        _payload_transferencia(cenario["cessionario"].id, cenario["admin_a"].id),
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        evento = Auditoria.objects.get(
            action="equipamento.consentimento_historico_concedido"
        )
    payload_str = str(evento.payload_jsonb)
    assert str(cenario["cedente"].id) not in payload_str
    assert evento.payload_jsonb.get("cedente_id_hash")
    assert evento.payload_jsonb["nivel"] == "completo"
    assert evento.payload_jsonb.get("consentimento_id")


# ====================================================================
# T-EQP-041 — endpoint revogacao
# ====================================================================


def _criar_consent_via_transferencia(cenario, client, nivel="completo"):
    _transferir(
        client,
        cenario["eq_a"].id,
        _payload_transferencia(
            cenario["cessionario"].id, cenario["admin_a"].id, nivel=nivel
        ),
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        return ConsentimentoHistoricoEquipamento.objects.get(
            equipamento_id=cenario["eq_a"].id
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_consentimento_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    # Nova chave Idempotency para o request seguinte.
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(consent.id),
            "justificativa": (
                "O cedente solicitou revogacao por mudanca de politica "
                "interna do laboratorio."
            ),
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["consentimento_id"] == str(consent.id)
    assert body["revogado_em"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        consent.refresh_from_db()
    assert consent.revogado_em is not None
    assert consent.revogado_por_id == cenario["admin_a"].id
    assert consent.revogado_via == "presencial_atendente"
    assert consent.revogado_justificativa_hash  # hash gravado
    # justificativa em CLARO nunca persiste:
    assert "revogacao por mudanca" not in consent.revogado_justificativa_hash


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_segunda_vez_412_one_shot(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    body_revogar = {
        "consentimento_id": str(consent.id),
        "justificativa": (
            "Cedente solicitou revogacao formal por escrito conforme "
            "registro interno."
        ),
        "via_revogacao": "presencial_atendente",
    }
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        body_revogar,
        format="json",
    )
    assert r1.status_code == 200
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        body_revogar,
        format="json",
    )
    assert r2.status_code == 412
    assert "ja revogado" in r2.json()["detail"]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_justificativa_curta_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(consent.id),
            "justificativa": "curto demais",
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_justificativa_com_pii_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(consent.id),
            "justificativa": (
                "Cedente Joao Silva pediu revogacao por escrito assinada."
            ),
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_perfil_sem_authz_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    # Troca para perfil sem authz revogar.
    client_leitor = APIClient()
    _autenticar(client_leitor, cenario["leitor_a"], cenario["tenant_a"])
    resp = client_leitor.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(consent.id),
            "justificativa": (
                "Tentativa de revogacao por usuario sem perfil — defesa authz."
            ),
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_revogar_consent_inexistente_404(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    # Sem criar consentimento — equipamento sem nenhum.
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(uuid4()),
            "justificativa": (
                "Revogacao de consentimento inexistente — defesa em profundidade."
            ),
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_revogado_payload_sanitizado(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    consent = _criar_consent_via_transferencia(cenario, client)
    justificativa = (
        "O cedente revogou por mudanca interna de politica documentada."
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    client.post(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/consentimento-historico/revogar/",
        {
            "consentimento_id": str(consent.id),
            "justificativa": justificativa,
            "via_revogacao": "presencial_atendente",
        },
        format="json",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        evento = Auditoria.objects.get(
            action="equipamento.consentimento_historico_revogado"
        )
    payload_str = str(evento.payload_jsonb)
    # texto cru NUNCA aparece no payload
    assert "mudanca interna" not in payload_str
    # cedente_id cru NUNCA aparece
    assert str(cenario["cedente"].id) not in payload_str
    assert evento.payload_jsonb.get("justificativa_hash")
    assert evento.payload_jsonb.get("cedente_id_hash")
    assert evento.payload_jsonb["via_revogacao"] == "presencial_atendente"


# ====================================================================
# T-EQP-039/041 — defesa trigger PG imutabilidade (camada B)
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_trigger_pg_bloqueia_update_campo_core(cenario):
    """UPDATE direto via ORM no nivel (campo CORE imutavel) deve falhar."""
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    # consent default nivel='completo'. Tenta mutar pra 'resumo' (valor
    # diferente) — trigger PG deve rejeitar (campo CORE imutavel).
    consent = _criar_consent_via_transferencia(cenario, client, nivel="completo")
    with run_in_tenant_context(cenario["tenant_a"].id):
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos_consentimento_historico SET nivel='resumo' WHERE id=%s",
                    [str(consent.id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "imutaveis pos-INSERT" in msg or "T-EQP-039" in msg


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_consentimento_invisivel_outro_tenant(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    _criar_consent_via_transferencia(cenario, client)
    with run_in_tenant_context(cenario["tenant_b"].id):
        visiveis = ConsentimentoHistoricoEquipamento.objects.count()
    assert visiveis == 0
