"""Cliente — modelo (INV-024 dedup + INV-036 CNPJ unico + RLS).

Cobertura UNHAPPY-PATH obrigatoria (drill F-A 2026-05-18 — bug GRAVE #5):
para cada policy/constraint, ha teste que prova que tentativa ilegitima e
bloqueada (pytest.raises), nao so o caminho feliz.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.db.utils import ProgrammingError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.mark.django_db(transaction=True)
def test_cliente_pj_persiste_e_volta():
    """Happy path PJ — cria, salva, le."""
    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        c = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Empresa Teste LTDA",
        )
        assert c.id is not None
        achado = Cliente.objects.get(id=c.id)
        assert achado.documento == "11222333000181"


@pytest.mark.django_db(transaction=True)
def test_cliente_pf_persiste_e_volta():
    """Happy path PF — CPF."""
    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        c = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PF,
            documento="52998224725",
            nome="Joao Teste",
        )
        assert c.documento == "52998224725"


@pytest.mark.django_db(transaction=True)
def test_cliente_pj_alfanumerico_persiste():
    """ADR-0017 — CNPJ com letras no boundary novo."""
    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        c = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="12ABC34501DE35",
            nome="Empresa Alfa LTDA",
        )
        assert c.documento == "12ABC34501DE35"


@pytest.mark.django_db(transaction=True)
def test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita():
    """UNHAPPY — INV-024: 2o cliente com mesmo CPF/CNPJ no mesmo tenant = IntegrityError."""
    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Primeiro",
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Cliente.objects.create(
                    tenant=tenant,
                    tipo_pessoa=TipoPessoa.PJ,
                    documento="11222333000181",
                    nome="Duplicado",
                )


@pytest.mark.django_db(transaction=True)
def test_inv_024_mesmo_documento_tenants_diferentes_eh_OK():
    """HAPPY — mesmo CNPJ em tenants diferentes deve passar (isolamento)."""
    tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
    tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")

    with run_in_tenant_context(tenant_a.id):
        Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Em A",
        )

    with run_in_tenant_context(tenant_b.id):
        # Mesmo CNPJ em outro tenant — permitido
        Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Em B",
        )


@pytest.mark.django_db(transaction=True)
def test_inv_tenant_001_rls_bloqueia_insert_fora_do_active_tenant():
    """UNHAPPY — INV-TENANT-001: INSERT com tenant_id != active_tenant_id deve falhar."""
    tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
    tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")

    # active_tenant = A; tenta inserir cliente do tenant B = bloqueado pela policy INSERT
    with run_in_tenant_context(tenant_a.id):
        with pytest.raises(ProgrammingError):
            with transaction.atomic():
                Cliente.objects.create(
                    tenant=tenant_b,
                    tipo_pessoa=TipoPessoa.PJ,
                    documento="33000167000101",
                    nome="Tentativa de injecao cross-tenant",
                )


@pytest.mark.django_db(transaction=True)
def test_cliente_clean_rejeita_cnpj_invalido():
    """Boundary validation via clean() — DV errado nao deve passar."""
    from django.core.exceptions import ValidationError

    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    c = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000199",  # DV errado
        nome="X",
    )
    with pytest.raises(ValidationError):
        c.clean()


@pytest.mark.django_db(transaction=True)
def test_cliente_clean_rejeita_cpf_invalido():
    from django.core.exceptions import ValidationError

    tenant = TenantFactory(slug=f"cli-{uuid4().hex[:8]}")
    c = Cliente(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PF,
        documento="52998224726",  # DV errado
        nome="X",
    )
    with pytest.raises(ValidationError):
        c.clean()
