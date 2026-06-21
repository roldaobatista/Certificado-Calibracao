"""PDF da prestação de contas — testes Fatia 3c (T-CT-056).

Cobre (plan §7 / Verificação 3c):
  Unitário (gerador puro, sem banco):
    - ``gerar_pdf_prestacao`` → bytes não-vazios começando com ``%PDF``;
    - ``montar_html_prestacao`` → dados financeiros presentes (R$, categoria, OS);
    - GPS AUSENTE: despesa COM coordenada GPS não vaza lat/lng no HTML (AC-CT-002-7).
  E2E (action GET ``/prestacoes/{id}/pdf/``):
    - técnico-próprio → 200 + ``Content-Type: application/pdf``;
    - outro técnico → 403;
    - cross-tenant → 404 (RLS escopa o repo);
    - financeiro/admin (não-técnico) → 200 (vê tudo).

IMPORTANTE: usa ``--reuse-db`` (NUNCA ``--create-db``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.domain.caixa_tecnico.entities import Adiantamento, Despesa, PrestacaoContas
from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    DirecaoPrestacao,
    EstadoAdiantamento,
    EstadoDespesa,
    MeioEntrega,
    TipoDespesa,
)
from src.domain.caixa_tecnico.value_objects import (
    Coordenada,
    Dinheiro,
    Periodo,
    ReferenciaPIIAnonimizavel,
)
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.caixa_tecnico.models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    DespesaCaixa as DespesaCaixaModel,
)
from src.infrastructure.caixa_tecnico.models import (
    PrestacaoContasCaixa as PrestacaoContasCaixaModel,
)
from src.infrastructure.caixa_tecnico.pdf_prestacao import (
    gerar_pdf_prestacao,
    montar_html_prestacao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

_DBS = ["default", "breaker_writer"]
_HASH_V1 = "v1"


# ---------------------------------------------------------------------------
# Helpers de domínio puro (sem banco)
# ---------------------------------------------------------------------------


def _ref(hash_original: str = "f" * 64) -> ReferenciaPIIAnonimizavel:
    return ReferenciaPIIAnonimizavel(
        uuid_atual_id=None, hash_original=hash_original, key_id=_HASH_V1
    )


def _prestacao_dominio(
    *,
    tenant_id=None,
    caixa_id=None,
    tecnico_hash: str = "f" * 64,
) -> PrestacaoContas:
    return PrestacaoContas(
        prestacao_id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        caixa_id=caixa_id or uuid4(),
        tecnico_referencia=_ref(tecnico_hash),
        periodo=Periodo(de=date(2026, 6, 1), ate=date(2026, 6, 30)),
        total_adiantado=Dinheiro(50000, "BRL"),
        total_despesas_validadas=Dinheiro(32345, "BRL"),
        saldo_final=Dinheiro(17655, "BRL"),
        direcao=DirecaoPrestacao.TENANT_DEVE,
        fechada_em=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
        criado_em=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
        observacoes="prestação de junho",
    )


def _despesa_dominio(*, com_gps: bool = False, valor_centavos: int = 32345) -> Despesa:
    return Despesa(
        despesa_id=uuid4(),
        tenant_id=uuid4(),
        caixa_id=uuid4(),
        tecnico_referencia=_ref(),
        categoria=CategoriaDespesa.COMBUSTIVEL,
        tipo=TipoDespesa.NORMAL,
        valor=Dinheiro(valor_centavos, "BRL"),
        estado=EstadoDespesa.VALIDADA,
        foto_hash="a" * 64,
        foto_url="http://x/f.jpg",
        data=date(2026, 6, 15),
        criado_em=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        revision=1,
        descricao="abastecimento posto BR",
        os_id=uuid4(),
        coordenada=Coordenada(lat=-15.601234, lng=-56.097654) if com_gps else None,
    )


def _adiantamento_dominio(valor_centavos: int = 50000) -> Adiantamento:
    return Adiantamento(
        adiantamento_id=uuid4(),
        tenant_id=uuid4(),
        caixa_id=uuid4(),
        tecnico_referencia=_ref(),
        valor=Dinheiro(valor_centavos, "BRL"),
        estado=EstadoAdiantamento.ENTREGUE,
        meio=MeioEntrega.PIX,
        solicitado_em=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        criado_em=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        revision=2,
        entregue_em=datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
    )


# ===========================================================================
# Unitário — gerador puro
# ===========================================================================


def test_gerar_pdf_bytes_validos():
    """gerar_pdf_prestacao → bytes não-vazios começando com ``%PDF``."""
    prestacao = _prestacao_dominio()
    pdf = gerar_pdf_prestacao(
        prestacao, [_despesa_dominio()], [_adiantamento_dominio()], tenant_nome="Balanças Solution"
    )
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
    assert pdf[:5] == b"%PDF-"


def test_html_tem_dados_financeiros():
    """HTML carrega resumo financeiro + categoria + OS vinculada (AC-CT-006-2)."""
    prestacao = _prestacao_dominio()
    despesa = _despesa_dominio()
    html = montar_html_prestacao(
        prestacao, [despesa], [_adiantamento_dominio()], tenant_nome="Balanças Solution"
    )
    assert "Balanças Solution" in html
    assert "R$ 500,00" in html  # total adiantado
    assert "R$ 323,45" in html  # total despesas / valor da despesa
    assert "R$ 176,55" in html  # saldo final
    assert "combustivel" in html
    assert str(despesa.os_id) in html  # OS vinculada
    assert "Tenant deve ao técnico" in html  # direção legível


def test_html_sem_gps_mesmo_com_coordenada():
    """Despesa COM coordenada GPS → lat/lng NÃO vazam no HTML (AC-CT-002-7 / INV-LGPD-CONSENT-001)."""
    prestacao = _prestacao_dominio()
    despesa_com_gps = _despesa_dominio(com_gps=True)
    assert despesa_com_gps.coordenada is not None  # sanidade: a despesa tem GPS

    html = montar_html_prestacao(prestacao, [despesa_com_gps], [], tenant_nome="X")

    # Nenhum fragmento de coordenada pode aparecer no relatório fiscal.
    assert "-15.60" not in html
    assert "-56.09" not in html
    assert "15.601234" not in html
    assert "56.097654" not in html
    for termo in ("gps", "coordenada", "latitude", "longitude"):
        assert termo not in html.lower()


def test_saldo_negativo_preserva_sinal():
    """direcao=tecnico_deve → saldo negativo formatado com sinal (R$ -...)."""
    prestacao = PrestacaoContas(
        prestacao_id=uuid4(),
        tenant_id=uuid4(),
        caixa_id=uuid4(),
        tecnico_referencia=_ref(),
        periodo=Periodo(de=date(2026, 6, 1), ate=date(2026, 6, 30)),
        total_adiantado=Dinheiro(10000, "BRL"),
        total_despesas_validadas=Dinheiro(15000, "BRL"),
        saldo_final=Dinheiro(-5000, "BRL"),
        direcao=DirecaoPrestacao.TECNICO_DEVE,
        fechada_em=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
        criado_em=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
    )
    html = montar_html_prestacao(prestacao, [], [], tenant_nome="X")
    assert "R$ -50,00" in html
    assert "Técnico deve ao tenant" in html


# ===========================================================================
# E2E — action GET /prestacoes/{id}/pdf/
# ===========================================================================

URL_PDF = "/api/v1/caixa-tecnico/prestacoes/{}/pdf/"


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


def _cpf() -> str:
    return str(uuid4().int)[-11:]


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=True, slug=f"ct-pdf-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@ctpdf.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _cria_colaborador_tecnico(tenant, usuario):
    """Cria Colaborador (papel técnico) vinculado ao usuário e retorna seu colaborador_id."""
    from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel

    colaborador_id = uuid4()
    with run_in_tenant_context(tenant.id):
        Colaborador.objects.create(
            id=colaborador_id,
            tenant_id=tenant.id,
            nome="Técnico de Campo",
            cpf=_cpf(),
            email="",
            telefone="",
            vinculo="clt",
            data_admissao=date(2026, 1, 1),
            comissao_default_pct=Decimal("0"),
            usuario_id=usuario.id,
        )
        ColaboradorPapel.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colaborador_id,
            papel="tecnico",
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            revogado_em=None,
        )
    return colaborador_id


def _cria_caixa(tenant, tecnico_hash: str) -> CaixaTecnicoModel:
    with run_in_tenant_context(tenant.id):
        return CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )


def _cria_prestacao(tenant, caixa) -> PrestacaoContasCaixaModel:
    with run_in_tenant_context(tenant.id):
        return PrestacaoContasCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            periodo_de=date(2026, 6, 1),
            periodo_ate=date(2026, 6, 30),
            total_adiantado=50000,
            total_despesas_validadas=32345,
            saldo_final=17655,
            direcao=DirecaoPrestacao.TENANT_DEVE.value,
            fechada_em=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
        )


def _cria_despesa_validada(tenant, caixa, *, com_gps: bool = False):
    with run_in_tenant_context(tenant.id):
        DespesaCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            categoria="combustivel",
            tipo="normal",
            valor=32345,
            estado="validada",
            foto_hash=uuid4().hex + uuid4().hex,
            foto_url="http://x/f.jpg",
            data=date(2026, 6, 15),
            gps_lat=Decimal("-15.6012340") if com_gps else None,
            gps_lng=Decimal("-56.0976540") if com_gps else None,
            client_offline_id="",
            validado_em=datetime(2026, 6, 16, 10, 0, tzinfo=UTC),
        )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_pdf_tecnico_proprio_200():
    """Técnico dono do caixa → 200 + application/pdf + corpo %PDF."""
    c = _cenario()
    tenant = c["tenant"]
    tecnico = UsuarioFactory(email=f"tec-{uuid4().hex[:8]}@ctpdf.local")
    UsuarioPerfilTenantFactory(usuario=tecnico, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(tecnico.id, tenant.id)
    colaborador_id = _cria_colaborador_tecnico(tenant, tecnico)
    tecnico_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant.id).split(":", 1)[1]
    caixa = _cria_caixa(tenant, tecnico_hash)
    _cria_despesa_validada(tenant, caixa, com_gps=True)
    prestacao = _cria_prestacao(tenant, caixa)

    client = APIClient()
    _autenticar(client, tecnico, tenant)
    r = client.get(URL_PDF.format(prestacao.id))

    assert r.status_code == 200, getattr(r, "content", b"")[:300]
    assert r["Content-Type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"
    assert "prestacao-" in r["Content-Disposition"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_pdf_outro_tecnico_403():
    """Técnico de OUTRO caixa → 403 (não é o dono)."""
    c = _cenario()
    tenant = c["tenant"]
    # dono do caixa/prestação
    dono = UsuarioFactory(email=f"dono-{uuid4().hex[:8]}@ctpdf.local")
    UsuarioPerfilTenantFactory(usuario=dono, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(dono.id, tenant.id)
    dono_col = _cria_colaborador_tecnico(tenant, dono)
    dono_hash = hashear_pii_com_salt_tenant(str(dono_col), tenant.id).split(":", 1)[1]
    caixa = _cria_caixa(tenant, dono_hash)
    prestacao = _cria_prestacao(tenant, caixa)

    # outro técnico (caixa diferente)
    outro = UsuarioFactory(email=f"outro-{uuid4().hex[:8]}@ctpdf.local")
    UsuarioPerfilTenantFactory(usuario=outro, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(outro.id, tenant.id)
    _cria_colaborador_tecnico(tenant, outro)

    client = APIClient()
    _autenticar(client, outro, tenant)
    r = client.get(URL_PDF.format(prestacao.id))
    assert r.status_code == 403, getattr(r, "content", b"")[:300]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_pdf_financeiro_nao_tecnico_200():
    """Usuário sem vínculo de colaborador (financeiro/admin) → 200 (vê tudo)."""
    c = _cenario()
    tenant = c["tenant"]
    dono = UsuarioFactory(email=f"dono2-{uuid4().hex[:8]}@ctpdf.local")
    UsuarioPerfilTenantFactory(usuario=dono, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(dono.id, tenant.id)
    dono_col = _cria_colaborador_tecnico(tenant, dono)
    dono_hash = hashear_pii_com_salt_tenant(str(dono_col), tenant.id).split(":", 1)[1]
    caixa = _cria_caixa(tenant, dono_hash)
    prestacao = _cria_prestacao(tenant, caixa)

    client = APIClient()
    _autenticar(client, c["admin"], tenant)  # admin não tem Colaborador
    r = client.get(URL_PDF.format(prestacao.id))
    assert r.status_code == 200, getattr(r, "content", b"")[:300]
    assert r["Content-Type"] == "application/pdf"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_pdf_cross_tenant_404():
    """Prestação de outro tenant → 404 (RLS escopa o repo)."""
    c1 = _cenario()
    caixa = _cria_caixa(c1["tenant"], "h" * 56 + uuid4().hex[:8])
    prestacao = _cria_prestacao(c1["tenant"], caixa)

    c2 = _cenario()  # tenant diferente
    client = APIClient()
    _autenticar(client, c2["admin"], c2["tenant"])
    r = client.get(URL_PDF.format(prestacao.id))
    assert r.status_code == 404, getattr(r, "content", b"")[:300]
