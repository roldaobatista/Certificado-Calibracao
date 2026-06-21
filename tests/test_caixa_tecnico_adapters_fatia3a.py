"""Adapters reais cross-módulo do caixa_tecnico — testes (Fatia 3a / T-CT-043).

Cobre:
  FotoComprovanteStorageLocal (T-CT-040): EXIF/GPS stripado; foto_hash sobre bytes
    PÓS-strip; HMAC-tenant (cross-tenant → hashes distintos → coexistem; mesmo tenant
    → determinístico); dedup mesmo tenant → IntegrityError no UNIQUE parcial (409);
    tipo inválido → FotoTipoInvalido (422); foto ausente → FotoComprovanteObrigatoria
    (412); salvar idempotente.
  ConsentimentoGpsAdapter (T-CT-041): opt-in vigente / revogado / ausente.
  ColaboradorCaixaAdapter (T-CT-041): e_tecnico com/sem papel; esta_referenciado
    com/sem vínculo (assinatura colaborador_id, tenant_id — porta compartilhada).
  OSReferenciaAdapter (T-CT-042): OS existente / ausente / cross-tenant.

IMPORTANTE: usa --reuse-db (NUNCA --create-db).
"""

from __future__ import annotations

import hashlib
import io
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from PIL import Image
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.caixa_tecnico.colaborador_caixa_adapter import (
    ColaboradorCaixaAdapter,
)
from src.infrastructure.caixa_tecnico.consentimento_gps_adapter import (
    ConsentimentoGpsAdapter,
)
from src.infrastructure.caixa_tecnico.foto_storage import FotoComprovanteStorageLocal
from src.infrastructure.caixa_tecnico.models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    ConsentimentoGpsColaborador as ConsentimentoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    DespesaCaixa as DespesaCaixaModel,
)
from src.infrastructure.caixa_tecnico.os_referencia_adapter import OSReferenciaAdapter
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

_DBS = ["default", "breaker_writer"]
_HASH_V1 = "v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tenant():
    return TenantFactory(perfil_b=True, slug=f"ct-3a-{uuid4().hex[:8]}")


def _jpeg(cor: tuple[int, int, int] = (123, 45, 67)) -> bytes:
    img = Image.new("RGB", (32, 32), cor)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _jpeg_com_exif_gps(cor: tuple[int, int, int] = (200, 50, 50)) -> bytes:
    """JPEG com EXIF (Model + DateTime) + GPS IFD (refs ASCII) embutidos — exercita o strip.

    Usa apenas tags ASCII (Model/DateTime/GPSLatitudeRef/GPSLongitudeRef) — as
    coordenadas RATIONAL do GPS quebram o writer do Pillow nesta versão e não são
    necessárias: o ponto do teste é que o EXIF (carreador do GPS) é removido (D-CT-6).
    """
    img = Image.new("RGB", (48, 48), cor)
    exif = img.getexif()
    exif[0x0110] = "AfereCam"  # Model (IFD0) — sempre persiste no round-trip
    exif[0x0132] = "2026:06:21 10:00:00"  # DateTime
    gps = exif.get_ifd(0x8825)  # GPSInfo IFD
    gps[1] = "S"  # GPSLatitudeRef (ASCII — dado de GPS real, sem rational)
    gps[3] = "W"  # GPSLongitudeRef
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, exif=exif)
    return buf.getvalue()


def _hash_esperado(bytes_limpos: bytes, tenant_id) -> str:
    """Reproduz o cálculo do adapter: HMAC-tenant do sha256-hex dos bytes."""
    digest = hashlib.sha256(bytes_limpos).hexdigest()  # audit-pii-salt: skip -- sha256 de bytes de imagem (binario, nao PII textual); reproduz o calculo do adapter; salt por tenant via HMAC na linha seguinte
    return hashear_pii_com_salt_tenant(digest, tenant_id).split(":", 1)[1]


# ===========================================================================
# FotoComprovanteStorageLocal — T-CT-040
# ===========================================================================


def test_foto_exif_gps_stripado(tmp_path):
    """EXIF (carreador de GPS) é removido no re-encode (D-CT-6 / INV-LGPD-CONSENT-001)."""
    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    original = _jpeg_com_exif_gps()

    exif_orig = Image.open(io.BytesIO(original)).getexif()
    assert len(exif_orig) > 0  # sanidade: EXIF presente no original

    bytes_limpos, _ = storage.validar_e_processar(tenant_id, original, "image/jpeg")

    exif_limpo = Image.open(io.BytesIO(bytes_limpos)).getexif()
    assert len(exif_limpo) == 0  # EXIF removido
    assert dict(exif_limpo.get_ifd(0x8825)) == {}  # GPS IFD vazio


def test_foto_hash_sobre_bytes_pos_strip(tmp_path):
    """foto_hash = HMAC-tenant(sha256(bytes PÓS-strip)) — nunca dos bytes pré-strip."""
    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    original = _jpeg_com_exif_gps()
    bytes_limpos, foto_hash = storage.validar_e_processar(tenant_id, original, "image/jpeg")
    assert foto_hash == _hash_esperado(bytes_limpos, tenant_id)
    assert foto_hash != _hash_esperado(original, tenant_id)


def test_foto_cross_tenant_hashes_distintos(tmp_path):
    """Mesma foto em 2 tenants → foto_hash distinto (HMAC-tenant → coexistem — R12)."""
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    foto = _jpeg((10, 20, 30))
    t1, t2 = uuid4(), uuid4()
    _, h1 = storage.validar_e_processar(t1, foto, "image/jpeg")
    _, h2 = storage.validar_e_processar(t2, foto, "image/jpeg")
    assert h1 != h2


def test_foto_mesmo_tenant_mesma_foto_deterministico(tmp_path):
    """Mesma foto, mesmo tenant → mesmo foto_hash (base do dedup INV-CT-FOTO-DEDUP-001)."""
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    foto = _jpeg((10, 20, 30))
    tid = uuid4()
    _, h1 = storage.validar_e_processar(tid, foto, "image/jpeg")
    _, h2 = storage.validar_e_processar(tid, foto, "image/jpeg")
    assert h1 == h2


def test_foto_tipo_invalido_422(tmp_path):
    """MIME fora da allowlist e imagem corrompida → FotoTipoInvalido (422)."""
    from src.domain.caixa_tecnico.erros import FotoTipoInvalido

    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    with pytest.raises(FotoTipoInvalido) as e1:
        storage.validar_e_processar(tenant_id, _jpeg(), "application/pdf")
    assert e1.value.http_status == 422
    with pytest.raises(FotoTipoInvalido):
        storage.validar_e_processar(tenant_id, b"isto-nao-e-uma-imagem", "image/jpeg")


def test_foto_ausente_412(tmp_path):
    """Bytes vazios → FotoComprovanteObrigatoria (412)."""
    from src.domain.caixa_tecnico.erros import FotoComprovanteObrigatoria

    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    with pytest.raises(FotoComprovanteObrigatoria) as e:
        storage.validar_e_processar(tenant_id, b"", "image/jpeg")
    assert e.value.http_status == 412


def test_foto_salvar_idempotente(tmp_path):
    """salvar 2x → grava 1x (if not exists), mesma URL (D-CT-4/5)."""
    tenant_id = uuid4()
    storage = FotoComprovanteStorageLocal(base_dir=tmp_path)
    bytes_limpos, foto_hash = storage.validar_e_processar(tenant_id, _jpeg(), "image/jpeg")
    url1 = storage.salvar(tenant_id, foto_hash, bytes_limpos)
    url2 = storage.salvar(tenant_id, foto_hash, bytes_limpos)
    assert url1 == url2
    destino = tmp_path / "caixa_tecnico" / str(tenant_id) / foto_hash[:2] / foto_hash
    assert destino.exists()
    assert destino.read_bytes() == bytes_limpos


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_foto_dedup_mesmo_tenant_409():
    """2 despesas pendentes com mesmo (tenant, foto_hash) → IntegrityError (UNIQUE parcial)."""
    tenant = _tenant()
    storage = FotoComprovanteStorageLocal()
    _, foto_hash = storage.validar_e_processar(tenant.id, _jpeg((7, 8, 9)), "image/jpeg")

    with run_in_tenant_context(tenant.id):
        caixa = CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash="t" * 56 + uuid4().hex[:8],
            tecnico_key_id=_HASH_V1,
        )
        DespesaCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            categoria="combustivel",
            tipo="normal",
            valor=5000,
            estado="pendente",
            foto_hash=foto_hash,
            foto_url="http://x/f.jpg",
            data=date.today(),
            client_offline_id="",
        )

    with run_in_tenant_context(tenant.id):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                DespesaCaixaModel.objects.create(
                    tenant=tenant,
                    caixa=caixa,
                    tecnico_referencia_hash=caixa.tecnico_referencia_hash,
                    tecnico_key_id=_HASH_V1,
                    categoria="alimentacao",
                    tipo="normal",
                    valor=3000,
                    estado="pendente",
                    foto_hash=foto_hash,
                    foto_url="http://x/g.jpg",
                    data=date.today(),
                    client_offline_id="",
                )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_foto_cross_tenant_coexiste_no_banco():
    """Mesma foto em 2 tenants → ambas as despesas persistem (constraint é por tenant — R12)."""
    storage = FotoComprovanteStorageLocal()
    foto = _jpeg((9, 9, 9))
    for _ in range(2):
        tenant = _tenant()
        _, foto_hash = storage.validar_e_processar(tenant.id, foto, "image/jpeg")
        with run_in_tenant_context(tenant.id):
            caixa = CaixaTecnicoModel.objects.create(
                tenant=tenant,
                tecnico_referencia_hash="t" * 56 + uuid4().hex[:8],
                tecnico_key_id=_HASH_V1,
            )
            DespesaCaixaModel.objects.create(
                tenant=tenant,
                caixa=caixa,
                tecnico_referencia_hash=caixa.tecnico_referencia_hash,
                tecnico_key_id=_HASH_V1,
                categoria="combustivel",
                tipo="normal",
                valor=5000,
                estado="pendente",
                foto_hash=foto_hash,
                foto_url="http://x/f.jpg",
                data=date.today(),
                client_offline_id="",
            )
            assert DespesaCaixaModel.objects.filter(foto_hash=foto_hash).count() == 1


# ===========================================================================
# ConsentimentoGpsAdapter — T-CT-041
# ===========================================================================


def _cria_consentimento(tenant, colaborador_id, *, revogado: bool = False):
    colaborador_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant.id).split(":", 1)[1]
    with run_in_tenant_context(tenant.id):
        ConsentimentoModel.objects.create(
            tenant=tenant,
            colaborador_referencia_hash=colaborador_hash,
            colaborador_key_id=_HASH_V1,
            vigencia_inicio=datetime.now(UTC) - timedelta(days=2),
            revogado_em=datetime.now(UTC) if revogado else None,
        )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consentimento_vigente():
    tenant = _tenant()
    colaborador_id = uuid4()
    _cria_consentimento(tenant, colaborador_id, revogado=False)
    adapter = ConsentimentoGpsAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.opt_in_vigente(tenant.id, colaborador_id, datetime.now(UTC)) is True


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consentimento_revogado():
    tenant = _tenant()
    colaborador_id = uuid4()
    _cria_consentimento(tenant, colaborador_id, revogado=True)
    adapter = ConsentimentoGpsAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.opt_in_vigente(tenant.id, colaborador_id, datetime.now(UTC)) is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consentimento_ausente():
    tenant = _tenant()
    adapter = ConsentimentoGpsAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.opt_in_vigente(tenant.id, uuid4(), datetime.now(UTC)) is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consentimento_vigente_com_date_puro():
    """Caminho real do use case passa um ``date`` — adapter coage p/ datetime aware (sem naive)."""
    tenant = _tenant()
    colaborador_id = uuid4()
    _cria_consentimento(tenant, colaborador_id, revogado=False)
    adapter = ConsentimentoGpsAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.opt_in_vigente(tenant.id, colaborador_id, date.today()) is True


# ===========================================================================
# ColaboradorCaixaAdapter — T-CT-041
# ===========================================================================


def _cria_colaborador_tecnico(tenant, colaborador_id):
    from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

    with run_in_tenant_context(tenant.id):
        Colaborador.objects.create(
            id=colaborador_id,
            tenant_id=tenant.id,
            nome="Técnico Teste",
            cpf="11111111111",
            email="",
            telefone="",
            vinculo="clt",
            data_admissao=date.today(),
            comissao_default_pct=Decimal("0"),
        )
        ColaboradorPapel.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colaborador_id,
            papel="tecnico",
            data_inicio=date.today(),
            data_fim=None,
            revogado_em=None,
        )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e_tecnico_com_papel():
    tenant = _tenant()
    colaborador_id = uuid4()
    _cria_colaborador_tecnico(tenant, colaborador_id)
    adapter = ColaboradorCaixaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.e_tecnico(tenant.id, colaborador_id) is True


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e_tecnico_sem_papel():
    tenant = _tenant()
    adapter = ColaboradorCaixaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.e_tecnico(tenant.id, uuid4()) is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_esta_referenciado_com_caixa_ativo():
    """Caixa ativo com hash do colaborador → esta_referenciado True (bloqueia hard-delete)."""
    tenant = _tenant()
    colaborador_id = uuid4()
    tecnico_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant.id).split(":", 1)[1]
    with run_in_tenant_context(tenant.id):
        CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )
    adapter = ColaboradorCaixaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.esta_referenciado(colaborador_id, tenant.id) is True


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_esta_referenciado_sem_vinculo():
    tenant = _tenant()
    adapter = ColaboradorCaixaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.esta_referenciado(uuid4(), tenant.id) is False


# ===========================================================================
# OSReferenciaAdapter — T-CT-042
# ===========================================================================


def _cria_os(tenant):
    from src.infrastructure.ordens_servico.models import OS

    chash = uuid4().hex + uuid4().hex  # 64 chars
    with run_in_tenant_context(tenant.id):
        return OS.objects.create(
            tenant_id=tenant.id,
            numero_os=1,
            cliente_id=uuid4(),
            cliente_referencia_hash=chash,
            cliente_key_id="v1",
            estado="rascunho",
            tipo_predominante="calibracao",
            valor_total=Decimal("0"),
            valor_total_atualizado=Decimal("0"),
        )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_existe_os_no_tenant():
    tenant = _tenant()
    os_obj = _cria_os(tenant)
    adapter = OSReferenciaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.existe_os(os_obj.id, tenant.id) is True


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_existe_os_ausente():
    tenant = _tenant()
    adapter = OSReferenciaAdapter()
    with run_in_tenant_context(tenant.id):
        assert adapter.existe_os(uuid4(), tenant.id) is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_existe_os_cross_tenant():
    tenant_a = _tenant()
    tenant_b = _tenant()
    os_a = _cria_os(tenant_a)
    adapter = OSReferenciaAdapter()
    with run_in_tenant_context(tenant_b.id):
        assert adapter.existe_os(os_a.id, tenant_b.id) is False
