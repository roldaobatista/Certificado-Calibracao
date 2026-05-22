"""Anti-regressao INV-EQP-001 (T-EQP-090 — AC-EQP-001-7 / P-EQP-T4).

`perfil_tenant_snapshot` no `Equipamento` e IMUTAVEL pos-INSERT:
trigger PG `equipamento_perfil_snapshot_imutavel_check` bloqueia
qualquer UPDATE direto. Promocoes legitimas usam funcao SECURITY
DEFINER `promover_perfil_equipamento_snapshot` (T-EQP-009) que setta
GUC local `app.perfil_promocao_permitida='1'`.

≥3 testes (padrao TST-004): happy + unhappy + cross-tenant.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import DatabaseError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _cria_equipamento(tenant, perfil="D"):
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome=f"Cli {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        return Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV001-{sfx}",
            numero_serie=f"NSI001-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": perfil},
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_snapshot_persistido_no_insert(db):
    tenant = TenantFactory(slug=f"inv001-h-{uuid4().hex[:6]}")
    eq = _cria_equipamento(tenant, perfil="D")
    with run_in_tenant_context(tenant.id):
        eq_db = Equipamento.objects.get(id=eq.id)
    assert eq_db.perfil_tenant_snapshot["perfil"] == "D"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_update_direto_bloqueado(db):
    tenant = TenantFactory(slug=f"inv001-u-{uuid4().hex[:6]}")
    eq = _cria_equipamento(tenant, perfil="D")
    with run_in_tenant_context(tenant.id), pytest.raises(
        DatabaseError, match=r"perfil_tenant_snapshot"
    ):
        Equipamento.objects.filter(id=eq.id).update(
            perfil_tenant_snapshot={"perfil": "A"}
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cross_tenant_update_nao_alcanca_outro(db):
    """RLS + trigger: tenant A nao pode ver equipamento de tenant B,
    portanto sequer dispara o trigger de imutabilidade do outro tenant.
    """
    tenant_a = TenantFactory(slug=f"inv001-ca-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv001-cb-{uuid4().hex[:6]}")
    eq_b = _cria_equipamento(tenant_b, perfil="D")

    with run_in_tenant_context(tenant_a.id):
        # Tenant A nao enxerga o equipamento de B (RLS).
        assert not Equipamento.objects.filter(id=eq_b.id).exists()
        # UPDATE no contexto de A nao alcanca linha de B.
        afetadas = Equipamento.objects.filter(id=eq_b.id).update(
            perfil_tenant_snapshot={"perfil": "A"}
        )
    assert afetadas == 0

    # Snapshot original em B permanece.
    with run_in_tenant_context(tenant_b.id):
        eq_b_atual = Equipamento.objects.get(id=eq_b.id)
    assert eq_b_atual.perfil_tenant_snapshot["perfil"] == "D"
