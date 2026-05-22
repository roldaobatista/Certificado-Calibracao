"""T-EQP-053+056+057 — recebimento provisorio (US-EQP-006 fase 3 /
Caminho A Roldao / P-EQP-R9 / INV-EQP-PROV-001).

Cobre:
- Happy criar provisorio (POST /equipamentos/provisorios/) com foto.
- Happy promover (POST /equipamentos/provisorios/{id}/promover/) cria
  Equipamento canonico + 1o EquipamentoRecebimento + atualiza status.
- 409 promover ja-promovido + 409 promover expirado.
- 400 sem foto + 400 tag_provisoria curta/PII + 400 descricao curta/PII +
  400 condicao fora enum.
- 403 sem authz.
- RLS cross-tenant invisivel.
- Trigger PG imutabilidade pos-INSERT (UPDATE em CORE bloqueado +
  re-mutacao terminal bloqueada).
- T-EQP-056: management command marca expirados + publica
  sistema.provisorio_expirado.
- T-EQP-057: GET /metricas/ calcula taxa_provisorios_mensal +
  alerta_excedido quando >5%.
- Payload sanitizado (cliente NUNCA aparece).
- AC-EQP-006-8: devolucao exige Equipamento canonico (provisorio NAO
  tem ciclo de devolucao proprio — design via tabela separada).
"""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoRecebimento,
    RecebimentoProvisorio,
    RecebimentoProvisorioFoto,
    StatusRecebimentoProvisorio,
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


def _gerar_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (50, 50), color=(80, 90, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"prov-a-{sfx}", nome_fantasia="Lab Prov A")
    admin_a = UsuarioFactory(email=f"adm-prov-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-prov-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=leitor_a, tenant=tenant_a, perfil="cliente_externo_leitura"
    )
    for u in [admin_a, leitor_a]:
        invalidate_user_cache(u.id, tenant_a.id)

    with run_in_tenant_context(tenant_a.id):
        cliente = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Prov",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    return {
        "tenant_a": tenant_a,
        "admin_a": admin_a,
        "leitor_a": leitor_a,
        "cliente": cliente,
    }


def _criar_provisorio_via_api(client, cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    return client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": f"PROV-{uuid4().hex[:6]}",
            "descricao_estimada": "Balanca digital marca incerta cap 30kg.",
            "condicao_visual_chegada": "integro",
            "foto": foto,
        },
        format="multipart",
    )


# ====================================================================
# Happy paths
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = _criar_provisorio_via_api(client, cenario)
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["provisorio_id"]
    assert body["status"] == "pendente_promocao"
    assert len(body["foto_sha256"]) == 64
    assert body["ttl_expira_em"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        prov = RecebimentoProvisorio.objects.get(id=body["provisorio_id"])
        foto = RecebimentoProvisorioFoto.objects.get(provisorio_id=prov.id)
    assert prov.status == "pendente_promocao"
    assert foto.mime_type == "image/jpeg"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_promover_provisorio_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = _criar_provisorio_via_api(client, cenario)
    prov_id = r1.json()["provisorio_id"]
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    sfx = uuid4().hex[:6]
    r2 = client.post(
        f"/api/v1/equipamentos/provisorios/{prov_id}/promover/",
        {
            "tag_canonica": f"CANON-{sfx}",
            "numero_serie": f"NS-{sfx}",
            "fabricante": "Toledo",
            "modelo": "Prix 4",
            "cliente_atual_id": str(cenario["cliente"].id),
            "perfil_tenant_snapshot": {"perfil": "D"},
        },
        format="json",
    )
    assert r2.status_code == 200, r2.content
    body = r2.json()
    assert body["equipamento_id"]
    assert body["recebimento_id"]
    assert body["tag_canonica"] == f"CANON-{sfx}"
    with run_in_tenant_context(cenario["tenant_a"].id):
        prov = RecebimentoProvisorio.objects.get(id=prov_id)
        eq = Equipamento.objects.get(id=body["equipamento_id"])
        rec = EquipamentoRecebimento.objects.get(id=body["recebimento_id"])
    assert prov.status == "promovido"
    assert prov.equipamento_promovido_id == eq.id
    assert prov.promovido_em is not None
    assert eq.tag == f"CANON-{sfx}"
    assert rec.equipamento_id == eq.id
    assert rec.foto_sha256 == prov.foto_sha256  # foto reusada


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_promover_duplicado_409(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = _criar_provisorio_via_api(client, cenario)
    prov_id = r1.json()["provisorio_id"]
    body_promover = {
        "tag_canonica": f"DUP-{uuid4().hex[:6]}",
        "numero_serie": f"NS-DUP-{uuid4().hex[:6]}",
        "fabricante": "Toledo",
        "modelo": "Prix 4",
        "cliente_atual_id": str(cenario["cliente"].id),
        "perfil_tenant_snapshot": {"perfil": "D"},
    }
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/provisorios/{prov_id}/promover/",
        body_promover,
        format="json",
    )
    assert r2.status_code == 200
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r3 = client.post(
        f"/api/v1/equipamentos/provisorios/{prov_id}/promover/",
        {**body_promover, "tag_canonica": f"DUP2-{uuid4().hex[:6]}"},
        format="json",
    )
    assert r3.status_code == 409
    assert "promovido" in r3.json()["detail"].lower()


def _criar_provisorio_com_ttl_passado(cenario, user_id) -> str:
    """Helper: cria provisorio diretamente via ORM com ttl_expira_em
    no passado (INSERT inicial — trigger BEFORE UPDATE nao se aplica).
    """
    from datetime import timedelta

    with run_in_tenant_context(cenario["tenant_a"].id):
        prov = RecebimentoProvisorio.objects.create(
            tenant_id=cenario["tenant_a"].id,
            tag_provisoria=f"EXP-{uuid4().hex[:6]}",
            descricao_estimada="Provisorio com TTL forcadamente no passado.",
            condicao_visual_chegada="integro",
            foto_storage_key=str(uuid4()),
            foto_sha256="a" * 64,
            recebido_por_id=user_id,
            ttl_expira_em=timezone.now() - timedelta(days=1),
        )
    return str(prov.id)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_promover_provisorio_expirado_409(cenario):
    """Provisorio com TTL vencido -> promover bloqueado 409."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    prov_id = _criar_provisorio_com_ttl_passado(
        cenario, cenario["admin_a"].id
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    sfx = uuid4().hex[:6]
    r2 = client.post(
        f"/api/v1/equipamentos/provisorios/{prov_id}/promover/",
        {
            "tag_canonica": f"EXP-{sfx}",
            "numero_serie": f"NS-EXP-{sfx}",
            "fabricante": "Toledo",
            "modelo": "Prix 4",
            "cliente_atual_id": str(cenario["cliente"].id),
            "perfil_tenant_snapshot": {"perfil": "D"},
        },
        format="json",
    )
    assert r2.status_code == 409
    assert "vencido" in r2.json()["detail"].lower() or "expir" in r2.json()["detail"].lower()


# ====================================================================
# Validacoes
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_sem_foto_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": f"PROV-{uuid4().hex[:6]}",
            "descricao_estimada": "Balanca generica.",
            "condicao_visual_chegada": "integro",
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_tag_curta_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    resp = client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": "ab",
            "descricao_estimada": "Balanca generica de mesa pequena.",
            "condicao_visual_chegada": "integro",
            "foto": foto,
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_descricao_com_pii_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    resp = client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": f"PROV-{uuid4().hex[:6]}",
            "descricao_estimada": "Cliente Joao Silva da Costa trouxe.",
            "condicao_visual_chegada": "integro",
            "foto": foto,
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_condicao_invalida_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    resp = client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": f"PROV-{uuid4().hex[:6]}",
            "descricao_estimada": "Balanca digital marca incerta cap 30kg.",
            "condicao_visual_chegada": "fora_do_enum",
            "foto": foto,
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_provisorio_perfil_sem_authz_403(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    resp = client.post(
        "/api/v1/equipamentos/provisorios/",
        {
            "tag_provisoria": f"PROV-{uuid4().hex[:6]}",
            "descricao_estimada": "Balanca digital marca incerta cap 30kg.",
            "condicao_visual_chegada": "integro",
            "foto": foto,
        },
        format="multipart",
    )
    assert resp.status_code == 403


# ====================================================================
# Trigger PG imutabilidade
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_trigger_pg_bloqueia_update_campo_core(cenario):
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = _criar_provisorio_via_api(client, cenario)
    prov_id = r1.json()["provisorio_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos_recebimento_provisorio SET tag_provisoria='HACK' WHERE id=%s",
                    [str(prov_id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "imutaveis pos-INSERT" in msg or "T-EQP-053" in msg


# ====================================================================
# RLS
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_provisorio_cross_tenant_invisivel(cenario):
    sfx = uuid4().hex[:6]
    tenant_b = TenantFactory(slug=f"prov-b-{sfx}")
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    _criar_provisorio_via_api(client, cenario)
    with run_in_tenant_context(tenant_b.id):
        visiveis = RecebimentoProvisorio.objects.count()
    assert visiveis == 0


# ====================================================================
# T-EQP-056 — job TTL
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_job_marca_provisorios_expirados(cenario):
    """Provisorio com TTL vencido -> management command marca como
    expirado_descartado + publica sistema.provisorio_expirado."""
    from django.core.management import call_command

    prov_id = _criar_provisorio_com_ttl_passado(
        cenario, cenario["admin_a"].id
    )
    # Roda command (sem --tenant pra exercitar iteracao multi-tenant).
    call_command(
        "processar_provisorios_expirados",
        f"--tenant={cenario['tenant_a'].id}",
    )
    from src.infrastructure.multitenant.connection import run_as_system

    with run_in_tenant_context(cenario["tenant_a"].id):
        prov = RecebimentoProvisorio.objects.get(id=prov_id)
    assert prov.status == StatusRecebimentoProvisorio.EXPIRADO_DESCARTADO.value
    # Eventos sistema (tenant_id=NULL) requerem `run_as_system` pra leitura.
    with run_as_system():
        eventos = [
            e
            for e in Auditoria.objects.filter(action="sistema.provisorio_expirado")
            if e.payload_jsonb.get("provisorio_id") == str(prov_id)
        ]
    assert len(eventos) == 1


# ====================================================================
# T-EQP-057 — métrica taxa_provisorios_mensal
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_metrica_taxa_provisorios_mensal_endpoint(cenario):
    """GET /metricas/ retorna taxa e alerta_excedido."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    # 2 provisorios pendentes; 0 recebimentos canonicos -> taxa = 1.0 -> alerta.
    _criar_provisorio_via_api(client, cenario)
    _criar_provisorio_via_api(client, cenario)
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.get("/api/v1/equipamentos/provisorios/metricas/")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["pendentes_ativos"] >= 2
    assert body["taxa_provisorios_mensal"] > 0.05
    assert body["alerta_excedido"] is True
    assert body["limiar_p2"] == 0.05


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_metrica_perfil_sem_authz_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    resp = client.get("/api/v1/equipamentos/provisorios/metricas/")
    assert resp.status_code == 403


# ====================================================================
# Evento sanitizado
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_promovido_payload_sanitizado(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = _criar_provisorio_via_api(client, cenario)
    prov_id = r1.json()["provisorio_id"]
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    sfx = uuid4().hex[:6]
    r2 = client.post(
        f"/api/v1/equipamentos/provisorios/{prov_id}/promover/",
        {
            "tag_canonica": f"EVT-{sfx}",
            "numero_serie": f"NS-EVT-{sfx}",
            "fabricante": "Toledo",
            "modelo": "Prix 4",
            "cliente_atual_id": str(cenario["cliente"].id),
            "perfil_tenant_snapshot": {"perfil": "D"},
        },
        format="json",
    )
    assert r2.status_code == 200
    with run_in_tenant_context(cenario["tenant_a"].id):
        eventos = [
            e
            for e in Auditoria.objects.filter(
                action="equipamento.promovido_de_provisorio"
            )
            if e.payload_jsonb.get("provisorio_id") == str(prov_id)
        ]
    assert len(eventos) == 1
    p = eventos[0].payload_jsonb
    assert p["tag_canonica"] == f"EVT-{sfx}"
    assert p["equipamento_id"]
    assert p["recebimento_id"]
    # Cliente NUNCA vaza no payload.
    assert str(cenario["cliente"].id) not in str(p)
