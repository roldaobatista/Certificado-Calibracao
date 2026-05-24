"""Anti-regressao INV-OS-FAT-001 (ADR-0042) — faturamento = sum atividades
nao canceladas; cancelamento parcial recalcula `valor_total_atualizado` +
publica `OS.EscopoAlterado`.

≥3 testes: happy (cancela 1, recalcula), todas canceladas (valor=0),
cross-tenant (cancelar em tenant_a nao afeta OS de tenant_b).
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
from src.application.operacao.os.cancelar import (
    CancelarAtividadeInput,
    cancelar_atividade,
)
from src.domain.operacao.os.value_objects import (
    MotivoCancelamento,
    TipoAtividade,
    TipoEventoDeOS,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS, EventoDeOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

MOTIVO = "tecnico identificou ressonancia eletromagnetica fora do escopo"


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
            tag=f"INV-FAT-{sfx}",
            numero_serie=f"NS-FAT-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_3_atividades(tenant, cliente, equipamento, valores):
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
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
        valor_total=sum((Decimal(v) for v in valores), Decimal("0")),
        itens=tuple(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=i + 1,
                valor_unitario=Decimal(v),
                requer_recebimento=False,
            )
            for i, v in enumerate(valores)
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        return abrir_os_via_orcamento(payload=payload, repository=repo)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_fat_001_happy_cancela_1_recalcula(db):
    """Happy: cancelar 1 atividade -> valor_total_atualizado = sum das outras 2."""
    tenant = TenantFactory(slug=f"inv-fat-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res = _abrir_3_atividades(tenant, cliente, equipamento, ["100", "200", "300"])
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(res.os_id)
        cancelar_atividade(
            payload=CancelarAtividadeInput(
                atividade_id=atividades[0].id,  # cancela R$ 100
                usuario_id=uuid4(),
                motivo=MotivoCancelamento(MOTIVO),
                correlation_id=uuid4(),
                cancelada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.valor_total_atualizado == Decimal("500.00")
        assert os_obj.valor_total == Decimal("600.00")
        # OS.EscopoAlterado publicado.
        assert (
            EventoDeOS.objects.filter(
                os_id=res.os_id,
                tipo=TipoEventoDeOS.OS_ESCOPO_ALTERADO.value,
            ).count()
            == 1
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_fat_001_unhappy_todas_canceladas_valor_zero(db):
    """Unhappy: cancelar TODAS -> valor_total_atualizado=0; valor_total intacto."""
    tenant = TenantFactory(slug=f"inv-fat-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res = _abrir_3_atividades(tenant, cliente, equipamento, ["100", "200"])
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        for ativ in repo.listar_atividades_por_os(res.os_id):
            cancelar_atividade(
                payload=CancelarAtividadeInput(
                    atividade_id=ativ.id,
                    usuario_id=uuid4(),
                    motivo=MotivoCancelamento(MOTIVO),
                    correlation_id=uuid4(),
                    cancelada_em=datetime.now(UTC),
                ),
                repository=repo,
            )
    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.valor_total_atualizado == Decimal("0")
        assert os_obj.valor_total == Decimal("300.00")  # preservado


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_fat_001_cross_tenant_cancelamento_isolado(db):
    """Cross-tenant: cancelamento em tenant_a NAO afeta valor de OS em tenant_b."""
    tenant_a = TenantFactory(slug=f"inv-fat-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-fat-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    cli_b, eq_b = _setup(tenant_b)
    res_a = _abrir_3_atividades(tenant_a, cli_a, eq_a, ["100", "200"])
    res_b = _abrir_3_atividades(tenant_b, cli_b, eq_b, ["50", "75"])
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant_a.id), transaction.atomic():
        ativ_a = repo.listar_atividades_por_os(res_a.os_id)[0]
        cancelar_atividade(
            payload=CancelarAtividadeInput(
                atividade_id=ativ_a.id,
                usuario_id=uuid4(),
                motivo=MotivoCancelamento(MOTIVO),
                correlation_id=uuid4(),
                cancelada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant_a.id):
        os_a = OS.objects.get(id=res_a.os_id)
        assert os_a.valor_total_atualizado == Decimal("200.00")
    with run_in_tenant_context(tenant_b.id):
        os_b = OS.objects.get(id=res_b.os_id)
        # OS_b intacta: nenhum cancelamento la.
        assert os_b.valor_total_atualizado == Decimal("125.00")
