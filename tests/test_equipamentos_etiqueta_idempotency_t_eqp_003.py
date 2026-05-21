"""T-EQP-003 — POST /etiqueta.pdf exige `Idempotency-Key` (P-EQP-T6).

Cobre a politica P-EQP-T6:
- 400 sem header / header nao-UUID
- 200 com chave nova
- 200 replay (mesma chave + mesmo payload, dentro de 24h)
- 422 mesma chave + payload diferente (outro equipamento)
- 409 chave expirada (>24h)
- 425 chave em_processo (outra request ainda nao concluiu)
- cross-tenant: tenants A e B podem usar mesma UUID sem colisao
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.equipamentos.models import Equipamento, QRCode
from src.infrastructure.idempotencia.models import (
    ChaveIdempotencia,
    StatusChaveIdempotencia,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


def _autenticar(client: APIClient, usuario, tenant, com_mfa: bool = True) -> None:
    if com_mfa:
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
    else:
        client.force_login(usuario)
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"eqi-a-{suffix}", nome_fantasia="Lab Idemp A")
    tenant_b = TenantFactory(slug=f"eqi-b-{suffix}", nome_fantasia="Lab Idemp B")
    admin_a = UsuarioFactory(email=f"adm-a-{suffix}@i.local")
    admin_b = UsuarioFactory(email=f"adm-b-{suffix}@i.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    for u, t in [(admin_a, tenant_a), (admin_b, tenant_b)]:
        invalidate_user_cache(u.id, t.id)

    with run_in_tenant_context(tenant_a.id):
        eq_a1 = Equipamento.objects.create(
            tenant=tenant_a,
            tag="BAL-IDEMP-001",
            numero_serie="NS-1",
            fabricante="Toledo",
            modelo="Prix 4",
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
        eq_a2 = Equipamento.objects.create(
            tenant=tenant_a,
            tag="BAL-IDEMP-002",
            numero_serie="NS-2",
            fabricante="Toledo",
            modelo="Prix 4",
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
    with run_in_tenant_context(tenant_b.id):
        eq_b = Equipamento.objects.create(
            tenant=tenant_b,
            tag="BAL-IDEMP-B-1",
            numero_serie="NS-B",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "eq_a1": eq_a1,
        "eq_a2": eq_a2,
        "eq_b": eq_b,
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestHeaderObrigatorio:
    def test_sem_header_retorna_400(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        resp = client.post(f"/api/v1/equipamentos/{cenario['eq_a1'].id}/etiqueta.pdf/")
        assert resp.status_code == 400, resp.content
        body = resp.json()
        assert body["codigo"] == "idempotency_key_ausente"

    def test_header_nao_uuid_retorna_400(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        resp = client.post(
            f"/api/v1/equipamentos/{cenario['eq_a1'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY="nao-eh-uuid",
        )
        assert resp.status_code == 400, resp.content
        body = resp.json()
        assert body["codigo"] == "idempotency_key_invalido"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestChaveNova:
    def test_primeira_chamada_200_e_persiste_concluida(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        resp = client.post(
            f"/api/v1/equipamentos/{cenario['eq_a1'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert resp.status_code == 200, resp.content
        assert resp["Content-Type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF-")

        with run_in_tenant_context(cenario["tenant_a"].id):
            chaves = list(ChaveIdempotencia.objects.filter(chave=UUID(key)))
        assert len(chaves) == 1
        assert chaves[0].status == StatusChaveIdempotencia.CONCLUIDA
        assert chaves[0].response_status == 200
        assert chaves[0].endpoint == "equipamentos.etiqueta"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestReplay:
    def test_segunda_chamada_mesma_chave_200_sem_criar_qr_novo(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        eq_id = cenario["eq_a1"].id

        r1 = client.post(
            f"/api/v1/equipamentos/{eq_id}/etiqueta.pdf/", HTTP_IDEMPOTENCY_KEY=key
        )
        r2 = client.post(
            f"/api/v1/equipamentos/{eq_id}/etiqueta.pdf/", HTTP_IDEMPOTENCY_KEY=key
        )
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1["Content-Type"] == "application/pdf"
        assert r2["Content-Type"] == "application/pdf"

        with run_in_tenant_context(cenario["tenant_a"].id):
            qtd_chaves = ChaveIdempotencia.objects.filter(chave=UUID(key)).count()
            qtd_qr_vigente = QRCode.objects.filter(
                equipamento_id=eq_id, revogado_em__isnull=True
            ).count()
        assert qtd_chaves == 1  # nenhuma chave duplicada
        assert qtd_qr_vigente == 1  # nenhum QR novo criado no replay


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestPayloadDivergente422:
    def test_mesma_chave_em_equipamentos_diferentes_retorna_422(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        r1 = client.post(
            f"/api/v1/equipamentos/{cenario['eq_a1'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert r1.status_code == 200
        r2 = client.post(
            f"/api/v1/equipamentos/{cenario['eq_a2'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert r2.status_code == 422, r2.content
        assert r2.json()["codigo"] == "idempotency_key_payload_divergente"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestChaveExpirada409:
    def test_replay_apos_24h_retorna_409(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        eq_id = cenario["eq_a1"].id

        r1 = client.post(
            f"/api/v1/equipamentos/{eq_id}/etiqueta.pdf/", HTTP_IDEMPOTENCY_KEY=key
        )
        assert r1.status_code == 200

        # Forca expira_em para o passado via UPDATE direto.
        # Burla o trigger de imutabilidade temporariamente desabilitando ele
        # (o trigger bloqueia mutacao apos status terminal; usar SQL raw com
        # role superuser fugiria do escopo de teste — entao a manobra e
        # criar a chave via INSERT manual com expira_em ja vencido).
        # Mais simples: substituir a chave por uma chave nova com expira_em vencido.
        with run_in_tenant_context(cenario["tenant_a"].id):
            ChaveIdempotencia.objects.filter(chave=UUID(key)).delete()
            agora = timezone.now()
            ChaveIdempotencia.objects.create(
                tenant=cenario["tenant_a"],
                endpoint="equipamentos.etiqueta",
                chave=UUID(key),
                payload_hash=_payload_hash_para_eq(eq_id),
                usuario_id=cenario["admin_a"].id,
                status=StatusChaveIdempotencia.CONCLUIDA,
                response_status=200,
                response_body_resumo={"equipamento_tag": "X"},
                concluida_em=agora - timedelta(hours=25),
                expira_em=agora - timedelta(hours=1),
            )

        r2 = client.post(
            f"/api/v1/equipamentos/{eq_id}/etiqueta.pdf/", HTTP_IDEMPOTENCY_KEY=key
        )
        assert r2.status_code == 409, r2.content
        assert r2.json()["codigo"] == "idempotency_key_expirada"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestEmProcesso425:
    def test_chave_em_processo_retorna_425_com_retry_after(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        eq_id = cenario["eq_a1"].id

        # Pre-cria chave em_processo (simula outra request rodando).
        with run_in_tenant_context(cenario["tenant_a"].id):
            agora = timezone.now()
            ChaveIdempotencia.objects.create(
                tenant=cenario["tenant_a"],
                endpoint="equipamentos.etiqueta",
                chave=UUID(key),
                payload_hash=_payload_hash_para_eq(eq_id),
                usuario_id=cenario["admin_a"].id,
                status=StatusChaveIdempotencia.EM_PROCESSO,
                expira_em=agora + timedelta(hours=24),
            )

        resp = client.post(
            f"/api/v1/equipamentos/{eq_id}/etiqueta.pdf/", HTTP_IDEMPOTENCY_KEY=key
        )
        assert resp.status_code == 425, resp.content
        assert resp.json()["codigo"] == "idempotency_key_em_processo"
        assert resp["Retry-After"] == "1"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestCrossTenant:
    def test_mesma_uuid_em_tenants_distintos_nao_colide(self, cenario):
        client_a = APIClient()
        client_b = APIClient()
        _autenticar(client_a, cenario["admin_a"], cenario["tenant_a"])
        _autenticar(client_b, cenario["admin_b"], cenario["tenant_b"])
        key = str(uuid4())

        r_a = client_a.post(
            f"/api/v1/equipamentos/{cenario['eq_a1'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        r_b = client_b.post(
            f"/api/v1/equipamentos/{cenario['eq_b'].id}/etiqueta.pdf/",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        # Ambos sucesso — UNIQUE composto (tenant, endpoint, chave) cobre.
        assert r_a.status_code == 200, r_a.content
        assert r_b.status_code == 200, r_b.content

        # Verifica que cada tenant ve APENAS sua propria chave (RLS).
        with run_in_tenant_context(cenario["tenant_a"].id):
            chaves_a = list(ChaveIdempotencia.objects.filter(chave=UUID(key)))
        with run_in_tenant_context(cenario["tenant_b"].id):
            chaves_b = list(ChaveIdempotencia.objects.filter(chave=UUID(key)))
        assert len(chaves_a) == 1
        assert len(chaves_b) == 1
        assert chaves_a[0].tenant_id == cenario["tenant_a"].id
        assert chaves_b[0].tenant_id == cenario["tenant_b"].id


def _payload_hash_para_eq(eq_id) -> str:
    """Reproduz o hash usado pelo viewset (mesmo helper canonico)."""
    from src.infrastructure.idempotencia.services_idempotencia import (
        _calcular_payload_hash,
    )

    return _calcular_payload_hash({"equipamento_id": str(eq_id)})
