"""M6 Fatia 1b (T-ECMC-010..017) — drill PG-real de schema + RLS + WORM + porta.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural e o hook não garantem):
- INV-SOFT-002: DELETE físico de escopo_cmc RAISE (soft-delete B).
- INV-ECMC-003 (WORM Padrão B): campo metrológico de CONFIRMADO/REVOGADO imutável;
  revogação one-shot; campo não-protegido (revision) muta.
- INV-TENANT: RLS isola escopo entre tenants.
- INV-ECMC-001: UNIQUE chave natural (nulls_distinct=False).
- Porta cobre()/cmc_para() (ADR-0073/0074): contenção + menor CMC, fail-closed.

GATE-ECMC-DRILL-LOCAL. Padrão TST-004 (happy + unhappy). Cada RAISE aborta a
transação PG → cada `raises` isolado na própria transação (run_in_tenant_context).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.domain.metrologia.escopos_cmc import cobertura
from src.infrastructure.metrologia.escopos_cmc import query_service
from src.infrastructure.metrologia.escopos_cmc.models import EscopoCMC
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELAS_M6 = ["escopo_cmc", "escopo_extraido"]


def _cria_escopo(
    tenant,
    *,
    grandeza: str = "massa",
    faixa_min: str = "0",
    faixa_max: str = "1000",
    unidade: str = "g",
    cmc_valor: str = "0.001",
    estado: str = "CONFIRMADO",
    versao: int = 1,
    rbc: bool = True,
    procedimento_id=None,
) -> EscopoCMC:
    with run_in_tenant_context(tenant.id):
        return EscopoCMC.objects.create(
            tenant=tenant,
            grandeza=grandeza,
            faixa_min=Decimal(faixa_min),
            faixa_max=Decimal(faixa_max),
            unidade=unidade,
            cmc_forma="ABSOLUTA",
            cmc_valor=Decimal(cmc_valor),
            cmc_unidade=unidade,
            rbc_acreditado=rbc,
            versao=versao,
            vigente_a_partir=timezone.now(),
            estado=estado,
            origem="MANUAL",
            vigencia_inicio=timezone.now(),
            procedimento_id=procedimento_id,
        )


# =============================================================
# Estrutura — RLS + FORCE + policies + grants
# =============================================================
@pytest.mark.django_db
def test_duas_tabelas_m6_tem_rls_force_e_4_policies():
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace = n.oid "
            "WHERE n.nspname='public' AND c.relkind='r' AND c.relname = ANY(%s)",
            [TABELAS_M6],
        )
        estado = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        cur.execute(
            "SELECT tablename, COUNT(*) FROM pg_policies WHERE schemaname='public' "
            "AND tablename = ANY(%s) GROUP BY tablename",
            [TABELAS_M6],
        )
        policies = dict(cur.fetchall())
    assert not (set(TABELAS_M6) - set(estado)), "Tabelas M6 ausentes em PG"
    assert all(estado[t][0] for t in TABELAS_M6), "INV-TENANT-001: M6 sem RLS"
    assert all(estado[t][1] for t in TABELAS_M6), "INV-TENANT-002: M6 sem FORCE"
    assert all(policies.get(t, 0) >= 4 for t in TABELAS_M6), "M6 com <4 policies"


# =============================================================
# INV-SOFT-002 — sem DELETE físico do escopo
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_soft_002_delete_escopo_bloqueia():
    tenant = TenantFactory(slug=f"ecmcsoft-{uuid4().hex[:6]}")
    escopo = _cria_escopo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EscopoCMC.objects.filter(id=escopo.id).delete()


# =============================================================
# INV-ECMC-003 — WORM Padrão B
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_ecmc_003_update_cmc_de_confirmado_bloqueia():
    tenant = TenantFactory(slug=f"ecmcw-{uuid4().hex[:6]}")
    escopo = _cria_escopo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EscopoCMC.objects.filter(id=escopo.id).update(cmc_valor=Decimal("0.999"))


@pytest.mark.django_db(transaction=True)
def test_inv_ecmc_003_update_faixa_de_confirmado_bloqueia():
    tenant = TenantFactory(slug=f"ecmcwf-{uuid4().hex[:6]}")
    escopo = _cria_escopo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EscopoCMC.objects.filter(id=escopo.id).update(faixa_max=Decimal("5000"))


@pytest.mark.django_db(transaction=True)
def test_inv_ecmc_003_campo_nao_protegido_muta():
    """revision bump (CAS) passa — só campos metrológicos são congelados."""
    tenant = TenantFactory(slug=f"ecmcnp-{uuid4().hex[:6]}")
    escopo = _cria_escopo(tenant)
    with run_in_tenant_context(tenant.id):
        EscopoCMC.objects.filter(id=escopo.id).update(revision=1)
        assert EscopoCMC.objects.get(id=escopo.id).revision == 1


@pytest.mark.django_db(transaction=True)
def test_revogacao_one_shot_e_revogado_congela():
    tenant = TenantFactory(slug=f"ecmcrev-{uuid4().hex[:6]}")
    escopo = _cria_escopo(tenant)
    # revogação CONFIRMADO -> REVOGADO passa (transação limpa)
    with run_in_tenant_context(tenant.id):
        EscopoCMC.objects.filter(id=escopo.id).update(
            estado="REVOGADO",
            revogado_em=timezone.now(),
            motivo_revogacao="revogado por supervisao CGCRE 2026",
        )
        assert EscopoCMC.objects.get(id=escopo.id).estado == "REVOGADO"
    # campo metrológico de REVOGADO continua congelado (cl. 8.4 retroativo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EscopoCMC.objects.filter(id=escopo.id).update(cmc_valor=Decimal("0.5"))
    # re-revogar (revogado_em já preenchido) bloqueia — one-shot
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EscopoCMC.objects.filter(id=escopo.id).update(revogado_em=timezone.now())


# =============================================================
# INV-TENANT — RLS isola escopo entre tenants
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_rls_isola_escopo_cross_tenant():
    tenant_a = TenantFactory(slug=f"ecmca-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"ecmcb-{uuid4().hex[:6]}")
    escopo_a = _cria_escopo(tenant_a)
    with run_in_tenant_context(tenant_b.id):
        assert not EscopoCMC.objects.filter(id=escopo_a.id).exists()
    with run_in_tenant_context(tenant_a.id):
        assert EscopoCMC.objects.filter(id=escopo_a.id).exists()


# =============================================================
# INV-ECMC-001 — UNIQUE chave natural (nulls_distinct=False)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_ecmc_001_unique_chave_natural_com_proc_null():
    tenant = TenantFactory(slug=f"ecmcuq-{uuid4().hex[:6]}")
    _cria_escopo(tenant, versao=1, procedimento_id=None)
    # mesma chave (proc_id NULL ainda colide — nulls_distinct=False)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_escopo(tenant, versao=1, procedimento_id=None)


# =============================================================
# Porta cobre()/cmc_para() (ADR-0073/0074)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_porta_cobre_contencao_total():
    tenant = TenantFactory(slug=f"ecmccob-{uuid4().hex[:6]}")
    _cria_escopo(tenant, faixa_min="0", faixa_max="1000", unidade="g")
    agora = timezone.now()
    with run_in_tenant_context(tenant.id):
        ok, reason = query_service.cobre(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=agora,
        )
        assert ok and reason == cobertura.REASON_OK
        # faixa fora do escopo -> bloqueia
        nok, reason2 = query_service.cobre(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("900"), faixa_max=Decimal("2000"), unidade="g", data=agora,
        )
        assert not nok and reason2 == cobertura.REASON_FORA_DO_ESCOPO


@pytest.mark.django_db(transaction=True)
def test_porta_cobre_sem_escopo_fail_closed():
    tenant = TenantFactory(slug=f"ecmcnoesc-{uuid4().hex[:6]}")
    with run_in_tenant_context(tenant.id):
        ok, reason = query_service.cobre(
            tenant_id=tenant.id, grandeza="massa",
            faixa_min=Decimal("10"), faixa_max=Decimal("20"), unidade="g", data=timezone.now(),
        )
    assert not ok and reason == cobertura.REASON_FORA_DO_ESCOPO


@pytest.mark.django_db(transaction=True)
def test_porta_cmc_para_pega_menor_entre_metodos():
    tenant = TenantFactory(slug=f"ecmccmc-{uuid4().hex[:6]}")
    # 2 métodos (procedimento_id distinto) na mesma faixa, CMC diferente
    _cria_escopo(tenant, cmc_valor="0.002", procedimento_id=uuid4())
    _cria_escopo(tenant, cmc_valor="0.001", procedimento_id=uuid4())
    with run_in_tenant_context(tenant.id):
        cmc = query_service.cmc_para(
            tenant_id=tenant.id, grandeza="massa", ponto=Decimal("500"), data=timezone.now(),
        )
    assert cmc == Decimal("0.001")  # menor CMC vigente (NIT-DICLA-012)
