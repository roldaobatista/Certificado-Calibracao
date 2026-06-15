"""Webhook público de baixa de cobrança — testes E2E Fatia 2b (T-CR-036 / D-CR-8).

Cobre (POST /api/v1/public/contas-receber/webhook/ sem autenticação):
  - HMAC válido → baixa + estado pago
  - HMAC inválido (signature vazia) → 401
  - gateway_id inexistente → 401 (mesmo corpo — anti-oráculo R7 / D-CR-8)
  - replay mesmo gateway_event_id → 200 sem 2º Pagamento (idempotência dupla)
  - webhook em título já pago → 200 sem efeito
  - cross-tenant: webhook de tenant-A não baixa título de tenant-B

Não cobre emissão/override (→ test_contas_receber_gateway_fatia2b.py).

Bancos: default + breaker_writer (INV-TENANT-001/003).
"""

from __future__ import annotations

import uuid
import zlib
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_DBS = ["default", "breaker_writer"]
_WEBHOOK_URL = "/api/v1/public/contas-receber/webhook/"
_VENCIMENTO = date.today() + timedelta(days=30)
_VENCIMENTO_ISO = _VENCIMENTO.isoformat()


# =====================================================================
# Helpers
# =====================================================================

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


def _gateway_id_mock(titulo_id, meio: str = "boleto") -> str:
    """Reproduz _gateway_id_deterministico do MockPaymentGatewayProvider."""
    base = f"{titulo_id}|{meio}|{_VENCIMENTO.isoformat()}"
    crc = zlib.crc32(base.encode("utf-8")) & 0xFFFFFFFF
    return f"MOCK-{crc:08x}"


def _cenario_perfil_a():
    sfx = uuid.uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"cr-wh-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@crwh.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _criar_titulo_e_emitir(tenant, admin):
    """
    Cria título via REST e emite boleto (para que gateway_externo_id seja setado).
    Retorna (titulo_id, gateway_externo_id).
    """
    client = APIClient()
    _autenticar(client, admin, tenant)

    resp = client.post(
        "/api/v1/contas-receber/criar/",
        {
            "cliente_referencia_hash": uuid.uuid4().hex,
            "cliente_key_id": "v1",
            "valor_centavos": 8000,
            "data_vencimento": _VENCIMENTO_ISO,
            "meio": "boleto",
            "categoria_receita": "CALIBRACAO_RBC",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert resp.status_code == 201, f"criar falhou: {resp.data}"
    titulo_id = resp.data["titulo_id"]

    resp2 = client.post(
        f"/api/v1/contas-receber/{titulo_id}/emitir-boleto/",
        {},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert resp2.status_code == 201, f"emitir-boleto falhou: {resp2.data}"
    gateway_externo_id = resp2.data.get("gateway_externo_id")
    assert gateway_externo_id, "emitir-boleto não retornou gateway_externo_id"
    return titulo_id, gateway_externo_id


def _payload_webhook(gateway_event_id: str, titulo_gw_id: str, centavos: int = 8000) -> bytes:
    """Monta payload no formato do MockPaymentGatewayProvider: event|titulo_gw|centavos|data."""
    return f"{gateway_event_id}|{titulo_gw_id}|{centavos}|{date.today().isoformat()}".encode()


def _post_webhook(payload: bytes, signature: str = "mock-sig-valida"):
    # Retorna Response do DRF — tipo omitido para evitar import circular em arquivo de teste.
    """Envia POST para o endpoint público de webhook."""
    client = APIClient()
    return client.post(
        _WEBHOOK_URL,
        data=payload,
        content_type="application/octet-stream",
        HTTP_X_GATEWAY_SIGNATURE=signature,
    )


# =====================================================================
# HMAC válido → baixa + estado pago
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_hmac_valido_baixa_titulo():
    """Webhook com signature válida → título fica PAGO (estado contas_receber.pago)."""
    from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
    from src.infrastructure.contas_receber.models import Titulo as TituloModel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    payload = _payload_webhook(event_id, gateway_externo_id)
    resp = _post_webhook(payload, signature="qualquer-valor-nao-vazio")

    assert resp.status_code == 200, f"esperava 200, got {resp.status_code}: {resp.data}"

    # Valida no banco: estado PAGO + Pagamento criado.
    # QuerySets são lazy — avaliar DENTRO do with para que o SET LOCAL (RLS) esteja ativo.
    with run_in_tenant_context(ctx["tenant"].id):
        m = TituloModel.objects.get(id=titulo_id)
        pagamentos = list(PagamentoModel.objects.filter(titulo_id=titulo_id))  # força evaluate

    assert m.estado == "pago", f"estado esperado=pago, got={m.estado}"
    assert len(pagamentos) == 1, f"esperava 1 pagamento, got {len(pagamentos)}"
    assert pagamentos[0].gateway_event_id == event_id, "gateway_event_id não persistido"


# =====================================================================
# HMAC inválido (signature vazia) → 401
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_hmac_invalido_401():
    """Webhook com signature vazia → 401 (WebhookHMACInvalido / anti-oráculo)."""
    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    payload = _payload_webhook(event_id, gateway_externo_id)
    # Signature vazia → MockPaymentGatewayProvider.verificar_webhook lança WebhookHMACInvalido
    resp = _post_webhook(payload, signature="")

    assert resp.status_code == 401, f"esperava 401, got {resp.status_code}: {resp.data}"
    assert "nao_autorizado" in str(resp.data.get("codigo", ""))


# =====================================================================
# gateway_id inexistente → 401 (anti-oráculo: indistinguível de HMAC inválido)
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_gateway_id_inexistente_401_anti_oraculo():
    """gateway_id que não existe no banco → 401 com mesmo corpo de HMAC inválido (D-CR-8 R7)."""
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    titulo_gw_id_fantasma = f"MOCK-{uuid.uuid4().hex[:8]}"  # id que não existe
    payload = _payload_webhook(event_id, titulo_gw_id_fantasma)
    resp = _post_webhook(payload, signature="qualquer-valor-valido")

    assert resp.status_code == 401, f"esperava 401, got {resp.status_code}: {resp.data}"
    assert "nao_autorizado" in str(resp.data.get("codigo", ""))


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_anti_oraculo_corpo_identico():
    """Corpo da resposta 401 é idêntico entre HMAC inválido e gateway_id inexistente (D-CR-8)."""
    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    event_id = f"evt-{uuid.uuid4().hex[:12]}"

    # 401 por HMAC inválido
    payload_hmac = _payload_webhook(event_id, gateway_externo_id)
    resp_hmac = _post_webhook(payload_hmac, signature="")

    # 401 por gateway_id inexistente (signature seria válida)
    titulo_gw_id_fantasma = f"MOCK-{uuid.uuid4().hex[:8]}"
    payload_gw = _payload_webhook(event_id, titulo_gw_id_fantasma)
    resp_gw = _post_webhook(payload_gw, signature="qualquer-valor-valido")

    assert resp_hmac.status_code == 401
    assert resp_gw.status_code == 401
    # Corpos devem ser idênticos (anti-oráculo — D-CR-8 R7)
    assert resp_hmac.data.get("codigo") == resp_gw.data.get("codigo"), (
        f"anti-oráculo violado: resp HMAC={resp_hmac.data}, resp GW={resp_gw.data}"
    )


# =====================================================================
# Replay mesmo gateway_event_id → 200 sem 2º Pagamento (idempotência dupla)
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_replay_idempotente_sem_pagamento_duplo():
    """Segundo POST com mesmo gateway_event_id → 200 sem criar Pagamento duplicado."""
    from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    payload = _payload_webhook(event_id, gateway_externo_id)

    resp1 = _post_webhook(payload, signature="sig-valida")
    resp2 = _post_webhook(payload, signature="sig-valida")

    assert resp1.status_code == 200, f"1ª chamada: {resp1.status_code} {resp1.data}"
    assert resp2.status_code == 200, f"2ª chamada: {resp2.status_code} {resp2.data}"

    with run_in_tenant_context(ctx["tenant"].id):
        contagem = PagamentoModel.objects.filter(titulo_id=titulo_id).count()

    assert contagem == 1, f"idempotência violada: {contagem} pagamentos (esperava 1)"


# =====================================================================
# Webhook em título já pago → 200 sem efeito
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_titulo_ja_pago_200_sem_efeito():
    """Webhook recebido após título já pago → 200 sem criar novo Pagamento."""
    from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    # 1ª baixa via webhook (evento genuíno)
    event_id_1 = f"evt-{uuid.uuid4().hex[:12]}"
    payload1 = _payload_webhook(event_id_1, gateway_externo_id)
    resp1 = _post_webhook(payload1, signature="sig-valida")
    assert resp1.status_code == 200, f"1ª baixa: {resp1.status_code} {resp1.data}"

    # 2ª chegada (gateway reenvio com event_id diferente, mas título já pago)
    event_id_2 = f"evt-{uuid.uuid4().hex[:12]}"
    payload2 = _payload_webhook(event_id_2, gateway_externo_id)
    resp2 = _post_webhook(payload2, signature="sig-valida")

    assert resp2.status_code == 200, f"2ª baixa já pago: {resp2.status_code} {resp2.data}"

    # Deve ter apenas 1 Pagamento (o primeiro)
    with run_in_tenant_context(ctx["tenant"].id):
        contagem = PagamentoModel.objects.filter(titulo_id=titulo_id).count()

    assert contagem == 1, f"esperava 1 pagamento, got {contagem}"


# =====================================================================
# Cross-tenant: webhook não baixa título de tenant errado
# =====================================================================

@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_webhook_cross_tenant_nao_baixa_titulo_alheio():
    """Webhook de tenant A não pode baixar título de tenant B (INV-TENANT-001/003)."""
    from src.infrastructure.contas_receber.models import Titulo as TituloModel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    # Tenant A (tem título emitido)
    ctx_a = _cenario_perfil_a()
    titulo_id_a, gateway_externo_id_a = _criar_titulo_e_emitir(ctx_a["tenant"], ctx_a["admin"])

    # Tenant B (completamente diferente)
    ctx_b = _cenario_perfil_a()
    titulo_id_b, gateway_externo_id_b = _criar_titulo_e_emitir(ctx_b["tenant"], ctx_b["admin"])

    # Envia webhook com gateway_id do titulo_b mas assinado para tenant_a
    # O SECURITY DEFINER vai resolver tenant_b (correto — lookup é global)
    # O título baixado deve ser de tenant_b, não de tenant_a
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    payload = _payload_webhook(event_id, gateway_externo_id_b)
    resp = _post_webhook(payload, signature="sig-valida")

    # Webhook processa OK para tenant_b (o SECURITY DEFINER encontrou)
    assert resp.status_code == 200, f"webhook cross-tenant: {resp.status_code} {resp.data}"

    # Título de tenant_a NÃO deve ter sido afetado
    with run_in_tenant_context(ctx_a["tenant"].id):
        m_a = TituloModel.objects.get(id=titulo_id_a)
    assert m_a.estado != "pago", (
        f"Cross-tenant violado: título de tenant_a ficou pago (estado={m_a.estado})"
    )

    # Título de tenant_b deve estar pago (foi ele que o webhook processou)
    with run_in_tenant_context(ctx_b["tenant"].id):
        m_b = TituloModel.objects.get(id=titulo_id_b)
    assert m_b.estado == "pago", (
        f"título de tenant_b deveria estar pago, got estado={m_b.estado}"
    )
