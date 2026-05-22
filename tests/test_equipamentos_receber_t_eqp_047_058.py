"""T-EQP-047+048+050+052+058+059 — recebimento de equipamento (US-EQP-006).

Cobre:
- AC-EQP-006-1: POST /recebimentos/ happy integro sem foto + happy com
  anomalia + decisao + foto. Estado inicial `recebido_pendente_inspecao`.
- AC-EQP-006-2: condicao != integro exige decisao + justificativa
  >=30 + anti-PII (INV-EQP-ANOM-002); ausente -> 400.
- AC-EQP-006-3b / T-EQP-050: transicao status_fluxo_lab valida via
  trigger PG (matriz de 9 fases + 2 alt); transicao invalida -> 409.
- AC-EQP-006-5 / T-EQP-052: FotoStorageService EXIF strip + SHA256 +
  storage_key UUID; MIME invalido -> 400; tamanho >5MB -> 400.
- T-EQP-058 (P-EQP-S3): trigger PG imutabilidade foto_sha256 +
  foto_storage_key pos-INSERT.
- T-EQP-059 (P-EQP-S3): evento equipamento.recebido payload inclui
  foto_sha256.
- Anomalia anti-PII -> 400.
- AC-EQP-006-5 (P-EQP-A6): aviso UX canonico anti-drift.
- RLS cross-tenant invisivel.
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
    EquipamentoRecebimento,
    EquipamentoRecebimentoFoto,
)
from src.infrastructure.equipamentos.services_foto_storage import (
    _hash_binario_foto,
)
from src.infrastructure.equipamentos.validators import (
    AVISO_UX_FOTO_RECEBIMENTO_VERSAO_CANONICA,
    aviso_ux_foto_recebimento,
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


def _gerar_jpeg_bytes(largura: int = 50, altura: int = 50) -> bytes:
    img = Image.new("RGB", (largura, altura), color=(120, 130, 140))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _gerar_jpeg_com_exif() -> bytes:
    img = Image.new("RGB", (40, 40), color=(200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, exif=b"Exif\x00\x00" + b"\x00" * 100)
    return buf.getvalue()


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"rec-a-{sfx}", nome_fantasia="Lab Rec A")
    admin_a = UsuarioFactory(email=f"adm-rec-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-rec-{sfx}@e.local")
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
            nome="Cliente Rec",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant_a,
            tag=f"REC-{sfx}",
            numero_serie=f"NS-REC-{sfx}",
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


# ====================================================================
# T-EQP-047 — happy paths
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_receber_integro_sem_foto_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["status_fluxo_lab"] == "recebido_pendente_inspecao"
    assert body["foto_storage_key"] == ""
    assert body["foto_sha256"] == ""
    with run_in_tenant_context(cenario["tenant_a"].id):
        rec = EquipamentoRecebimento.objects.get(id=body["recebimento_id"])
    assert rec.condicao_visual_chegada == "integro"
    assert rec.decisao_apos_anomalia == ""


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_receber_com_anomalia_e_decisao_e_foto_happy(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    jpeg_bytes = _gerar_jpeg_bytes()
    from django.core.files.uploadedfile import SimpleUploadedFile

    foto_file = SimpleUploadedFile(
        "recebimento.jpg", jpeg_bytes, content_type="image/jpeg"
    )
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {
            "condicao_visual_chegada": "amassado",
            "anomalias_observadas": "Painel frontal apresenta amassado leve no canto direito.",
            "decisao_apos_anomalia": "aceitar_com_ressalva",
            "justificativa_decisao": (
                "Calibracao tecnicamente viavel; amassado nao afeta celula "
                "de carga. Cliente avisado verbalmente."
            ),
            "foto": foto_file,
        },
        format="multipart",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["status_fluxo_lab"] == "recebido_pendente_inspecao"
    assert body["foto_storage_key"]
    assert len(body["foto_sha256"]) == 64
    with run_in_tenant_context(cenario["tenant_a"].id):
        foto = EquipamentoRecebimentoFoto.objects.get(
            recebimento_id=body["recebimento_id"]
        )
    binario_persistido = bytes(foto.conteudo_bytes)
    sha_calc = _hash_binario_foto(binario_persistido)
    assert sha_calc == body["foto_sha256"]
    assert foto.mime_type == "image/jpeg"


# ====================================================================
# T-EQP-052 — FotoStorageService EXIF strip + validações
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_exif_strip_remove_metadados(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    jpeg_com_exif = _gerar_jpeg_com_exif()
    from django.core.files.uploadedfile import SimpleUploadedFile

    foto_file = SimpleUploadedFile(
        "exif.jpg", jpeg_com_exif, content_type="image/jpeg"
    )
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro", "foto": foto_file},
        format="multipart",
    )
    assert resp.status_code == 200, resp.content
    with run_in_tenant_context(cenario["tenant_a"].id):
        foto = EquipamentoRecebimentoFoto.objects.get(
            recebimento_id=resp.json()["recebimento_id"]
        )
    binario_persistido = bytes(foto.conteudo_bytes)
    # PIL JPEG re-encode remove EXIF; marker `Exif\x00\x00` nao deve
    # aparecer no inicio do binario.
    assert b"Exif\x00\x00" not in binario_persistido[:200]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_foto_mime_invalido_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    from django.core.files.uploadedfile import SimpleUploadedFile

    foto_file = SimpleUploadedFile(
        "x.gif", b"GIF89a binario falso", content_type="image/gif"
    )
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro", "foto": foto_file},
        format="multipart",
    )
    assert resp.status_code == 400
    assert resp.json().get("codigo") == "foto_invalida"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_foto_tamanho_excedido_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    from django.core.files.uploadedfile import SimpleUploadedFile

    bytes_pesados = b"\xff\xd8\xff\xe0" + (b"A" * (6 * 1024 * 1024))
    foto_file = SimpleUploadedFile(
        "grande.jpg", bytes_pesados, content_type="image/jpeg"
    )
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro", "foto": foto_file},
        format="multipart",
    )
    assert resp.status_code == 400
    assert "5MB" in resp.json()["detail"] or "5242880" in resp.json()["detail"]


# ====================================================================
# AC-EQP-006-2 — validacoes
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_anomalia_sem_decisao_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {
            "condicao_visual_chegada": "amassado",
            "anomalias_observadas": "leve amassado",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_anomalia_com_decisao_mas_justificativa_curta_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {
            "condicao_visual_chegada": "amassado",
            "decisao_apos_anomalia": "prosseguir",
            "justificativa_decisao": "curto",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_anomalias_observadas_com_pii_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {
            "condicao_visual_chegada": "amassado",
            "anomalias_observadas": "Recebido de Joao Silva da Costa via balcao.",
            "decisao_apos_anomalia": "prosseguir",
            "justificativa_decisao": (
                "Cliente notificado e autorizou o prosseguimento da calibracao."
            ),
        },
        format="json",
    )
    assert resp.status_code == 400


# ====================================================================
# T-EQP-050 — transicionar status_fluxo_lab
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transicionar_valida_recebido_para_inspecao(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    rec_id = r1.json()["recebimento_id"]
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/transicionar/",
        {"status_alvo": "em_inspecao_visual"},
        format="json",
    )
    assert r2.status_code == 200, r2.content
    assert r2.json()["status_fluxo_lab"] == "em_inspecao_visual"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transicionar_invalida_pula_fase_409(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    rec_id = r1.json()["recebimento_id"]
    client.defaults["HTTP_IDEMPOTENCY_KEY"] = str(uuid4())
    r2 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/{rec_id}/transicionar/",
        {"status_alvo": "em_calibracao"},
        format="json",
    )
    assert r2.status_code == 409


# ====================================================================
# T-EQP-058 — trigger PG imutabilidade foto_sha256
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_foto_sha256_imutavel_trigger(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.db import connection

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro", "foto": foto},
        format="multipart",
    )
    rec_id = r1.json()["recebimento_id"]
    fake_sha = "0" * 64
    with run_in_tenant_context(cenario["tenant_a"].id):
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE equipamentos_recebimento SET foto_sha256=%s WHERE id=%s",
                    [fake_sha, str(rec_id)],
                )
        except Exception as exc:
            msg = str(exc)
        else:
            msg = ""
    assert "foto_sha256 imutavel" in msg or "T-EQP-058" in msg


# ====================================================================
# T-EQP-059 — evento equipamento.recebido com foto_sha256
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_recebido_payload_inclui_foto_sha256(cenario):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    foto = SimpleUploadedFile(
        "p.jpg", _gerar_jpeg_bytes(), content_type="image/jpeg"
    )
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro", "foto": foto},
        format="multipart",
    )
    rec_id = r1.json()["recebimento_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        eventos = [
            e
            for e in Auditoria.objects.filter(action="equipamento.recebido")
            if e.payload_jsonb.get("recebimento_id") == str(rec_id)
        ]
    assert len(eventos) == 1
    assert eventos[0].payload_jsonb["tem_foto"] is True
    assert len(eventos[0].payload_jsonb["foto_sha256"]) == 64
    assert str(cenario["cliente"].id) not in str(eventos[0].payload_jsonb)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_evento_notificacao_cliente_aguardando_disparado(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    r1 = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {
            "condicao_visual_chegada": "lacre_violado",
            "anomalias_observadas": "Lacre violado entre embalagem e equipamento.",
            "decisao_apos_anomalia": "contatar_cliente_aguardando",
            "justificativa_decisao": (
                "Antes de prosseguir, contatar cliente pra confirmar se "
                "houve manuseio entre envio e chegada."
            ),
        },
        format="json",
    )
    rec_id = r1.json()["recebimento_id"]
    with run_in_tenant_context(cenario["tenant_a"].id):
        eventos = [
            e
            for e in Auditoria.objects.filter(
                action="equipamento.notificacao_cliente_aguardando"
            )
            if e.payload_jsonb.get("recebimento_id") == str(rec_id)
        ]
    assert len(eventos) == 1


# ====================================================================
# Authz + RLS
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_perfil_sem_authz_403(cenario):
    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rls_recebimento_cross_tenant_invisivel(cenario):
    sfx = uuid4().hex[:6]
    tenant_b = TenantFactory(slug=f"rec-b-{sfx}")
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/recebimentos/",
        {"condicao_visual_chegada": "integro"},
        format="json",
    )
    with run_in_tenant_context(tenant_b.id):
        visiveis = EquipamentoRecebimento.objects.count()
    assert visiveis == 0


# ====================================================================
# T-EQP-052 (P-EQP-A6) — anti-drift do aviso UX da foto
# ====================================================================


def test_aviso_ux_foto_versao_canonica_helper():
    texto = aviso_ux_foto_recebimento()
    assert "Sem face/imagem do cliente" in texto
    assert "LGPD art. 5º I" in texto
    assert "REMOVIDOS automaticamente" in texto
    import pytest as _pt

    with _pt.raises(ValueError):
        aviso_ux_foto_recebimento("v9.99-2030-12-31")


def test_aviso_ux_foto_versao_canonica_bate_doc():
    from pathlib import Path

    doc = Path("docs/conformidade/equipamentos/aviso-foto-recebimento.md")
    assert doc.exists(), f"Doc canônico esperado em {doc}"
    conteudo = doc.read_text(encoding="utf-8")
    assert AVISO_UX_FOTO_RECEBIMENTO_VERSAO_CANONICA in conteudo
