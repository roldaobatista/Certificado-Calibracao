"""Pipeline integrado M3 Fase 5 — atribuir -> iniciar -> concluir atividade.

Cobre:
- AC-OS-002b-1 (atribuir tecnico happy)
- AC-OS-003-1 (iniciar happy + OS->EM_EXECUCAO)
- AC-OS-003-4 (gate sequencia N-1 -> 412 SequenciaPendente)
- AC-OS-004-1 (concluir happy)
- AC-OS-004-3 (OS->CONCLUIDA + tipo_predominante)
- AC-OS-004-4 (NaoEExecutor 403)

Testa contra `DjangoOSRepository` real.
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
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS, EventoDeOS
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
            tag=f"M3-LC-{sfx}",
            numero_serie=f"NS-LC-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_duas_atividades(tenant, cliente, equipamento):
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
        valor_total=Decimal("200.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("80.00"),
                requer_recebimento=False,
                equipamento_id=equipamento.id,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_PREVENTIVA,
                sequencia=2,
                valor_unitario=Decimal("120.00"),
                requer_recebimento=False,
                equipamento_id=equipamento.id,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        return abrir_os_via_orcamento(payload=payload, repository=repo)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_pipeline_happy_atribuir_iniciar_concluir(db):
    """AC-OS-002b-1 + AC-OS-003-1 + AC-OS-004-1 + AC-OS-004-3."""
    tenant = TenantFactory(slug=f"m3lc-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res_abrir = _abrir_duas_atividades(tenant, cliente, equipamento)
    repo = DjangoOSRepository()

    executor_id = uuid4()

    # ---- atribuir tecnico nas 2 atividades ----
    with run_in_tenant_context(tenant.id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_1 = next(a for a in atividades if a.sequencia == 1)
        ativ_2 = next(a for a in atividades if a.sequencia == 2)
        res_atrib = atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_1.id, tecnico_executor_id=executor_id
                    ),
                    AtribuicaoAtividade(
                        atividade_id=ativ_2.id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
    assert res_atrib.os_transitou_para_agendada is True

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res_abrir.os_id)
        assert os_obj.estado == EstadoOS.AGENDADA.value

    # ---- iniciar atividade 1 ----
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res_ini_1 = iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_1.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    assert res_ini_1.os_transitou_para_em_execucao is True

    # ---- concluir atividade 1 (sem checklist; sem aceite — tipo=vistoria nao exige) ----
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res_concl_1 = concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_1.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    assert res_concl_1.os_transitou_para_concluida is False  # ainda tem ativ_2

    # ---- iniciar + concluir atividade 2 ----
    with run_in_tenant_context(tenant.id), transaction.atomic():
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_2.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        res_concl_2 = concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_2.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,  # tipo=manutencao_preventiva nao exige aceite mesmo
            ),
            repository=repo,
        )
    assert res_concl_2.os_transitou_para_concluida is True
    # Empate: 2 tipos diferentes (vistoria + manutencao_preventiva), sem
    # calibracao. Regra: maior sequencia vence -> manutencao_preventiva.
    assert res_concl_2.tipo_predominante == "manutencao_preventiva"

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res_abrir.os_id)
        assert os_obj.estado == EstadoOS.CONCLUIDA.value
        assert os_obj.tipo_predominante == "manutencao_preventiva"

        atividades = list(AtividadeDaOS.objects.filter(os_id=res_abrir.os_id))
        assert all(a.estado == EstadoAtividade.CONCLUIDA.value for a in atividades)

        # Evento OS_CONCLUIDA gravado.
        ev_os_concluida = EventoDeOS.objects.filter(
            os_id=res_abrir.os_id,
            tipo=TipoEventoDeOS.OS_CONCLUIDA.value,
        ).count()
        assert ev_os_concluida == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_003_4_sequencia_pendente_bloqueia_iniciar(db):
    """AC-OS-003-4: iniciar ativ N com ativ N-1 nao-terminal -> 412 SequenciaPendente."""
    tenant = TenantFactory(slug=f"m3lc-u3-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res_abrir = _abrir_duas_atividades(tenant, cliente, equipamento)
    repo = DjangoOSRepository()
    executor_id = uuid4()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_1 = next(a for a in atividades if a.sequencia == 1)
        ativ_2 = next(a for a in atividades if a.sequencia == 2)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_1.id, tecnico_executor_id=executor_id
                    ),
                    AtribuicaoAtividade(
                        atividade_id=ativ_2.id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    # Tenta iniciar atividade 2 com atividade 1 ainda AGENDADA.
    with run_in_tenant_context(tenant.id), pytest.raises(ErroIniciarAtividade) as exc:
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=ativ_2.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    assert exc.value.codigo == "SequenciaPendente"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_004_4_nao_e_executor_403(db):
    """AC-OS-004-4: usuario != tecnico_executor_id -> 403 NaoEExecutor."""
    tenant = TenantFactory(slug=f"m3lc-u4-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res_abrir = _abrir_duas_atividades(tenant, cliente, equipamento)
    repo = DjangoOSRepository()
    executor_id = uuid4()
    intruso_id = uuid4()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_1 = next(a for a in atividades if a.sequencia == 1)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_1.id, tecnico_executor_id=executor_id
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
                atividade_id=ativ_1.id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id), pytest.raises(ErroConcluirAtividade) as exc:
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_1.id,
                usuario_id=intruso_id,  # nao eh o executor
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )
    assert exc.value.codigo == "NaoEExecutor"
    assert exc.value.http_status == 403
