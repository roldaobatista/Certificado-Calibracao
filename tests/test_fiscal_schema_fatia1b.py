"""Frente fiscal/NFS-e — Fatia 1b (T-FIS-020..023): schema PG-real.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural não garante):
- RLS FORCE + 4 policies + isolamento cross-tenant (INV-TENANT-001/002 / INV-FIS-006).
- INV-FIS-008: DELETE físico de nota_fiscal_servico RAISE (retenção fiscal).
- INV-FIS-004 (WORM Padrão B / D-FIS-4): campo probatório imutável RAISE; `status`
  transiciona OK; `cancelado_em` one-shot.
- INV-FIS-005: UNIQUE de negócio (tenant, origem_id, versao).

Cada RAISE aborta a transação PG → cada cenário em teste isolado (TST-004).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.infrastructure.fiscal.models import NotaFiscalServico
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELA = "nota_fiscal_servico"


def _cria_nota(
    tenant,
    *,
    origem_id=None,
    versao: int = 1,
    status: str = "AUTHORIZED",
    cancelado_em=None,
) -> NotaFiscalServico:
    with run_in_tenant_context(tenant.id):
        return NotaFiscalServico.objects.create(
            tenant=tenant,
            origem_id=origem_id or uuid4(),
            versao=versao,
            status=status,
            tipo_servico="calibracao",
            perfil_no_evento="A",
            valor_centavos=25000,
            cliente_referencia_hash="ref-hash-abc",
            snapshot_hash="v01$deadbeef",
            tipo_acreditacao_vinculo="RBC",
            certificado_id=uuid4(),
            emitido_em=timezone.now(),
            cancelado_em=cancelado_em,
        )


# === estrutura ===


@pytest.mark.django_db
def test_rls_force_e_4_policies() -> None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relname=%s",
            [TABELA],
        )
        enabled, forced = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [TABELA])
        n_pol = cur.fetchone()[0]
    assert enabled, "INV-TENANT-001: fiscal sem RLS"
    assert forced, "INV-TENANT-002: fiscal sem FORCE"
    assert n_pol >= 4, f"fiscal com <4 policies ({n_pol})"


# === RLS cross-tenant (INV-FIS-006) ===


@pytest.mark.django_db(transaction=True)
def test_rls_isola_nota_entre_tenants() -> None:
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    nota_a = _cria_nota(tenant_a)
    # Tenant B NÃO enxerga a nota do tenant A.
    with run_in_tenant_context(tenant_b.id):
        assert not NotaFiscalServico.objects.filter(id=nota_a.id).exists()
    # Tenant A enxerga a própria.
    with run_in_tenant_context(tenant_a.id):
        assert NotaFiscalServico.objects.filter(id=nota_a.id).exists()


# === WORM: block-delete (INV-FIS-008) ===


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_raise() -> None:
    tenant = TenantFactory()
    nota = _cria_nota(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NotaFiscalServico.objects.filter(id=nota.id).delete()


# === WORM: campo probatório imutável (INV-FIS-004) ===


@pytest.mark.django_db(transaction=True)
def test_valor_imutavel_raise() -> None:
    tenant = TenantFactory()
    nota = _cria_nota(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NotaFiscalServico.objects.filter(id=nota.id).update(valor_centavos=999)


@pytest.mark.django_db(transaction=True)
def test_snapshot_hash_imutavel_raise() -> None:
    tenant = TenantFactory()
    nota = _cria_nota(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NotaFiscalServico.objects.filter(id=nota.id).update(snapshot_hash="v01$outro")


# === WORM: status transiciona (D-FIS-4 — mutável) ===


@pytest.mark.django_db(transaction=True)
def test_status_transiciona_ok() -> None:
    tenant = TenantFactory()
    nota = _cria_nota(tenant, status="AUTHORIZED", cancelado_em=None)
    with run_in_tenant_context(tenant.id):
        n = NotaFiscalServico.objects.filter(id=nota.id).update(
            status="CANCELED",
            cancelado_em=timezone.now(),
            motivo_cancelamento="cancelamento de teste com mais de trinta caracteres ok",
        )
    assert n == 1


# === WORM: cancelado_em one-shot ===


@pytest.mark.django_db(transaction=True)
def test_cancelado_em_one_shot_raise() -> None:
    tenant = TenantFactory()
    nota = _cria_nota(tenant, status="CANCELED", cancelado_em=timezone.now())
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NotaFiscalServico.objects.filter(id=nota.id).update(cancelado_em=timezone.now())


# === UNIQUE de negócio (INV-FIS-005) ===


@pytest.mark.django_db(transaction=True)
def test_unique_origem_versao_raise() -> None:
    tenant = TenantFactory()
    origem = uuid4()
    _cria_nota(tenant, origem_id=origem, versao=1)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_nota(tenant, origem_id=origem, versao=1)
