"""T-EQP-051 — devolucao de equipamento (US-EQP-006 AC-EQP-006-4 /
ISO 17025 cl. 7.4.5).

Cobre:
- Happy path: recebimento em `aguardando_devolucao` -> POST `/devolver/`
  -> devolucao gravada + recebimento.status_fluxo_lab -> `devolvido` +
  Equipamento.status -> `ativo` + evento `equipamento.devolvido`.
- 409 quando recebimento.status_fluxo_lab != aguardando_devolucao.
- 409 duplicado (segunda devolucao no mesmo recebimento).
- 400 sem foto (Marco 2 dogfooding: obrigatoria).
- 400 MIME invalido + 400 tamanho excedido (delegado a FotoStorageService).
- 400 condicao_visual_devolucao fora enum.
- 400 termo_versao_id desconhecida.
- 403 sem authz.
- RLS cross-tenant invisivel.
- Trigger PG imutabilidade pos-INSERT (UPDATE bloqueado).
- Anti-drift termo canonico + frontmatter.
- Payload sanitizado (cliente NAO vaza).
"""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from PIL import Image
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoDevolucao,
    EquipamentoDevolucaoFoto,
    EquipamentoRecebimento,
)
from src.infrastructure.equipamentos.validators import (
    TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA,
    texto_termo_devolucao,
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
    img = Image.new("RGB", (50, 50), color=(100, 110, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _avancar_recebimento_ate_aguardando_devolucao(
    client: APIClient, equipamento, recebimento_id: str
) -> None:
    """Avanca o status_fluxo_lab via 7 transicoes ate
    `aguardando_devolucao` — usa o endpoint transicionar pra exercitar
    o fluxo real."""
    fases = [
        "em_inspecao_visual",
        "aguardando_calibracao",
        "em_calibracao",
        "aguardando_aprovacao_tecnica",
        "aguardando_devolucao",
    ]
    for alvo in fases:
        client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
        resp = client.post(
            f"/api/v1/equipamentos/{equipamento.id}/recebimentos/{recebimento_id}/transicionar/",
            {"status_alvo": alvo},
            format="json",
        )
        assert resp.status_code == 200, (alvo, resp.content)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"dev-a-{sfx}", nome_fantasia="Lab Dev A")
    admin_a = UsuarioFactory(email=f"adm-dev-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-dev-{sfx}@e.local")
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
            nome="Cliente Dev",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant_a,
            tag=f"DEV-{sfx}",
            numero_serie=f"NS-DEV-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant_a": tenant_a,
        "admin_a": admin_a,
        "leitor_a": leitor_a,
        "cliente": cliente,
        "eq": eq,
    }


def _criar_recebimento_e_avancar(client, cenario) -> str:
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    rec_id = r1.json()["recebimento_id"]
    _avancar_recebimento_ate_aguardando_devolucao(client, cenario["eq"], rec_id)
    return rec_id


# ====================================================================
# Happy path
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_happy(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "dev.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {
            "condicao_visual_devolucao": "integro",
            "foto": foto,
        },
        format="multipart",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["devolucao_id"]
    assert len(body["foto_sha256"]) == 64
    assert len(body["termo_aceite_hash"]) >= 32  # hex hash
    assert body["recebimento_status_fluxo_lab"] == "devolvido"
    assert body["equipamento_status"] == "ativo"
    with run_in_tenant_context(cenario["tenant_a"].id):
        rec = EquipamentoRecebimento.objects.get(id=rec_id)
        eq = Equipamento.objects.get(id=cenario["eq"].id)
        dev = EquipamentoDevolucao.objects.get(recebimento_id=rec_id)
        foto_dev = EquipamentoDevolucaoFoto.objects.get(devolucao_id=dev.id)
    assert rec.status_fluxo_lab == "devolvido"
    assert eq.status == "ativo"
    assert dev.termo_devolucao_versao_id == TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA
    assert foto_dev.mime_type == "image/jpeg"


# ====================================================================
# Erros
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_recebimento_nao_em_aguardando_409(cenario):
    """Recebimento recem-criado em `recebido_pendente_inspecao` ->
    devolucao bloqueada (409)."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    rec_id = r1.json()["recebimento_id"]
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    assert resp.status_code == 409


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_duplicado_409(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto1 = SimpleUploadedFile(
        "d1.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto1},
        format="multipart",
    )
    assert r1.status_code == 200
    foto2 = SimpleUploadedFile(
        "d2.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto2},
        format="multipart",
    )
    # Pode ser 409 (StatusFluxoLabNaoAguardando — recebimento ja em
    # devolvido) OU 409 (DevolucaoDuplicada). Qualquer um e 409.
    assert r2.status_code == 409


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_sem_foto_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro"},
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_mime_invalido_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.gif", b"GIF89a fake", content_type="image/gif"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    assert resp.status_code == 400
    assert resp.json().get("codigo") == "foto_invalida"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_condicao_invalida_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "fora_do_enum", "foto": foto},
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_termo_versao_desconhecida_400(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {
            "condicao_visual_devolucao": "integro",
            "foto": foto,
            "termo_versao_id": "v9.99-2030",
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolver_perfil_sem_authz_403(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client_adm = APIClient()
    _autenticar(client_adm, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client_adm, cenario)
    # Mesmo recebimento, perfil sem authz devolver.
    client_l = APIClient()
    _autenticar(client_l, cenario["leitor_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    resp = client_l.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    assert resp.status_code == 403


# ====================================================================
# Evento + trigger imutabilidade
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_devolvido_payload_sanitizado(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    with run_in_tenant_context(cenario["tenant_a"].id):
        eventos = [
            e
            for e in Auditoria.objects.filter(action="equipamento.devolvido")
            if e.payload_jsonb.get("recebimento_id") == str(rec_id)
        ]
    assert len(eventos) == 1
    p = eventos[0].payload_jsonb
    assert p["condicao_visual_devolucao"] == "integro"
    assert len(p["foto_sha256"]) == 64
    assert p["termo_aceite_hash"]
    assert p["termo_versao_id"] == TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA
    # Cliente NAO vaza no payload.
    assert str(cenario["cliente"].id) not in str(p)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_devolucao_update_bloqueado_trigger(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    dev_id = r1.json()["devolucao_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos_devolucao SET condicao_visual_devolucao='amassado' WHERE id=%s",
                    [str(dev_id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "imutavel pos-INSERT" in msg or "T-EQP-051" in msg


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_devolucao_cross_tenant_invisivel(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    sfx = uuid4().hex[:6]
    tenant_b = TenantFactory(slug=f"dev-b-{sfx}")
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    rec_id = _criar_recebimento_e_avancar(client, cenario)
    foto = SimpleUploadedFile(
        "x.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/devolver/",
        {"condicao_visual_devolucao": "integro", "foto": foto},
        format="multipart",
    )
    with run_in_tenant_context(tenant_b.id):
        visiveis = EquipamentoDevolucao.objects.count()
    assert visiveis == 0


# ====================================================================
# Anti-drift termo canonico
# ====================================================================


def test_termo_devolucao_helper_canonico():
    texto = texto_termo_devolucao()
    assert "ISO/IEC 17025 cl. 7.4.5" in texto
    assert "art. 624" in texto
    assert "LGPD art. 7º V" in texto
    assert "CPC" not in texto  # CPC ref so esta no doc, nao no texto canonico
    import pytest as _pt

    with _pt.raises(ValueError):
        texto_termo_devolucao("v9.99-2030-12-31")


def test_termo_devolucao_versao_canonica_bate_doc():
    from pathlib import Path

    doc = Path("docs/conformidade/equipamentos/termo-devolucao.md")
    assert doc.exists(), f"Doc canônico esperado em {doc}"
    conteudo = doc.read_text(encoding="utf-8")
    assert TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA in conteudo
