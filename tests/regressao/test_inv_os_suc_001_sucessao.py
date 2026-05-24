"""Anti-regressao INV-OS-SUC-001 (AC-OS-006-6/7) — reabertura M&A.

INV-OS-SUC-001: OS-mae com cliente_id NULL (anonimizado Zona A/B ADR-0021)
pode reabrir SOMENTE com `sucessao_societaria_id` informada; sem ela ->
412 `ClienteAnonimizadoSemSucessao`. OS-filha preserva
`cliente_referencia_hash` (audit) + `sucessao_societaria_id`.

≥3 testes: happy (cliente NAO anonimizado reabre OK), unhappy
(cliente anonimizado sem sucessao -> 412), happy 2 (cliente anonimizado
COM sucessao -> reabre OK preservando hash).
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
from src.application.operacao.os.concluir_atividade import (
    ConcluirAtividadeInput,
    concluir_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.operacoes_avancadas import (
    ErroReabrir,
    ReabrirOSInput,
    reabrir_os,
)
from src.domain.operacao.os.value_objects import (
    EstadoOS,
    MotivoCancelamento,
    TipoAtividade,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

MOTIVO = "garantia procedente apos analise de causa-raiz do tecnico signatario"


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
            tag=f"INV-SUC-{sfx}",
            numero_serie=f"NS-SUC-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_e_concluir(tenant, cliente, equipamento, executor_id):
    """Cria OS + atribui + inicia + conclui (estado CONCLUIDA)."""
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
                tipo=TipoAtividade.VISTORIA,
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
        ativ_id = repo.listar_atividades_por_os(res.os_id)[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
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
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )
    return res.os_id


def _anonimizar_cliente_da_os(tenant_id, os_id):
    """Simula Zona A/B ADR-0021: cliente_id vira NULL preservando hash.

    Anonimizacao real eh evento externo (saga Cliente.Anonimizado);
    `DjangoOSRepository.salvar_os` nao mexe em cliente_id (imutavel
    pos-INSERT). Aqui forcamos via ORM direto pra simular o estado
    pos-saga.
    """
    with run_in_tenant_context(tenant_id):
        OS.objects.filter(id=os_id).update(cliente_id=None)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_suc_001_happy_cliente_nao_anonimizado_reabre(db):
    """Happy: OS CONCLUIDA com cliente ativo reabre sem sucessao_societaria_id."""
    tenant = TenantFactory(slug=f"inv-suc-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    os_id = _abrir_e_concluir(tenant, cliente, equipamento, executor)

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = reabrir_os(
            payload=ReabrirOSInput(
                os_origem_id=os_id,
                motivo=MotivoCancelamento(MOTIVO),
                garantia_procedente=True,
                chamado_origem_id=None,
                sucessao_societaria_id=None,  # nao precisa — cliente ativo
                correlation_id=uuid4(),
                reaberta_em=datetime.now(UTC),
                reaberta_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        nova = OS.objects.get(id=res.os_id_nova)
        assert nova.cliente_id == cliente.id  # preserva
        assert nova.os_origem_id == os_id
        assert nova.sucessao_societaria_id is None
        assert nova.estado == EstadoOS.RASCUNHO.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_suc_001_unhappy_anonimizado_sem_sucessao_412(db):
    """Unhappy: cliente_id=NULL + sem sucessao_societaria_id -> 412
    ClienteAnonimizadoSemSucessao."""
    tenant = TenantFactory(slug=f"inv-suc-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    os_id = _abrir_e_concluir(tenant, cliente, equipamento, executor)
    _anonimizar_cliente_da_os(tenant.id, os_id)

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroReabrir) as exc:
        reabrir_os(
            payload=ReabrirOSInput(
                os_origem_id=os_id,
                motivo=MotivoCancelamento(MOTIVO),
                garantia_procedente=False,
                chamado_origem_id=None,
                sucessao_societaria_id=None,
                correlation_id=uuid4(),
                reaberta_em=datetime.now(UTC),
                reaberta_por_user_id=None,
            ),
            repository=repo,
        )
    assert exc.value.codigo == "ClienteAnonimizadoSemSucessao"
    assert exc.value.http_status == 412


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_suc_001_happy_anonimizado_com_sucessao_reabre_preservando_hash(db):
    """Happy 2: cliente anonimizado + sucessao_societaria_id presente ->
    OS-filha preserva cliente_referencia_hash + grava sucessao."""
    tenant = TenantFactory(slug=f"inv-suc-h2-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    os_id = _abrir_e_concluir(tenant, cliente, equipamento, executor)
    _anonimizar_cliente_da_os(tenant.id, os_id)

    sucessao_id = uuid4()
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = reabrir_os(
            payload=ReabrirOSInput(
                os_origem_id=os_id,
                motivo=MotivoCancelamento(MOTIVO),
                garantia_procedente=False,
                chamado_origem_id=None,
                sucessao_societaria_id=sucessao_id,
                correlation_id=uuid4(),
                reaberta_em=datetime.now(UTC),
                reaberta_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        nova = OS.objects.get(id=res.os_id_nova)
        assert nova.cliente_id is None  # cliente nao restaura
        assert nova.cliente_referencia_hash == "a" * 64  # preservado
        assert nova.sucessao_societaria_id == sucessao_id
