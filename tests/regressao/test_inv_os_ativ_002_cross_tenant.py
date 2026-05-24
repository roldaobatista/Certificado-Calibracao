"""Anti-regressao INV-OS-ATIV-002 — cross-tenant proibido entre OS e Atividade.

INV-OS-ATIV-002: AtividadeDaOS.tenant_id MUST == OS.tenant_id. RLS do banco
+ trigger sao defesa em profundidade contra bug de injecao de tenant via
ORM. INV-TENANT-001 derivado.

≥3 testes: happy (mesmo tenant), unhappy (tenant divergente bloqueado),
cross-tenant (OS em tenant A nao visivel em tenant B via RLS).
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
from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS
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
            tag=f"INV-CT-{sfx}",
            numero_serie=f"NS-CT-{sfx}",
            fabricante="Toledo",
            modelo="X",
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
def test_inv_os_ativ_002_happy_atividade_herda_tenant_da_os(db):
    """Happy: atividade gerada via use case sempre tem tenant == OS.tenant."""
    tenant = TenantFactory(slug=f"inv-ct-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res = _abrir(tenant, cliente, equipamento)
    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        for ativ in os_obj.atividades.all():
            assert ativ.tenant_id == os_obj.tenant_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_002_unhappy_atividade_em_tenant_b_nao_le_os_tenant_a(db):
    """Unhappy: dentro de tenant_b NAO consegue ler/manipular OS de tenant_a (RLS)."""
    tenant_a = TenantFactory(slug=f"inv-ct-a-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-ct-b-{uuid4().hex[:6]}")
    cliente_a, equip_a = _setup(tenant_a)
    res_a = _abrir(tenant_a, cliente_a, equip_a)

    # Dentro do tenant_b, OS de tenant_a NAO eh visivel — RLS bloqueia leitura.
    with run_in_tenant_context(tenant_b.id):
        assert not OS.objects.filter(id=res_a.os_id).exists()
        assert not AtividadeDaOS.objects.filter(os_id=res_a.os_id).exists()


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_002_cross_tenant_listagem_isolada(db):
    """OSs de tenant_a nao aparecem em listagem do tenant_b (RLS)."""
    tenant_a = TenantFactory(slug=f"inv-ct-la-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-ct-lb-{uuid4().hex[:6]}")
    cliente_a, equip_a = _setup(tenant_a)
    cliente_b, equip_b = _setup(tenant_b)
    _abrir(tenant_a, cliente_a, equip_a)
    _abrir(tenant_b, cliente_b, equip_b)

    with run_in_tenant_context(tenant_a.id):
        oss_a = list(OS.objects.all())
    with run_in_tenant_context(tenant_b.id):
        oss_b = list(OS.objects.all())

    assert len(oss_a) == 1
    assert len(oss_b) == 1
    assert oss_a[0].id != oss_b[0].id
    assert oss_a[0].tenant_id == tenant_a.id
    assert oss_b[0].tenant_id == tenant_b.id
