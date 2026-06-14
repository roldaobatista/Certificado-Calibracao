"""Testes integrados M3 OS Fase 6 — Query services T-OS-085..088.

Cobre:
- visao_360_da_os (T-OS-085)
- listar_os com filtros (T-OS-086)
- os_do_tecnico (T-OS-087)
- timeline_da_os (T-OS-088)

Todos contra `DjangoOSRepository` real.
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
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.queries.listagem import (
    listar_os,
    os_do_tecnico,
)
from src.application.operacao.os.queries.timeline import timeline_da_os
from src.application.operacao.os.queries.visao_360 import visao_360_da_os
from src.domain.operacao.os.value_objects import EstadoOS, TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
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
            tag=f"M3-Q-{sfx}",
            numero_serie=f"NS-Q-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_2_atividades(tenant, cliente, equipamento, executor_id=None):
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("250.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
                equipamento_id=equipamento.id,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_PREVENTIVA,
                sequencia=2,
                valor_unitario=Decimal("150.00"),
                requer_recebimento=False,
                equipamento_id=equipamento.id,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        if executor_id is not None:
            atividades = repo.listar_atividades_por_os(res.os_id)
            atribuir_tecnico(
                payload=AtribuirTecnicoInput(
                    os_id=res.os_id,
                    atribuicoes=tuple(
                        AtribuicaoAtividade(
                            atividade_id=a.id, tecnico_executor_id=executor_id
                        )
                        for a in atividades
                    ),
                    correlation_id=uuid4(),
                    solicitada_em=datetime.now(UTC),
                    solicitada_por_user_id=None,
                ),
                repository=repo,
            )
    return res.os_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_carrega_os_completa(db):
    tenant = TenantFactory(slug=f"m3q-v-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    os_id = _abrir_2_atividades(tenant, cliente, equipamento)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id):
        visao = visao_360_da_os(os_id, repo)

    assert visao is not None
    assert visao.numero_os > 0
    assert visao.estado == EstadoOS.RASCUNHO.value
    assert visao.valor_total == Decimal("250.00")
    assert len(visao.atividades) == 2
    # Ordenadas por sequencia.
    assert visao.atividades[0].sequencia == 1
    assert visao.atividades[1].sequencia == 2
    assert all(not a.tem_aceite for a in visao.atividades)
    assert all(not a.tem_dispensa for a in visao.atividades)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_visao_360_retorna_none_se_nao_existe(db):
    tenant = TenantFactory(slug=f"m3q-vn-{uuid4().hex[:6]}")
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        assert visao_360_da_os(uuid4(), repo) is None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_listar_os_com_filtros(db):
    tenant = TenantFactory(slug=f"m3q-l-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    _abrir_2_atividades(tenant, cliente, equipamento)
    _abrir_2_atividades(tenant, cliente, equipamento)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id):
        lista = listar_os(tenant_id=tenant.id, repository=repo)
    assert len(lista) == 2

    with run_in_tenant_context(tenant.id):
        rascunhos = listar_os(
            tenant_id=tenant.id, repository=repo, estado=EstadoOS.RASCUNHO.value
        )
    assert len(rascunhos) == 2

    with run_in_tenant_context(tenant.id):
        agendadas = listar_os(
            tenant_id=tenant.id, repository=repo, estado=EstadoOS.AGENDADA.value
        )
    assert agendadas == []


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_listar_os_paginacao_valida_limites(db):
    repo = DjangoOSRepository()
    with pytest.raises(ValueError):
        listar_os(tenant_id=uuid4(), repository=repo, limit=0)
    with pytest.raises(ValueError):
        listar_os(tenant_id=uuid4(), repository=repo, limit=300)
    with pytest.raises(ValueError):
        listar_os(tenant_id=uuid4(), repository=repo, offset=-1)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_os_do_tecnico_filtra_por_executor(db):
    tenant = TenantFactory(slug=f"m3q-t-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_alvo = uuid4()
    executor_outro = uuid4()

    _abrir_2_atividades(tenant, cliente, equipamento, executor_id=executor_alvo)
    _abrir_2_atividades(tenant, cliente, equipamento, executor_id=executor_outro)
    _abrir_2_atividades(tenant, cliente, equipamento)  # sem tecnico

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        do_alvo = os_do_tecnico(
            tenant_id=tenant.id, tecnico_user_id=executor_alvo, repository=repo
        )
    assert len(do_alvo) == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_timeline_da_os_retorna_eventos_em_ordem(db):
    tenant = TenantFactory(slug=f"m3q-tl-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    os_id = _abrir_2_atividades(tenant, cliente, equipamento, executor_id=executor_id)
    repo = DjangoOSRepository()

    # Inicia atividade 1 pra gerar mais um evento.
    with run_in_tenant_context(tenant.id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(os_id)
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=atividades[0].id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        eventos = timeline_da_os(os_id, repo)

    # Pelo menos 3 eventos: os_aberta + os_atribuida + atividade_iniciada.
    assert len(eventos) >= 3
    tipos = {e.tipo for e in eventos}
    assert "os_aberta" in tipos
    assert "os_atribuida" in tipos
    assert "atividade_iniciada" in tipos
    # Ordem decrescente.
    for i in range(len(eventos) - 1):
        assert eventos[i].occurred_at >= eventos[i + 1].occurred_at
