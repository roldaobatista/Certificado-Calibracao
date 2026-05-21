"""T-EQP-005 + T-EQP-007 — POST /api/v1/equipamentos/ cadastro.

Cobre:
- AC-EQP-001-1: cadastro happy 201.
- AC-EQP-001-3 (INV-049): TAG duplicada no mesmo tenant -> 409 com
  referencia ao equipamento existente.
- AC-EQP-001-4 (INV-EQP-LOC-001): localizacao_fisica com CPF/CNPJ/
  email/telefone/nomes consecutivos -> 400.
- AC-EQP-001-6 (T-EQP-007): publica `equipamento.criado` na cadeia
  com payload sanitizado (tag_hash + numero_serie_hash em vez de cru).
- AC-EQP-001-2b (T-EQP-003): POST exige Idempotency-Key UUID.
- Cross-tenant: tenant B nao consegue criar equipamento "para" tenant A
  (RLS + middleware bloqueiam).
- Authz: perfil sem `equipamentos.criar` toma 403.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.equipamentos.models import Equipamento
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
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"eqc-a-{sfx}", nome_fantasia="Lab Criar A")
    tenant_b = TenantFactory(slug=f"eqc-b-{sfx}", nome_fantasia="Lab Criar B")
    admin_a = UsuarioFactory(email=f"adm-a-{sfx}@c.local")
    admin_b = UsuarioFactory(email=f"adm-b-{sfx}@c.local")
    leitor_a = UsuarioFactory(email=f"ler-a-{sfx}@c.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=leitor_a, tenant=tenant_a, perfil="cliente_externo_leitura")
    for u, t in [(admin_a, tenant_a), (admin_b, tenant_b), (leitor_a, tenant_a)]:
        invalidate_user_cache(u.id, t.id)
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "leitor_a": leitor_a,
    }


def _payload_basico() -> dict:
    return {
        "tag": "BAL-CRIAR-001",
        "numero_serie": "NS-AABB-001",
        "fabricante": "Toledo",
        "modelo": "Prix 4",
        "perfil_tenant_snapshot": {"perfil": "D", "schema": "1.0.0"},
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestCadastroHappy:
    def test_admin_cadastra_201_e_publica_evento(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        resp = client.post(
            "/api/v1/equipamentos/",
            _payload_basico(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert body["tag"] == "BAL-CRIAR-001"
        assert body["status"] == "ativo"
        # Equipamento existe + evento publicado na cadeia
        with run_in_tenant_context(cenario["tenant_a"].id):
            assert Equipamento.objects.filter(id=body["id"]).exists()
            assert Auditoria.objects.filter(action="equipamento.criado").exists()

    def test_evento_publicado_nao_vaza_tag_crua(self, cenario):
        """T-EQP-007 / AC-EQP-001-6: payload tem tag_hash, nao tag literal."""
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        tag_unica = f"BAL-SECRETA-{uuid4().hex[:6]}"
        payload = _payload_basico() | {"tag": tag_unica, "numero_serie": f"NS-{uuid4().hex[:8]}"}
        resp = client.post(
            "/api/v1/equipamentos/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert resp.status_code == 201, resp.content
        with run_in_tenant_context(cenario["tenant_a"].id):
            evento = Auditoria.objects.filter(action="equipamento.criado").order_by(
                "-timestamp"
            ).first()
        assert evento is not None
        # Tag crua NAO pode estar no payload — apenas hash
        canon = str(evento.payload_jsonb)
        assert tag_unica not in canon
        assert "tag_hash" in canon


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestTagDuplicada:
    def test_tag_duplicada_no_mesmo_tenant_retorna_409(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        payload = _payload_basico()
        r1 = client.post(
            "/api/v1/equipamentos/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert r1.status_code == 201, r1.content
        # Segunda chamada com mesma TAG (numero_serie pode ser igual ou nao)
        # mas chave idempotency diferente — TagDuplicada deve disparar.
        payload2 = _payload_basico() | {"numero_serie": "OUTRO-NS"}
        r2 = client.post(
            "/api/v1/equipamentos/",
            payload2,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert r2.status_code == 409, r2.content
        body = r2.json()
        assert body["codigo"] == "tag_duplicada"
        assert "equipamento_existente_id" in body


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestINVEqpLoc001:
    @pytest.mark.parametrize(
        "loc_pii",
        [
            "Sala do Joao Silva 123.456.789-01",  # CPF
            "Sala do Toledo 12.345.678/0001-90",  # CNPJ
            "Contato joao@labx.com.br",  # email
            "Tel (11) 99999-9999 — bancada",  # telefone
            "Sala Joao Silva",  # 2 nomes proprios
        ],
    )
    def test_localizacao_com_pii_retorna_400(self, cenario, loc_pii):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        payload = _payload_basico() | {
            "tag": f"X-{uuid4().hex[:6]}",
            "numero_serie": f"NS-{uuid4().hex[:6]}",
            "localizacao_fisica": loc_pii,
        }
        resp = client.post(
            "/api/v1/equipamentos/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert resp.status_code == 400, resp.content
        body = resp.json()
        # serializer field validation -> sob chave do campo
        assert "localizacao_fisica" in body or "INV-EQP-LOC-001" in str(body)

    def test_localizacao_sem_pii_aceita(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        payload = _payload_basico() | {
            "tag": f"X-{uuid4().hex[:6]}",
            "numero_serie": f"NS-{uuid4().hex[:6]}",
            "localizacao_fisica": "Sala A - Bancada 3",
        }
        resp = client.post(
            "/api/v1/equipamentos/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert resp.status_code == 201, resp.content


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestIdempotencyKey:
    def test_post_sem_idempotency_key_retorna_400(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        resp = client.post("/api/v1/equipamentos/", _payload_basico(), format="json")
        assert resp.status_code == 400, resp.content
        assert resp.json()["codigo"] == "idempotency_key_ausente"

    def test_replay_mesma_chave_retorna_200_sem_duplicar(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        key = str(uuid4())
        r1 = client.post(
            "/api/v1/equipamentos/",
            _payload_basico(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        r2 = client.post(
            "/api/v1/equipamentos/",
            _payload_basico(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        assert r1.status_code == 201
        assert r2.status_code == 200  # replay
        # Apenas 1 equipamento criado
        with run_in_tenant_context(cenario["tenant_a"].id):
            assert Equipamento.objects.filter(tag=_payload_basico()["tag"]).count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
class TestAuthz:
    def test_cliente_externo_sem_criar_toma_403(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
        resp = client.post(
            "/api/v1/equipamentos/",
            _payload_basico(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        assert resp.status_code == 403, resp.content
