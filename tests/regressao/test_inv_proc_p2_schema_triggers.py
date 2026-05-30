"""M7 Fatia 1b (T-PROC-020..027) — drill PG-real de schema + RLS + WORM + porta.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural e o hook não garantem):
- INV-SOFT-002: DELETE físico de procedimento_calibracao RAISE (soft-delete B).
- INV-PROC-003 (WORM Padrão B): campo técnico de PUBLICADO imutável; revogação
  one-shot; RASCUNHO editável.
- INV-PROC-002: UNIQUE documental (tenant, codigo, versao).
- INV-PROC-008: UNIQUE parcial — no máx 1 PUBLICADO vigente por chave natural.
- INV-TENANT: RLS isola procedimento entre tenants.
- Porta vigente_em (ADR-0073): contenção + fail-closed.

GATE-PROC-DRILL-LOCAL. Cada RAISE aborta a transação PG → cada `raises` isolado
na própria transação (run_in_tenant_context).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.infrastructure.metrologia.procedimentos_calibracao import query_service
from src.infrastructure.metrologia.procedimentos_calibracao.models import (
    ProcedimentoCalibracao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELA = "procedimento_calibracao"


def _cria_proc(
    tenant,
    *,
    codigo: str = "PC-MASSA-001",
    grandeza: str = "massa",
    faixa_min: str = "0",
    faixa_max: str = "1000",
    unidade: str = "g",
    estado: str = "PUBLICADO",
    versao: int = 1,
    vigencia_fim=None,
) -> ProcedimentoCalibracao:
    with run_in_tenant_context(tenant.id):
        return ProcedimentoCalibracao.objects.create(
            tenant=tenant,
            codigo=codigo,
            titulo="Calibração de massa",
            grandeza=grandeza,
            faixa_min=Decimal(faixa_min),
            faixa_max=Decimal(faixa_max),
            unidade=unidade,
            metodo_norma="OIML R76",
            tipo_metodo="NORMALIZADO",
            numero_revisao="Rev. 03",
            aprovado_em=timezone.now(),
            aprovado_por_id=uuid4(),
            anexo_pdf_sha256="abc123",
            versao=versao,
            vigente_a_partir=timezone.now(),
            estado=estado,
            vigencia_inicio=timezone.now(),
            vigencia_fim=vigencia_fim,
        )


# =============================================================
# Estrutura — RLS + FORCE + policies
# =============================================================
@pytest.mark.django_db
def test_tabela_m7_tem_rls_force_e_4_policies():
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relkind='r' AND c.relname=%s",
            [TABELA],
        )
        enabled, force = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s", [TABELA])
        n = cur.fetchone()[0]
    assert enabled, "INV-TENANT-001: M7 sem RLS"
    assert force, "INV-TENANT-002: M7 sem FORCE"
    assert n >= 4, "M7 com <4 policies"


# =============================================================
# INV-SOFT-002 — sem DELETE físico
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_soft_002_delete_procedimento_bloqueia():
    tenant = TenantFactory(slug=f"procsoft-{uuid4().hex[:6]}")
    p = _cria_proc(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ProcedimentoCalibracao.objects.filter(id=p.id).delete()


# =============================================================
# INV-PROC-003 — WORM Padrão B
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_proc_003_update_metodo_de_publicado_bloqueia():
    tenant = TenantFactory(slug=f"procw-{uuid4().hex[:6]}")
    p = _cria_proc(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(metodo_norma="OUTRO")


@pytest.mark.django_db(transaction=True)
def test_inv_proc_003_update_faixa_de_publicado_bloqueia():
    tenant = TenantFactory(slug=f"procwf-{uuid4().hex[:6]}")
    p = _cria_proc(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(faixa_max=Decimal("5000"))


@pytest.mark.django_db(transaction=True)
def test_inv_proc_003_rascunho_editavel():
    """RASCUNHO não é congelado — campo técnico muta (só PUBLICADO congela)."""
    tenant = TenantFactory(slug=f"procras-{uuid4().hex[:6]}")
    p = _cria_proc(tenant, estado="RASCUNHO")
    with run_in_tenant_context(tenant.id):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(metodo_norma="REVISADO")
        assert ProcedimentoCalibracao.objects.get(id=p.id).metodo_norma == "REVISADO"


@pytest.mark.django_db(transaction=True)
def test_revogacao_one_shot_e_revogado_congela():
    tenant = TenantFactory(slug=f"procrev-{uuid4().hex[:6]}")
    p = _cria_proc(tenant)
    with run_in_tenant_context(tenant.id):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(
            estado="REVOGADO",
            revogado_em=timezone.now(),
            motivo_revogacao="revogado por revisao normativa 2026",
        )
        assert ProcedimentoCalibracao.objects.get(id=p.id).estado == "REVOGADO"
    # campo técnico de REVOGADO continua congelado (cl. 8.4 retroativo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(metodo_norma="X")
    # re-revogar (revogado_em já preenchido) bloqueia — one-shot
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        ProcedimentoCalibracao.objects.filter(id=p.id).update(revogado_em=timezone.now())


# =============================================================
# INV-PROC-002 — UNIQUE documental (tenant, codigo, versao)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_proc_002_unique_documental():
    tenant = TenantFactory(slug=f"procuq-{uuid4().hex[:6]}")
    _cria_proc(tenant, codigo="PC-X-1", versao=1)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_proc(tenant, codigo="PC-X-1", versao=1)


# =============================================================
# INV-PROC-008 — UNIQUE parcial: no máx 1 PUBLICADO vigente por chave natural
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_proc_008_uma_vigente_por_chave():
    tenant = TenantFactory(slug=f"procov-{uuid4().hex[:6]}")
    # 2 versões PUBLICADO vigentes (vigencia_fim NULL) da MESMA chave natural
    _cria_proc(tenant, codigo="PC-OV-1", versao=1, vigencia_fim=None)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_proc(tenant, codigo="PC-OV-1", versao=2, vigencia_fim=None)


@pytest.mark.django_db(transaction=True)
def test_inv_proc_008_anterior_encerrada_permite_nova_vigente():
    """Encerrando a vigência da v1 (vigencia_fim setado), a v2 vigente passa."""
    tenant = TenantFactory(slug=f"procok-{uuid4().hex[:6]}")
    v1 = _cria_proc(tenant, codigo="PC-OK-1", versao=1, vigencia_fim=None)
    with run_in_tenant_context(tenant.id):
        # encerra v1 (one-shot permitido em PUBLICADO)
        ProcedimentoCalibracao.objects.filter(id=v1.id).update(vigencia_fim=timezone.now())
    p2 = _cria_proc(tenant, codigo="PC-OK-1", versao=2, vigencia_fim=None)
    assert p2.versao == 2


# =============================================================
# INV-TENANT — RLS isola procedimento entre tenants
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_rls_isola_procedimento_cross_tenant():
    ta = TenantFactory(slug=f"proca-{uuid4().hex[:6]}")
    tb = TenantFactory(slug=f"procb-{uuid4().hex[:6]}")
    pa = _cria_proc(ta)
    with run_in_tenant_context(tb.id):
        assert not ProcedimentoCalibracao.objects.filter(id=pa.id).exists()
    with run_in_tenant_context(ta.id):
        assert ProcedimentoCalibracao.objects.filter(id=pa.id).exists()


# =============================================================
# Porta vigente_em (ADR-0073) — contenção + fail-closed
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_porta_vigente_em_contencao():
    tenant = TenantFactory(slug=f"procvig-{uuid4().hex[:6]}")
    _cria_proc(tenant, faixa_min="0", faixa_max="1000", unidade="g")
    agora = timezone.now()
    with run_in_tenant_context(tenant.id):
        dentro = query_service.vigente_em(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=agora,
        )
        assert dentro is not None and dentro.codigo == "PC-MASSA-001"
        fora = query_service.vigente_em(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("900"), faixa_max=Decimal("2000"), unidade="g", data=agora,
        )
        assert fora is None


@pytest.mark.django_db(transaction=True)
def test_porta_vigente_em_sem_procedimento_fail_closed():
    tenant = TenantFactory(slug=f"procno-{uuid4().hex[:6]}")
    with run_in_tenant_context(tenant.id):
        r = query_service.vigente_em(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=timezone.now(),
        )
    assert r is None


@pytest.mark.django_db(transaction=True)
def test_porta_vigente_em_rascunho_nao_resolve():
    """Procedimento em RASCUNHO nunca entra na resolução (só PUBLICADO)."""
    tenant = TenantFactory(slug=f"procrs-{uuid4().hex[:6]}")
    _cria_proc(tenant, estado="RASCUNHO")
    with run_in_tenant_context(tenant.id):
        r = query_service.vigente_em(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=timezone.now(),
        )
    assert r is None
