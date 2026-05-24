"""Anti-regressao INV-OS-ATIV-005 — `tecnico_executor_id` eh o UNICO
autorizado a iniciar/concluir/marcar_nc na atividade. Outros usuarios
recebem 403.

≥3 testes: happy (executor inicia/conclui), unhappy (outro usuario
recebe 403 ao concluir), unhappy (outro usuario recebe 403 ao marcar NC).
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
    ErroConcluirAtividade,
    concluir_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    ErroIniciarAtividade,
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.marcar_nao_conformidade import (
    ErroMarcarNC,
    MarcarNCInput,
    marcar_nao_conformidade,
)
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    MotivoCancelamento,
    TipoAtividade,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import AtividadeDaOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

MOTIVO = "padrao desviou da especificacao apos terceira leitura validada"


def _setup_calibracao_iniciada(tenant, executor_id):
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
            tag=f"INV-EX-{sfx}",
            numero_serie=f"NS-EX-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=uuid4(),
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.CALIBRACAO,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=True,
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
    return ativ_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_005_happy_executor_inicia_e_conclui(db):
    """Happy: usuario designado eh quem inicia e conclui."""
    tenant = TenantFactory(slug=f"inv-ex-h-{uuid4().hex[:6]}")
    executor = uuid4()
    ativ_id = _setup_calibracao_iniciada(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=executor,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )
    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.estado == EstadoAtividade.CONCLUIDA.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_005_unhappy_outro_usuario_concluir_403(db):
    """Unhappy: usuario != executor tenta concluir -> NaoEExecutor 403."""
    tenant = TenantFactory(slug=f"inv-ex-u-{uuid4().hex[:6]}")
    executor = uuid4()
    intruso = uuid4()
    ativ_id = _setup_calibracao_iniciada(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), pytest.raises(ErroConcluirAtividade) as exc:
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=intruso,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )
    assert exc.value.codigo == "NaoEExecutor"
    assert exc.value.http_status == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_005_unhappy_outro_usuario_marca_nc_403(db):
    """Unhappy: outro usuario tenta marcar NC -> NaoEExecutor 403."""
    tenant = TenantFactory(slug=f"inv-ex-nc-{uuid4().hex[:6]}")
    executor = uuid4()
    intruso = uuid4()
    ativ_id = _setup_calibracao_iniciada(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), pytest.raises(ErroMarcarNC) as exc:
        marcar_nao_conformidade(
            payload=MarcarNCInput(
                atividade_id=ativ_id,
                usuario_id=intruso,
                razao=MotivoCancelamento(MOTIVO),
                correlation_id=uuid4(),
                marcada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    assert exc.value.codigo == "NaoEExecutor"
    assert exc.value.http_status == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_005_unhappy_outro_usuario_inicia_pendente_403(db):
    """Unhappy variante: usuario != executor tenta INICIAR atividade
    AGENDADA — bloqueia 403."""
    tenant = TenantFactory(slug=f"inv-ex-i-{uuid4().hex[:6]}")
    executor = uuid4()
    intruso = uuid4()

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
            tag=f"INV-EXI-{sfx}",
            numero_serie=f"NS-EXI-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
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
                        atividade_id=ativ_id, tecnico_executor_id=executor
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id), pytest.raises(ErroIniciarAtividade) as exc:
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=intruso,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    assert exc.value.codigo == "NaoEExecutor"
    assert exc.value.http_status == 403
