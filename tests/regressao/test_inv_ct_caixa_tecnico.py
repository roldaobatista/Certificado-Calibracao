"""Testes de regressão de invariante — módulo `caixa_tecnico` (TST-004 / T-CT-057..062).

Uma função por INV crítica, com o INV-ID literal no docstring. Cada teste EXERCE
A BARREIRA REAL e falha se a barreira for removida — não é duplicação cosmética
das fatias 1b/3a/2, é a suíte de regressão rastreável por INV-ID (R do ritual).

INVs cobertas:
  INV-CT-IMUT-001       — reapresentação (rejeitada→pendente) NÃO dispara anti-mutação;
                          validada→qualquer dispara RAISE (trigger PG `BEFORE UPDATE`).
  INV-CT-FOTO-DEDUP-001 — foto idêntica cross-tenant coexiste (HMAC-tenant); mesma foto
                          no mesmo tenant → IntegrityError (UNIQUE parcial); foto_hash é
                          calculado sobre bytes PÓS-EXIF-strip.
  INV-CT-IDEMP-001      — batch parcial per-item: 2 itens ruins não derrubam os 3 bons.
  INV-CT-PRESTACAO-001  — fechamento concorrente: advisory lock garante 1 só prestação.
  INV-LGPD-CONSENT-001  — EXIF (carreador de GPS) é removido nos bytes armazenados.

Refs: tasks.md §"Testes de INV adicionais" (TL-CT-15); plan §7/§8.
IMPORTANTE: usa ``--reuse-db`` (NUNCA ``--create-db``).
"""

from __future__ import annotations

import base64
import hashlib
import io
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.db import Error as DjangoDBError
from django.db import IntegrityError, transaction
from PIL import Image
from rest_framework.test import APIClient
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.caixa_tecnico.foto_storage import FotoComprovanteStorageLocal
from src.infrastructure.caixa_tecnico.models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    DespesaCaixa as DespesaCaixaModel,
)
from src.infrastructure.caixa_tecnico.models import (
    PrestacaoContasCaixa as PrestacaoContasCaixaModel,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

_DBS = ["default", "breaker_writer"]
_HASH_V1 = "v1"


# ---------------------------------------------------------------------------
# Helpers de imagem (molde fatia 3a)
# ---------------------------------------------------------------------------


def _jpeg(seed: object) -> bytes:
    """JPEG real e único por ``seed`` (foto_hash distinto, evita colisão no UNIQUE)."""
    h = hashlib.sha256(str(seed).encode()).digest()
    img = Image.new("RGB", (4, 3))
    img.putdata([(h[i % 32], h[(i + 7) % 32], h[(i + 17) % 32]) for i in range(12)])
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _jpeg_com_exif_gps() -> bytes:
    """JPEG com EXIF (Model + DateTime) + GPS IFD (refs ASCII) — exercita o strip."""
    img = Image.new("RGB", (48, 48), (200, 50, 50))
    exif = img.getexif()
    exif[0x0110] = "AfereCam"  # Model (IFD0)
    exif[0x0132] = "2026:06:21 10:00:00"  # DateTime
    gps = exif.get_ifd(0x8825)  # GPSInfo IFD
    gps[1] = "S"  # GPSLatitudeRef
    gps[3] = "W"  # GPSLongitudeRef
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, exif=exif)
    return buf.getvalue()


def _hash_esperado(bytes_limpos: bytes, tenant_id) -> str:
    """Reproduz o cálculo do adapter: HMAC-tenant do sha256-hex dos bytes."""
    digest = hashlib.sha256(
        bytes_limpos
    ).hexdigest()  # audit-pii-salt: skip -- sha256 de bytes de imagem (binário); salt por tenant via HMAC na linha seguinte
    return hashear_pii_com_salt_tenant(digest, tenant_id).split(":", 1)[1]


# ---------------------------------------------------------------------------
# Helpers de banco / API (molde fatia 2)
# ---------------------------------------------------------------------------


def _tenant():
    return TenantFactory(perfil_b=True, slug=f"ct-inv-{uuid4().hex[:8]}")


def _cria_caixa(tenant, tecnico_hash: str | None = None) -> CaixaTecnicoModel:
    if tecnico_hash is None:
        tecnico_hash = "t" * 56 + uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        return CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )


def _cria_despesa(tenant, caixa, *, estado: str, foto_hash: str, **kw) -> DespesaCaixaModel:
    campos = {
        "tenant": tenant,
        "caixa": caixa,
        "tecnico_referencia_hash": caixa.tecnico_referencia_hash,
        "tecnico_key_id": _HASH_V1,
        "categoria": "combustivel",
        "tipo": "normal",
        "valor": 5000,
        "estado": estado,
        "foto_hash": foto_hash,
        "foto_url": "http://x/f.jpg",
        "data": date.today(),
        "client_offline_id": "",
    }
    campos.update(kw)
    with run_in_tenant_context(tenant.id):
        return DespesaCaixaModel.objects.create(**campos)


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


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=True, slug=f"ct-inv-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@ctinv.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _post(client, url, payload, key=None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


def _item_lote(**kw):
    base = {
        "foto_base64": base64.b64encode(_jpeg(uuid4().hex)).decode(),
        "foto_mime": "image/jpeg",
        "categoria": "combustivel",
        "valor_centavos": 3000,
        "data": date.today().isoformat(),
    }
    base.update(kw)
    return base


URL_SYNC = "/api/v1/caixa-tecnico/despesas/sync-lote/"
URL_FECHAR = "/api/v1/caixa-tecnico/prestacoes/fechar/"


# ===========================================================================
# T-CT-057 — INV-CT-IMUT-001
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reapresentacao_nao_dispara_trigger():
    """INV-CT-IMUT-001: rejeitada→pendente é UPDATE legítimo (não dispara); validada→X RAISE."""
    tenant = _tenant()
    caixa = _cria_caixa(tenant)

    # Reapresentação: rejeitada → pendente NÃO dispara o trigger anti-mutação (R3 / TL-CT-05).
    rejeitada = _cria_despesa(
        tenant,
        caixa,
        estado="rejeitada",
        foto_hash="r" * 64,
        motivo_rejeicao="m" * 30,
        rejeitado_em=datetime.now(UTC),
    )
    with run_in_tenant_context(tenant.id):
        n = DespesaCaixaModel.objects.filter(id=rejeitada.id).update(estado="pendente")
        assert n == 1
        assert DespesaCaixaModel.objects.get(id=rejeitada.id).estado == "pendente"

    # Despesa validada (WORM): qualquer UPDATE dispara RAISE no trigger.
    validada = _cria_despesa(
        tenant,
        caixa,
        estado="validada",
        foto_hash="v" * 64,
        validado_em=datetime.now(UTC),
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        with pytest.raises(DjangoDBError):
            DespesaCaixaModel.objects.filter(id=validada.id).update(estado="rejeitada")


# ===========================================================================
# T-CT-058 — INV-CT-FOTO-DEDUP-001 (cross-tenant coexiste + dedup mesmo tenant)
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_foto_identica_cross_tenant_coexiste():
    """INV-CT-FOTO-DEDUP-001: mesma foto em 2 tenants coexiste; 2ª no mesmo tenant → 409."""
    storage = FotoComprovanteStorageLocal()
    foto = _jpeg("dedup-fixa")  # MESMA foto nos dois tenants

    # Cross-tenant: hashes distintos (HMAC-tenant) → ambas as despesas persistem (R12).
    for _ in range(2):
        tenant = _tenant()
        _, foto_hash = storage.validar_e_processar(tenant.id, foto, "image/jpeg")
        caixa = _cria_caixa(tenant)
        _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)
        with run_in_tenant_context(tenant.id):
            assert DespesaCaixaModel.objects.filter(foto_hash=foto_hash).count() == 1

    # Mesmo tenant, mesma foto 2ª vez (status ativo) → IntegrityError (UNIQUE parcial).
    tenant = _tenant()
    _, foto_hash = storage.validar_e_processar(tenant.id, foto, "image/jpeg")
    caixa = _cria_caixa(tenant)
    _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)
    with run_in_tenant_context(tenant.id), transaction.atomic():
        with pytest.raises(IntegrityError):
            _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)


# ===========================================================================
# T-CT-059 — INV-CT-FOTO-DEDUP-001 (foto_hash sobre bytes pós-strip)
# ===========================================================================


def test_foto_hash_sobre_bytes_pos_strip(tmp_path):
    """INV-CT-FOTO-DEDUP-001 / ADV-CT-04: foto_hash = HMAC(sha256(bytes PÓS-strip)), nunca pré."""
    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    original = _jpeg_com_exif_gps()
    bytes_limpos, foto_hash = storage.validar_e_processar(tenant_id, original, "image/jpeg")
    assert foto_hash == _hash_esperado(bytes_limpos, tenant_id)
    assert foto_hash != _hash_esperado(original, tenant_id)


# ===========================================================================
# T-CT-060 — INV-CT-IDEMP-001 (batch parcial per-item)
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_batch_parcial_per_item():
    """INV-CT-IDEMP-001: lote 5 (3 bons + 2 com foto inválida) → 207 com 3 OK + 2 erro; banco=3."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    itens = [
        _item_lote(client_offline_id=f"ok-{uuid4()}"),
        {**_item_lote(), "foto_base64": "!!!invalido!!!"},
        _item_lote(client_offline_id=f"ok-{uuid4()}"),
        {**_item_lote(), "foto_base64": "@@@tambem-ruim@@@"},
        _item_lote(client_offline_id=f"ok-{uuid4()}"),
    ]
    payload = {"caixa_id": str(caixa.id), "colaborador_id": str(uuid4()), "itens": itens}
    r = _post(client, URL_SYNC, payload)
    assert r.status_code == 207, r.content

    resultados = r.json()["resultados"]
    assert len(resultados) == 5
    sucessos = [x for x in resultados if x["sucesso"]]
    falhas = [x for x in resultados if not x["sucesso"]]
    assert len(sucessos) == 3
    assert len(falhas) == 2

    # Banco tem EXATAMENTE 3 despesas (as 2 ruins não persistiram — atomicidade per-item).
    with run_in_tenant_context(c["tenant"].id):
        assert DespesaCaixaModel.objects.filter(caixa=caixa).count() == 3


# ===========================================================================
# T-CT-061 — INV-CT-PRESTACAO-001 (advisory lock)
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_fechamento_concorrente_advisory_lock():
    """INV-CT-PRESTACAO-001: 2 fechamentos concorrentes → 1 prestação só (advisory lock)."""
    import threading

    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    hoje = date.today()
    payload = {
        "caixa_id": str(caixa.id),
        "periodo_de": (hoje - timedelta(days=30)).isoformat(),
        "periodo_ate": (hoje - timedelta(days=1)).isoformat(),
    }
    resultados: list[int] = []

    def _fechar():
        client_t = APIClient()
        _autenticar(client_t, c["admin"], c["tenant"])
        resultados.append(_post(client_t, URL_FECHAR, payload).status_code)

    t1 = threading.Thread(target=_fechar)
    t2 = threading.Thread(target=_fechar)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exatamente 1 fechou (201); banco com no máximo 1 prestação (NUNCA 2 — barreira do lock).
    with run_in_tenant_context(c["tenant"].id):
        count = PrestacaoContasCaixaModel.objects.filter(caixa=caixa).count()
    assert count == 1
    assert resultados.count(201) == 1


# ===========================================================================
# T-CT-062 — INV-LGPD-CONSENT-001 (EXIF GPS não vaza)
# ===========================================================================


def test_exif_gps_nao_vaza(tmp_path):
    """INV-LGPD-CONSENT-001 / ADV-CT-03: bytes armazenados não carregam EXIF (carreador de GPS)."""
    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    original = _jpeg_com_exif_gps()

    exif_orig = Image.open(io.BytesIO(original)).getexif()
    assert len(exif_orig) > 0  # sanidade: EXIF (com GPS IFD) presente no original

    bytes_limpos, _ = storage.validar_e_processar(tenant_id, original, "image/jpeg")
    exif_limpo = Image.open(io.BytesIO(bytes_limpos)).getexif()
    assert len(exif_limpo) == 0  # EXIF removido
    assert dict(exif_limpo.get_ifd(0x8825)) == {}  # GPS IFD vazio
