"""Testes de integracao do use case `abrir_os_via_orcamento` (T-OS-041).

Cobre AC-OS-001-1, 2, 7, 8 atravessando o adapter Django concreto
(`DjangoOSRepository`) — exercita persistencia real de OS + AtividadeDaOS
+ EventoDeOS contra o banco de testes.

AC-OS-001-3/4/5/6 sao cobertos por outros testes (idempotencia M2,
middleware tenant, consumer queries externas, saga anonimizacao).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from django.db import transaction

from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ErroAbrirOS,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import (
    OS,
    AtividadeDaOS,
    EventoDeOS,
)
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _setup_cliente_equipamento(tenant):
    """Cria cliente PJ + equipamento dentro do tenant context."""
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
            tag=f"M3-OS-{sfx}",
            numero_serie=f"NS-M3OS-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _input_basico(
    *,
    tenant_id: UUID,
    cliente_id: UUID,
    equipamento_id: UUID,
    itens: tuple[ItemOrcamento, ...] | None = None,
    analise_critica_id: UUID | None = None,
    equipamento_recebimento_id: UUID | None = None,
) -> AbrirOSInput:
    """Builder com defaults validos pra os 4 ACs cobertos."""
    if itens is None:
        itens = (
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_CORRETIVA,
                sequencia=1,
                valor_unitario=Decimal("150.00"),
                requer_recebimento=False,
            ),
        )
    return AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant_id,
        cliente_id=cliente_id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento_id,
        equipamento_recebimento_id=equipamento_recebimento_id,
        analise_critica_id=analise_critica_id or uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=sum((i.valor_unitario for i in itens), Decimal("0")),
        itens=itens,
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_001_1_happy_abre_os_rascunho_n_atividades_pendentes(db):
    """AC-OS-001-1: cria OS RASCUNHO + N AtividadeDaOS PENDENTE + evento os_aberta."""
    tenant = TenantFactory(slug=f"m3os-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)

    payload = _input_basico(
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        equipamento_id=equipamento.id,
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_CORRETIVA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=2,
                valor_unitario=Decimal("50.00"),
                requer_recebimento=False,
            ),
        ),
    )

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        resultado = abrir_os_via_orcamento(payload=payload, repository=repo)

    assert resultado.numero_os > 0
    assert len(resultado.atividades_planejadas) == 2

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=resultado.os_id)
        assert os_obj.estado == EstadoOS.RASCUNHO.value
        assert os_obj.numero_os == resultado.numero_os
        assert os_obj.valor_total == Decimal("150.00")

        atividades = list(AtividadeDaOS.objects.filter(os=os_obj).order_by("sequencia"))
        assert len(atividades) == 2
        assert all(a.estado == EstadoAtividade.PENDENTE.value for a in atividades)
        assert atividades[0].tipo == TipoAtividade.MANUTENCAO_CORRETIVA.value
        assert atividades[1].tipo == TipoAtividade.VISTORIA.value

        eventos = list(EventoDeOS.objects.filter(os=os_obj))
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEventoDeOS.OS_ABERTA.value
        assert eventos[0].payload_data["numero_os"] == resultado.numero_os
        assert len(eventos[0].payload_data["atividades_planejadas"]) == 2


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_001_2_unhappy_orcamento_sem_itens_400(db):
    """AC-OS-001-2: orcamento sem itens -> 400 OrcamentoSemItensCarrinho."""
    tenant = TenantFactory(slug=f"m3os-u2-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)

    payload = _input_basico(
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        equipamento_id=equipamento.id,
        itens=(),
    )

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAbrirOS) as exc:
        abrir_os_via_orcamento(payload=payload, repository=repo)

    assert exc.value.codigo == "OrcamentoSemItensCarrinho"
    assert exc.value.http_status == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_001_7_unhappy_orcamento_sem_analise_critica_412(db):
    """AC-OS-001-7 (P-OS-R2): analise_critica_id NULL -> 412 OrcamentoSemAnaliseCritica."""
    tenant = TenantFactory(slug=f"m3os-u7-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)

    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=None,  # disparador
        analise_critica_snapshot_hash="",
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_CORRETIVA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAbrirOS) as exc:
        abrir_os_via_orcamento(payload=payload, repository=repo)

    assert exc.value.codigo == "OrcamentoSemAnaliseCritica"
    assert exc.value.http_status == 412


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_001_8_unhappy_bancada_sem_recebimento_412(db):
    """AC-OS-001-8 (P-OS-R4): OS de bancada sem recebimento -> 412."""
    tenant = TenantFactory(slug=f"m3os-u8-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)

    payload = _input_basico(
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        equipamento_id=equipamento.id,
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.CALIBRACAO,
                sequencia=1,
                valor_unitario=Decimal("250.00"),
                requer_recebimento=True,  # bancada
            ),
        ),
        equipamento_recebimento_id=None,  # ausente
    )

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAbrirOS) as exc:
        abrir_os_via_orcamento(payload=payload, repository=repo)

    assert exc.value.codigo == "EquipamentoSemRecebimentoRegistrado"
    assert exc.value.http_status == 412
