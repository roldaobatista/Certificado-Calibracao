"""Cliente — isolamento cross-tenant (INV-TENANT-001/002/003).

UNHAPPY paths explicitos: tenant B nao ve cliente de tenant A.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_tenant_001_cliente_de_a_nao_eh_visivel_em_b():
    tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
    tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")

    with run_in_tenant_context(tenant_a.id):
        c_a = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente em A",
        )

    with run_in_tenant_context(tenant_b.id):
        # Filtro do ORM ja restrige por tenant; mas a RLS no banco eh quem
        # garante de verdade — testamos os 2 jeitos abaixo.
        assert (
            Cliente.objects.filter(id=c_a.id).count() == 0
        ), "VAZAMENTO: cliente do tenant A apareceu na sessao do tenant B"
        assert Cliente.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_tenant_001_count_em_b_ignora_clientes_de_a():
    tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
    tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")

    with run_in_tenant_context(tenant_a.id):
        for _ in range(3):
            # CNPJs validos diferentes — usamos so um conjunto
            pass
        Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="A1",
        )
        Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="33000167000101",
            nome="A2",
        )

    with run_in_tenant_context(tenant_b.id):
        # Insere 1 em B
        Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",  # mesmo CNPJ que A1 — permitido
            nome="B1",
        )
        # B so ve a sua linha — 1, nao 3
        assert Cliente.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_tenant_001_usuario_multi_tenant_ve_a_e_b_mas_nao_c():
    tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
    tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")
    tenant_c = TenantFactory(slug=f"c-{uuid4().hex[:8]}")

    with run_in_tenant_context(tenant_a.id):
        Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="A",
        )
    with run_in_tenant_context(tenant_b.id):
        Cliente.objects.create(
            tenant=tenant_b,
            tipo_pessoa=TipoPessoa.PJ,
            documento="33000167000101",
            nome="B",
        )
    with run_in_tenant_context(tenant_c.id):
        Cliente.objects.create(
            tenant=tenant_c,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="C",
        )

    # Simular middleware setando lista [A, B]
    from django.db import transaction as django_tx
    from src.infrastructure.multitenant.connection import (
        setar_contexto_pg_na_conexao,
    )

    with django_tx.atomic():
        setar_contexto_pg_na_conexao(
            tenant_ids=[tenant_a.id, tenant_b.id],
            active_tenant=tenant_a.id,
            usuario_id=None,
        )
        nomes = set(Cliente.objects.values_list("nome", flat=True))
        assert nomes == {"A", "B"}, f"Usuario multi-tenant deveria ver so A e B; viu {nomes}"
