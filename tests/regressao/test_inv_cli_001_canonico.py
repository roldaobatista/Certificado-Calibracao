"""INV-CLI-001 — identidade canônica de Cliente.

Spec Marco 1 §3 item 9: suíte anti-regressão `tests/regressao/inv_cli_*.py`
com happy + unhappy ANTES do fechamento — pré-condição de segurabilidade
(ADR-0019 + AUDIT-07 R-CLI-01).

INV-CLI-001 (REGRAS-INEGOCIAVEIS): default `cliente_canonico_id=self`,
trigger PG valida transição self → vencedor_vivo_mesmo_tenant, cap=10 hops
no resolver. Trigger + hook + suite property-based formam defesa em
profundidade.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db.utils import ProgrammingError
from src.infrastructure.clientes.canonico import (
    IdentidadeCanonicaCircular,
    resolver_cliente_canonico,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_cliente(tenant, doc, nome) -> Cliente:
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento=doc,
        nome=nome,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


@pytest.mark.django_db(transaction=True)
def test_inv_cli_001_happy_default_aponta_pra_si_proprio(db):
    """Happy — cliente novo tem `cliente_canonico_id == id` (default)."""
    tenant = TenantFactory(slug=f"inv1-h-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        c = _criar_cliente(tenant, "11222333000181", "PJ Canônico Happy")
    assert c.cliente_canonico_id == c.id


@pytest.mark.django_db(transaction=True)
def test_inv_cli_001_unhappy_update_canonico_para_cliente_de_outro_tenant_bloqueado(db):
    """Unhappy — trigger PG bloqueia UPDATE `cliente_canonico_id` apontando pra cliente de outro tenant."""
    ta = TenantFactory(slug=f"inv1-u-a-{uuid4().hex[:6]}")
    tb = TenantFactory(slug=f"inv1-u-b-{uuid4().hex[:6]}")
    with run_in_tenant_context(ta.id):
        ca = _criar_cliente(ta, "11222333000181", "Cliente A")
    with run_in_tenant_context(tb.id):
        cb = _criar_cliente(tb, "11222333000181", "Cliente B Mesmo doc outro tenant")
    # Tentar setar canonico do A → B (outro tenant) viola trigger
    with run_in_tenant_context(ta.id):
        with pytest.raises((ProgrammingError, Exception)):
            Cliente.all_objects.filter(id=ca.id).update(cliente_canonico_id=cb.id)


@pytest.mark.django_db(transaction=True)
def test_inv_cli_001_resolver_cap_10_levanta_em_ciclo(db):
    """Unhappy — resolver levanta IdentidadeCanonicaCircular se cadeia tem ciclo."""
    tenant = TenantFactory(slug=f"inv1-r-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        c1 = _criar_cliente(tenant, "11222333000181", "C1")
        c2 = _criar_cliente(tenant, "33000167000101", "C2")
        # Cria ciclo c1 → c2 → c1 (defesa em profundidade contra bug)
        Cliente.all_objects.filter(id=c1.id).update(cliente_canonico_id=c2.id)
        Cliente.all_objects.filter(id=c2.id).update(cliente_canonico_id=c1.id)
        with pytest.raises(IdentidadeCanonicaCircular):
            resolver_cliente_canonico(c1.id)
