"""Testes integrados M3 Fase 7 — jobs procrastinate T-OS-090..093.

Cobre comportamento esperado de cada job:
- watchdog_calibracao_link: detecta atividade calibracao concluida sem link.
- truncar_geo_lgpd: 5a -> geo NULL, hash preservado.
- retry_anonimizacao_pendente: conta OS abertas com cliente_id.
- detectar_sla_breach: detecta OS estourada via SLAContrato.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.jobs import (
    detectar_sla_breach,
    retry_anonimizacao_pendente,
    truncar_geo_lgpd,
    watchdog_calibracao_link,
)
from src.infrastructure.ordens_servico.models import (
    OS,
    AtividadeDaOS,
    SLAContrato,
)
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
            tag=f"M3-J-{sfx}",
            numero_serie=f"NS-J-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_calibracao_concluida(tenant, cliente, equipamento, executor_id):
    """Cria OS calibracao + atribui + inicia + conclui (sem link)."""
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
                valor_unitario=Decimal("300.00"),
                requer_recebimento=True,
                equipamento_id=equipamento.id,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res.os_id)
        ativ_id = atividades[0].id
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
    return res.os_id, ativ_id


# =============================================================
# T-OS-090 watchdog_calibracao_link
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_watchdog_calibracao_link_detecta_concluida_sem_link(db):
    tenant = TenantFactory(slug=f"m3j-wd-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    _, ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento, executor)

    # Avanca relogio simulado 100h apos conclusao.
    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        # Forca concluida_em pra 100h atras (passa do alerta 72h, nao do NC 15d).
        ativ.concluida_em = datetime.now(UTC) - timedelta(hours=100)
        ativ.save(update_fields=["concluida_em"])

    with run_in_tenant_context(tenant.id):
        resultado = watchdog_calibracao_link(tenant_id=tenant.id)
    assert resultado["alertados"] == 1
    assert resultado["nc_candidatos"] == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_watchdog_calibracao_link_atividade_com_link_nao_dispara(db):
    tenant = TenantFactory(slug=f"m3j-wd2-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    _, ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento, executor)

    # Atribui link_modulo_tecnico_id (simula modulo calibracao preencheu).
    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            link_modulo_tecnico_id=uuid4(),
            concluida_em=datetime.now(UTC) - timedelta(hours=100),
        )

    with run_in_tenant_context(tenant.id):
        resultado = watchdog_calibracao_link(tenant_id=tenant.id)
    assert resultado["alertados"] == 0


# =============================================================
# T-OS-091 truncar_geo_lgpd
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_truncar_geo_lgpd_5a_pos_concluida_zera_coordenadas(db):
    tenant = TenantFactory(slug=f"m3j-geo-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    _, ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento, executor)

    # Forca concluida_em 6 anos atras + geo preenchida.
    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(days=365 * 6),
            geo_lat=-23.5,
            geo_long=-46.6,
            geo_municipio_hash="hash-saopaulo",
        )

    with run_in_tenant_context(tenant.id):
        truncadas = truncar_geo_lgpd(tenant_id=tenant.id)
    assert truncadas == 1

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.geo_lat is None
        assert ativ.geo_long is None
        # Hash municipio PRESERVADO (INV-OS-GEO-001 item d).
        assert ativ.geo_municipio_hash == "hash-saopaulo"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_truncar_geo_lgpd_atividade_recente_nao_trunca(db):
    tenant = TenantFactory(slug=f"m3j-geo2-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    _, ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento, executor)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            geo_lat=-23.5, geo_long=-46.6
        )
        truncadas = truncar_geo_lgpd(tenant_id=tenant.id)
    assert truncadas == 0


# =============================================================
# T-OS-092 retry_anonimizacao_pendente
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_retry_anonimizacao_conta_os_ativas_com_cliente(db):
    tenant = TenantFactory(slug=f"m3j-anon-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    _, _ = _abrir_calibracao_concluida(tenant, cliente, equipamento, executor)

    # OS concluiu, mas estado nao-terminal? Nao — concluida eh terminal pra job.
    with run_in_tenant_context(tenant.id):
        pendentes = retry_anonimizacao_pendente(tenant_id=tenant.id)
    # Apenas OSs em RASCUNHO/AGENDADA/EM_EXECUCAO bloqueiam — concluida nao.
    assert pendentes == 0


# =============================================================
# T-OS-093 detectar_sla_breach
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_detectar_sla_breach_detecta_os_estourada(db):
    tenant = TenantFactory(slug=f"m3j-sla-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()

    # Cria OS + SLA agressivo (1h atendimento) + forca criada_em 5h atras.
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
                equipamento_id=equipamento.id,
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
                        atividade_id=atividades[0].id, tecnico_executor_id=executor
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        SLAContrato.objects.create(
            tenant=tenant,
            cliente=cliente,
            prioridade="alta",
            prazo_atendimento_horas=1,  # estoura em 1h
            prazo_conclusao_horas=4,
            descricao_publica="SLA emergencia 1h",
            vigencia_inicio=datetime.now(UTC) - timedelta(days=1),
            vigencia_fim=None,
            revogado_em=None,
            motivo_revogacao_hash="",
        )
        # Forca criada_em 5h atras pra estourar SLA.
        OS.objects.filter(id=res.os_id).update(
            criada_em=datetime.now(UTC) - timedelta(hours=5),
            estado="agendada",
        )

    with run_in_tenant_context(tenant.id):
        detectados = detectar_sla_breach(tenant_id=tenant.id)
    assert detectados == 1
