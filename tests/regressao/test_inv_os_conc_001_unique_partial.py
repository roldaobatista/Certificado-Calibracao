"""Anti-regressao INV-OS-CONC-001 (ADR-0041) — unique partial index garante
concorrencia max 1 atividade EM_EXECUCAO por equipamento quando o tipo
bloqueia (calibracao etc).

CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip
  ON atividade_da_os (tenant_id, equipamento_id)
  WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true;

≥3 testes: happy (1 atividade EM_EXECUCAO bloqueante OK), unhappy (2
atividades EM_EXECUCAO bloqueantes no mesmo equip falha), cross-tenant
(mesmo equip em tenants distintos NAO conflita — testavel ate o ponto
do RLS, ja que equipamento e tenant-scoped).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import AtividadeDaOS
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
            tag=f"INV-CONC-{sfx}",
            numero_serie=f"NS-CONC-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_atribuir(tenant, cliente, equipamento, executor_id, tipo):
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
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=tipo,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res.os_id)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=atividades[0].id,
                        tecnico_executor_id=executor_id,
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
    return atividades[0].id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_conc_001_happy_uma_atividade_em_execucao(db):
    """Happy: 1 atividade tipo bloqueante EM_EXECUCAO no equipamento OK."""
    tenant = TenantFactory(slug=f"inv-conc-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    ativ_id = _abrir_atribuir(
        tenant, cliente, equipamento, executor_id, TipoAtividade.CALIBRACAO
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.estado == "em_execucao"
        assert ativ.tipo_bloqueia_concorrencia is True


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_conc_001_unhappy_segunda_em_execucao_bloqueia(db):
    """Unhappy: 2a atividade tipo=calibracao EM_EXECUCAO no MESMO equipamento
    estoura unique violation (idx_atividade_em_execucao_por_equip)."""
    tenant = TenantFactory(slug=f"inv-conc-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()

    # 1a atividade calibracao EM_EXECUCAO.
    ativ_1 = _abrir_atribuir(
        tenant, cliente, equipamento, executor_id, TipoAtividade.CALIBRACAO
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_1,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    # 2a atividade calibracao no mesmo equipamento. Abertura cria nova OS
    # com ja 1 atividade PENDENTE. Quando atribuir + iniciar, deve estourar.
    ativ_2 = _abrir_atribuir(
        tenant, cliente, equipamento, executor_id, TipoAtividade.CALIBRACAO
    )
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        with transaction.atomic():
            iniciar_atividade(
                payload=IniciarAtividadeInput(
                    atividade_id=ativ_2,
                    usuario_id=executor_id,
                    correlation_id=uuid4(),
                    client_event_id=uuid4(),
                    iniciada_em=datetime.now(UTC),
                ),
                repository=repo,
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_conc_001_cross_tenant_mesmo_equip_id_nao_conflita(db):
    """Tenants distintos: mesmo equipamento_id (logicamente impossivel; equip
    eh tenant-scoped) — RLS isola. Garante que o unique partial NAO eh
    cross-tenant (nome inclui tenant_id na coluna)."""
    tenant_a = TenantFactory(slug=f"inv-conc-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-conc-ctb-{uuid4().hex[:6]}")
    cliente_a, equip_a = _setup(tenant_a)
    cliente_b, equip_b = _setup(tenant_b)
    executor = uuid4()
    ativ_a = _abrir_atribuir(
        tenant_a, cliente_a, equip_a, executor, TipoAtividade.CALIBRACAO
    )
    ativ_b = _abrir_atribuir(
        tenant_b, cliente_b, equip_b, executor, TipoAtividade.CALIBRACAO
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant_a.id), transaction.atomic():
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_a,
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    with run_in_tenant_context(tenant_b.id), transaction.atomic():
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_b,
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    # Ambas EM_EXECUCAO sem conflito — unique partial inclui tenant_id.
    with run_in_tenant_context(tenant_a.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_a)
        assert ativ.estado == "em_execucao"
    with run_in_tenant_context(tenant_b.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_b)
        assert ativ.estado == "em_execucao"
