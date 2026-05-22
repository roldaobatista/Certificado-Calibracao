"""T-EQP-025+026+033 — GET /api/v1/qr/{hash}/ 3 escopos publico.

Cobre:
- AC-EQP-003-2 / INV-051: 3 escopos resolvidos por sessao.
- AC-EQP-003-3 / P-EQP-T3: timing constant 200ms; 404 indistinguivel.
- AC-EQP-003-10 / P-EQP-S2: Escopo B 404 (sem oracle).
- Allowlist publica: payload Escopo C nao vaza tenant/cliente/tag/NS.
- Soft-delete + revogado: nao resolvem (404).
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, QRCode
from src.infrastructure.equipamentos.services_qr import gerar_qr_hash_versionado
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
    tenant_a = TenantFactory(slug=f"qrp-a-{sfx}", nome_fantasia="Lab A")
    tenant_b = TenantFactory(slug=f"qrp-b-{sfx}", nome_fantasia="Lab B")
    admin_a = UsuarioFactory(email=f"adm-a-{sfx}@e.local")
    admin_b = UsuarioFactory(email=f"adm-b-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    for u, t in [(admin_a, tenant_a), (admin_b, tenant_b)]:
        invalidate_user_cache(u.id, t.id)

    with run_in_tenant_context(tenant_a.id):
        cliente_a = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente PriX QR",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_a = Equipamento.objects.create(
            tenant=tenant_a,
            tag="QRP-A-001",
            numero_serie="NS-QRP-A-SECRETO",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente_a,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        # Gera QR vigente.
        hash_a = gerar_qr_hash_versionado(
            equipamento_id=eq_a.id,
            tenant_id=tenant_a.id,
            emitido_em=timezone.now(),
        )
        qr_a = QRCode.objects.create(
            tenant=tenant_a,
            equipamento=eq_a,
            hash=hash_a,
            emitido_em=timezone.now(),
        )
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "cliente_a": cliente_a,
        "eq_a": eq_a,
        "qr_a": qr_a,
        "hash_a": hash_a,
    }


# ----------------------------------------------------------------------
# Escopo A — autenticado mesmo tenant -> ficha completa
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_escopo_a_autenticado_mesmo_tenant_retorna_ficha_completa(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 200
    body = resp.json()
    # Escopo A retorna ficha 360 completa.
    assert body["equipamento"]["tag"] == "QRP-A-001"
    assert body["equipamento"]["numero_serie"] == "NS-QRP-A-SECRETO"
    assert "perfil_no_momento_do_cadastro" in body


# ----------------------------------------------------------------------
# Escopo B — autenticado OUTRO tenant -> 404 indistinguivel (P-EQP-S2)
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_escopo_b_autenticado_outro_tenant_retorna_404(cenario):
    """P-EQP-S2: cross-tenant nao vaza nem payload minimo — 404."""
    client = APIClient()
    _autenticar(client, cenario["admin_b"], cenario["tenant_b"])
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 404
    body = resp.json()
    # Body deve ser IGUAL ao 404 de hash invalido (indistinguivel).
    assert body == {"detail": "qr_nao_encontrado"}


# ----------------------------------------------------------------------
# Escopo C — anonimo -> 200 payload minimo allowlist
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_escopo_c_anonimo_retorna_payload_minimo(cenario):
    client = APIClient()
    # Sem autenticar.
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["tipo"] == "ativo_afere"
    assert body["fabricante"] == "Toledo"
    assert body["modelo"] == "Prix 4"
    assert body["status"] == "ativo"
    assert "mensagem" in body
    assert body["afere_url_institucional"] == "https://afere.com.br"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_escopo_c_payload_nao_vaza_tenant_cliente_tag_ns(cenario):
    """Allowlist Escopo C: NUNCA tenant_id, cliente_id, tag, NS,
    localizacao, foto, historico, eventos."""
    client = APIClient()
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    body_txt = resp.content.decode("utf-8")
    assert str(cenario["tenant_a"].id) not in body_txt
    assert str(cenario["cliente_a"].id) not in body_txt
    assert "QRP-A-001" not in body_txt  # TAG
    assert "NS-QRP-A-SECRETO" not in body_txt  # NS
    assert "Cliente PriX" not in body_txt  # nome cliente


# ----------------------------------------------------------------------
# 404 indistinguivel
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_hash_invalido_404(cenario):
    client = APIClient()
    resp = client.get("/api/v1/qr/hashqualquersem_prefixo/")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "qr_nao_encontrado"}


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_hash_inexistente_mas_bem_formado_404(cenario):
    client = APIClient()
    resp = client.get("/api/v1/qr/qr1:zzzzzzzzzzzzzzzzzzzzzz/")
    assert resp.status_code == 404


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_qr_revogado_anonimo_404(cenario):
    """QR revogado nao resolve — mesmo Escopo C."""
    with run_in_tenant_context(cenario["tenant_a"].id):
        QRCode.all_objects.filter(id=cenario["qr_a"].id).update(
            revogado_em=timezone.now()
        )
    client = APIClient()
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 404


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_qr_de_equipamento_soft_deleted_404(cenario):
    """Equipamento soft-deletado nao resolve."""
    from datetime import UTC, datetime

    with run_in_tenant_context(cenario["tenant_a"].id):
        Equipamento.all_objects.filter(id=cenario["eq_a"].id).update(
            deletado_em=datetime.now(UTC)
        )
    client = APIClient()
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# Timing constant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_timing_constant_404_proximo_de_alvo(cenario):
    """Latencia de 404 (hash invalido) >= TIMING_ALVO_MS - tolerancia.

    Sanity check: nao mede precisao p99 (isso e GATE-EQP-PENTEST), mas
    confirma que a normalizacao esta ativa (sem ela a latencia seria
    <50ms; com normalizacao fica perto de 200ms)."""
    from src.infrastructure.equipamentos.services_qr_publico import (
        TIMING_ALVO_MS,
        TIMING_TOLERANCIA_MS,
    )
    client = APIClient()
    t0 = time.perf_counter()
    resp = client.get("/api/v1/qr/qr1:zzz/")
    dt_ms = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 404
    assert dt_ms >= TIMING_ALVO_MS - TIMING_TOLERANCIA_MS, (
        f"latencia muito curta ({dt_ms:.1f}ms) — timing constant nao ativou"
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_timing_404_e_200_anonimo_similares(cenario):
    """Diferenca de latencia entre 404 (invalido) e 200 (valido) deve
    ser pequena (timing constant normaliza)."""
    client = APIClient()
    # Mede 404 (hash invalido).
    t0 = time.perf_counter()
    client.get("/api/v1/qr/qr1:zzz/")
    dt_404 = (time.perf_counter() - t0) * 1000
    # Mede 200 (hash valido — Escopo C).
    t0 = time.perf_counter()
    client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    dt_200 = (time.perf_counter() - t0) * 1000
    # Tolerancia generosa em test (Wave A fuzzing valida ±5ms p99).
    delta_ms = abs(dt_200 - dt_404)
    assert delta_ms < 100, (
        f"timing oracle detectado: dt_200={dt_200:.1f} dt_404={dt_404:.1f}"
    )
