"""Anti-regressao INV-049 (T-EQP-095 — AC-EQP-001-3 / P-EQP-T3).

`Equipamento.tag` e UNICA por tenant entre equipamentos ATIVOS (TAG
soft-deletado nao conta — UniqueConstraint parcial filtrada por
`deletado_em IS NULL`).

≥3 testes (padrao TST-004): happy + unhappy + cross-tenant.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_cliente_e_equipamento(tenant, tag, ns=""):
    sfx = uuid4().hex[:6]
    ns = ns or f"NSINV049-{sfx}"
    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        return Equipamento.objects.create(
            tenant=tenant,
            tag=tag,
            numero_serie=ns,
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_tag_unica_aceita_primeira(db):
    tenant = TenantFactory(slug=f"inv049-h-{uuid4().hex[:6]}")
    eq = _criar_cliente_e_equipamento(tenant, tag="INV049-TAG-A")
    with run_in_tenant_context(tenant.id):
        contagem = Equipamento.objects.filter(tag="INV049-TAG-A").count()
    assert contagem == 1
    assert eq.tag == "INV049-TAG-A"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_tag_duplicada_no_mesmo_tenant_falha(db):
    tenant = TenantFactory(slug=f"inv049-u-{uuid4().hex[:6]}")
    _criar_cliente_e_equipamento(tenant, tag="INV049-DUP")
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _criar_cliente_e_equipamento(tenant, tag="INV049-DUP", ns="NS-2")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cross_tenant_mesma_tag_em_tenants_distintos_ok(db):
    tenant_a = TenantFactory(slug=f"inv049-a-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv049-b-{uuid4().hex[:6]}")
    eq_a = _criar_cliente_e_equipamento(tenant_a, tag="INV049-X-COMUM")
    eq_b = _criar_cliente_e_equipamento(tenant_b, tag="INV049-X-COMUM")
    assert eq_a.tag == eq_b.tag
    assert eq_a.tenant_id != eq_b.tenant_id
