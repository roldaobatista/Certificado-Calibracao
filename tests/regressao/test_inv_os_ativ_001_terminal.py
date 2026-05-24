"""Anti-regressao INV-OS-ATIV-001 — OS so transita CONCLUIDA quando TODAS
as AtividadeDaOS estao em estado terminal (CONCLUIDA / NAO_CONFORME /
CANCELADA). Regra mestre da maquina de estados (AC-OS-004-3).

≥3 testes: happy (todas terminais -> OS CONCLUIDA), unhappy (1
em_execucao -> OS permanece), unhappy (NAO_CONFORME conta como terminal —
OS conclui se outras forem terminais).
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
from src.application.operacao.os.cancelar import (
    CancelarAtividadeInput,
    cancelar_atividade,
)
from src.application.operacao.os.concluir_atividade import (
    ConcluirAtividadeInput,
    concluir_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.marcar_nao_conformidade import (
    MarcarNCInput,
    marcar_nao_conformidade,
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

MOTIVO = "cliente solicitou alteracao de escopo apos analise da bancada"


def _setup_e_abrir_3(tenant, executor_id):
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
            tag=f"INV-T-{sfx}",
            numero_serie=f"NS-T-{sfx}",
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
        valor_total=Decimal("300.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.CALIBRACAO,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=True,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=2,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_PREVENTIVA,
                sequencia=3,
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
    return res.os_id, atividades


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_001_happy_todas_terminais_os_conclui(db):
    """Happy: 3 atividades CONCLUIDAS -> OS CONCLUIDA."""
    tenant = TenantFactory(slug=f"inv-t-h-{uuid4().hex[:6]}")
    executor = uuid4()
    os_id, atividades = _setup_e_abrir_3(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        for a in atividades:
            iniciar_atividade(
                payload=IniciarAtividadeInput(
                    atividade_id=a.id,
                    usuario_id=executor,
                    correlation_id=uuid4(),
                    client_event_id=uuid4(),
                    iniciada_em=datetime.now(UTC),
                ),
                repository=repo,
            )
            concluir_atividade(
                payload=ConcluirAtividadeInput(
                    atividade_id=a.id,
                    usuario_id=executor,
                    correlation_id=uuid4(),
                    concluida_em=datetime.now(UTC),
                    aceite_dispensado=True,
                ),
                repository=repo,
            )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=os_id)
        assert os_obj.estado == EstadoOS.CONCLUIDA.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_001_unhappy_uma_em_execucao_os_nao_conclui(db):
    """Unhappy: 2 CONCLUIDAS + 1 EM_EXECUCAO -> OS permanece EM_EXECUCAO."""
    tenant = TenantFactory(slug=f"inv-t-u-{uuid4().hex[:6]}")
    executor = uuid4()
    os_id, atividades = _setup_e_abrir_3(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        # Conclui apenas 2 das 3.
        for a in atividades[:2]:
            iniciar_atividade(
                payload=IniciarAtividadeInput(
                    atividade_id=a.id,
                    usuario_id=executor,
                    correlation_id=uuid4(),
                    client_event_id=uuid4(),
                    iniciada_em=datetime.now(UTC),
                ),
                repository=repo,
            )
            concluir_atividade(
                payload=ConcluirAtividadeInput(
                    atividade_id=a.id,
                    usuario_id=executor,
                    correlation_id=uuid4(),
                    concluida_em=datetime.now(UTC),
                    aceite_dispensado=True,
                ),
                repository=repo,
            )
        # 3a apenas inicia (EM_EXECUCAO — nao-terminal).
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=atividades[2].id,
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=os_id)
        # OS NAO conclui — 1 atividade nao-terminal segura.
        assert os_obj.estado != EstadoOS.CONCLUIDA.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_ativ_001_nao_conforme_e_cancelada_contam_como_terminais(db):
    """NAO_CONFORME + CANCELADA + CONCLUIDA = OS conclui (regra terminal)."""
    tenant = TenantFactory(slug=f"inv-t-mix-{uuid4().hex[:6]}")
    executor = uuid4()
    os_id, atividades = _setup_e_abrir_3(tenant, executor)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        # Ativ 1 (calibracao) -> EM_EXECUCAO -> NAO_CONFORME.
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=atividades[0].id,
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        marcar_nao_conformidade(
            payload=MarcarNCInput(
                atividade_id=atividades[0].id,
                usuario_id=executor,
                razao=MotivoCancelamento(MOTIVO),
                correlation_id=uuid4(),
                marcada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        # Ativ 2 -> CANCELADA.
        cancelar_atividade(
            payload=CancelarAtividadeInput(
                atividade_id=atividades[1].id,
                usuario_id=executor,
                motivo=MotivoCancelamento(MOTIVO),
                correlation_id=uuid4(),
                cancelada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        # Ativ 3 -> CONCLUIDA.
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=atividades[2].id,
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=atividades[2].id,
                usuario_id=executor,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=os_id)
        # Mix NC+CANCELADA+CONCLUIDA = todas terminais -> OS conclui.
        assert os_obj.estado == EstadoOS.CONCLUIDA.value
        assert os_obj.nao_conformidade_global is True
