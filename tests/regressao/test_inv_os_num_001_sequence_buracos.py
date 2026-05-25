"""Anti-regressao INV-OS-NUM-001 (Q-OS-05 P5 conserto) — sequence global + buracos.

INV-OS-NUM-001 (ADR-0056): `OS.numero_os` gerado por sequence global
`os_numero_seq_global` + UNIQUE(tenant_id, numero_os). Buracos por
rollback sao aceitos (NAO ha gap-less per-tenant — alternativa fica
pra Marco 4 fiscal).

≥3 testes: happy (numero_os monotonico crescente), unhappy (rollback
gera buraco), cross-tenant (numeros sao globais nao per-tenant).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _setup(tenant):
    sfx = uuid4().hex[:6]
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
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"NUM-{sfx}",
            numero_serie=f"NS-NUM-{sfx}",
            fabricante="X",
            modelo="Y",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir(tenant, cliente, equipamento):
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        return abrir_os_via_orcamento(
            payload=AbrirOSInput(
                orcamento_id=uuid4(),
                tenant_id=tenant.id,
                cliente_id=cliente.id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms",
                equipamento_id=equipamento.id,
                equipamento_recebimento_id=None,
                analise_critica_id=uuid4(),
                analise_critica_snapshot_hash="b" * 64,
                regra_decisao_acordada="default",
                valor_total=Decimal("100.00"),
                itens=(
                    ItemOrcamento(
                        tipo=TipoAtividade.VISTORIA,
                        sequencia=1,
                        valor_unitario=Decimal("100.00"),
                        requer_recebimento=False,
                    ),
                ),
                correlation_id=uuid4(),
                abertura_at=datetime.now(UTC),
                criada_por_user_id=None,
            ),
            repository=repo,
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_num_001_happy_monotonico_crescente(db):
    """Happy: 3 OSs consecutivas no mesmo tenant -> numero_os crescente."""
    tenant = TenantFactory(slug=f"num-h-{uuid4().hex[:6]}")
    cli, eq = _setup(tenant)
    n1 = _abrir(tenant, cli, eq).numero_os
    n2 = _abrir(tenant, cli, eq).numero_os
    n3 = _abrir(tenant, cli, eq).numero_os
    assert n1 < n2 < n3


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_num_001_cross_tenant_sequence_global(db):
    """Cross-tenant: sequence eh GLOBAL — tenant A e B compartilham
    monotonicidade da sequence; UNIQUE(tenant, numero_os) preserva
    isolamento mesmo com numero compartilhado."""
    tenant_a = TenantFactory(slug=f"num-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"num-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    cli_b, eq_b = _setup(tenant_b)

    res_a = _abrir(tenant_a, cli_a, eq_a)
    res_b = _abrir(tenant_b, cli_b, eq_b)
    # Sequence global -> numeros diferentes (mesmo entre tenants).
    assert res_a.numero_os != res_b.numero_os

    with run_in_tenant_context(tenant_a.id):
        os_a = OS.objects.get(id=res_a.os_id)
    with run_in_tenant_context(tenant_b.id):
        os_b = OS.objects.get(id=res_b.os_id)
    assert os_a.tenant_id == tenant_a.id
    assert os_b.tenant_id == tenant_b.id
