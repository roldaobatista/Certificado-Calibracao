"""Anti-regressao INV-OS-CAL-LINK-001 (T-OS-113) — janela link Calibracao.

INV-OS-CAL-LINK-001: Atividade tipo=calibracao CONCLUIDA precisa de FK
reversa `link_modulo_tecnico_id` em <=72h (alerta P2) e <=15 dias uteis
(NC automatica `link_calibracao_faltando` que bloqueia emissao de certificado).
Watchdog `watchdog_calibracao_link` (T-OS-090) detecta atividades vencidas.

≥3 testes: happy (com link nao dispara), unhappy alerta 72h, unhappy
NC 21 dias corridos, cross-tenant (tenant A nao conta atividades de B).
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
from src.infrastructure.ordens_servico.jobs import watchdog_calibracao_link
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
            tag=f"INV-CAL-{sfx}",
            numero_serie=f"NS-CAL-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_calibracao_concluida(tenant, cliente, equipamento) -> uuid4:
    """Cria OS calibracao + atribui + inicia + conclui. Sem link reverso."""
    repo = DjangoOSRepository()
    executor = uuid4()
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
                        atividade_id=ativ_id, tecnico_executor_id=executor
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
                usuario_id=executor,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
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
    return ativ_id


# =============================================================
# Happy: atividade ainda dentro da janela 72h nao alerta
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_cal_link_001_happy_dentro_janela_72h_nao_alerta(db):
    """Happy: concluida ha 50h (< 72h) sem link nao alerta nem gera NC."""
    tenant = TenantFactory(slug=f"inv-cl-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(hours=50),
        )
        resultado = watchdog_calibracao_link(tenant_id=tenant.id)
    assert resultado == {"alertados": 0, "nc_candidatos": 0}


# =============================================================
# Unhappy alerta 72h: concluida ha 100h sem link
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_cal_link_001_unhappy_passou_72h_alerta(db):
    """Unhappy alerta: concluida ha 100h sem link -> alertados=1, nc=0."""
    tenant = TenantFactory(slug=f"inv-cl-a-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(hours=100),
        )
        resultado = watchdog_calibracao_link(tenant_id=tenant.id)
    assert resultado["alertados"] == 1
    assert resultado["nc_candidatos"] == 0


# =============================================================
# Unhappy NC: 15d uteis (~21d corridos) sem link -> nc_candidato
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_cal_link_001_unhappy_passou_21d_corridos_vira_nc(db):
    """Unhappy NC: concluida ha 25d sem link -> nc_candidatos=1 (alem
    de alertados=1; nc cumulativo)."""
    tenant = TenantFactory(slug=f"inv-cl-n-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    ativ_id = _abrir_calibracao_concluida(tenant, cliente, equipamento)

    with run_in_tenant_context(tenant.id):
        AtividadeDaOS.objects.filter(id=ativ_id).update(
            concluida_em=datetime.now(UTC) - timedelta(days=25),
        )
        resultado = watchdog_calibracao_link(tenant_id=tenant.id)
    assert resultado["alertados"] == 1
    assert resultado["nc_candidatos"] == 1


# =============================================================
# Cross-tenant: tenant A nao conta atividades de tenant B
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_cal_link_001_cross_tenant_isolado(db):
    """Cross-tenant: watchdog tenant A retorna 1; tenant B retorna 0
    mesmo com atividade vencida em A."""
    tenant_a = TenantFactory(slug=f"inv-cl-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-cl-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    ativ_a_id = _abrir_calibracao_concluida(tenant_a, cli_a, eq_a)

    with run_in_tenant_context(tenant_a.id):
        AtividadeDaOS.objects.filter(id=ativ_a_id).update(
            concluida_em=datetime.now(UTC) - timedelta(hours=100),
        )

    with run_in_tenant_context(tenant_a.id):
        r_a = watchdog_calibracao_link(tenant_id=tenant_a.id)
    with run_in_tenant_context(tenant_b.id):
        r_b = watchdog_calibracao_link(tenant_id=tenant_b.id)

    assert r_a["alertados"] == 1, "tenant A deveria detectar a propria atividade"
    assert r_b["alertados"] == 0, "tenant B nao deveria contar atividade do tenant A"
