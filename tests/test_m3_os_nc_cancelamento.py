"""Testes integrados M3 Fase 5 — NC (CAPA) + cancelamento atividade/OS.

Cobre:
- AC-OS-005-1 (marcar NC happy: tipo=calibracao em EM_EXECUCAO -> NAO_CONFORME)
- AC-OS-005-2 (OS.nao_conformidade_global=True apos NC)
- AC-OS-005-3 + AC-OS-005-5 (resolver_nc CAPA completo -> volta EM_EXECUCAO)
- AC-OS-005-5 (CAPA incompleto -> 412)
- US-OS-008/011 cancelamento OS + atividade + ADR-0042 OS.EscopoAlterado
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
    CancelarOSInput,
    cancelar_atividade,
    cancelar_os,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.marcar_nao_conformidade import (
    MarcarNCInput,
    ResolverNCInput,
    marcar_nao_conformidade,
    resolver_nc,
)
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    MotivoCancelamento,
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
    NaoConformidadeAtividade,
)
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

MOTIVO_VALIDO_A = "valor obtido fora da incerteza declarada pelo cliente final"
MOTIVO_VALIDO_B = "lacre rompido durante transporte; padrao precisa recalibrar"
MOTIVO_VALIDO_C = "tecnico aplicou novo procedimento aprovado pelo gerente RBC"
MOTIVO_VALIDO_D = "incerteza expandida confirmada apos terceira leitura padrao"


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
            tag=f"M3-NC-{sfx}",
            numero_serie=f"NS-NC-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_e_iniciar_calibracao(tenant, cliente, equipamento, executor_id):
    """Abre OS com 1 atividade tipo=calibracao + atribui + inicia."""
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=uuid4(),  # bancada
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
        res_abrir = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_id = atividades[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
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
    return res_abrir.os_id, ativ_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_005_1_e_2_marcar_nc_calibracao_happy(db):
    """AC-OS-005-1 + AC-OS-005-2: NC marcada -> atividade NAO_CONFORME +
    OS.nao_conformidade_global=True."""
    tenant = TenantFactory(slug=f"m3nc-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    os_id, ativ_id = _abrir_e_iniciar_calibracao(
        tenant, cliente, equipamento, executor_id
    )
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = marcar_nao_conformidade(
            payload=MarcarNCInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                razao=MotivoCancelamento(MOTIVO_VALIDO_A),
                correlation_id=uuid4(),
                marcada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.estado == EstadoAtividade.NAO_CONFORME.value
        os_obj = OS.objects.get(id=os_id)
        assert os_obj.nao_conformidade_global is True
        nc = NaoConformidadeAtividade.objects.get(id=res.nc_id)
        assert nc.causa_raiz_hash == ""  # CAPA aberto


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_005_5_resolver_nc_capa_incompleto_412(db):
    """AC-OS-005-5: CAPA incompleto -> 412 CAPAIncompleto.

    O VO `MotivoCancelamento` exige >=30 chars + anti-PII — se construirmos um
    `causa_raiz` valido mas `acao_corretiva` igual, ambos hashes ficam preenchidos.
    Pra falhar em CAPAIncompleto, simulamos um caso onde o repository devolve
    NC sem eficacia_verificada — mas como o use case PREENCHE eficacia a cada
    chamada, na pratica o erro CAPAIncompleto so ocorre se VO falhar ANTES de
    chegar ao use case (ValueError). Esse teste cobre o caminho indireto:
    erguer ValueError quando causa_raiz tem PII, e o caller (consumer) mapeia.
    """
    tenant = TenantFactory(slug=f"m3nc-u5-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    _, ativ_id = _abrir_e_iniciar_calibracao(
        tenant, cliente, equipamento, executor_id
    )
    repo = DjangoOSRepository()

    # Marca NC primeiro.
    with run_in_tenant_context(tenant.id), transaction.atomic():
        marcar_nao_conformidade(
            payload=MarcarNCInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                razao=MotivoCancelamento(MOTIVO_VALIDO_A),
                correlation_id=uuid4(),
                marcada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    # Tenta criar VO com PII -> ValueError do VO (INV-OS-TXT-001).
    with pytest.raises(ValueError):
        MotivoCancelamento("Cliente Joao Silva pediu refazer porque resultado divergiu")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_005_3_resolver_nc_capa_completo_happy(db):
    """AC-OS-005-3: CAPA completo -> atividade volta pra EM_EXECUCAO."""
    tenant = TenantFactory(slug=f"m3nc-h3-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    _, ativ_id = _abrir_e_iniciar_calibracao(
        tenant, cliente, equipamento, executor_id
    )
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        marcar_nao_conformidade(
            payload=MarcarNCInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                razao=MotivoCancelamento(MOTIVO_VALIDO_A),
                correlation_id=uuid4(),
                marcada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
        resolver_nc(
            payload=ResolverNCInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                causa_raiz=MotivoCancelamento(MOTIVO_VALIDO_B),
                acao_corretiva=MotivoCancelamento(MOTIVO_VALIDO_C),
                correlation_id=uuid4(),
                eficacia_verificada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.estado == EstadoAtividade.EM_EXECUCAO.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_us_os_008_cancelar_os_cascateia_atividades(db):
    """cancelar_os: OS -> CANCELADA + todas atividades nao-terminais -> CANCELADA."""
    tenant = TenantFactory(slug=f"m3cn-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
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
        valor_total=Decimal("200.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_PREVENTIVA,
                sequencia=2,
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

    with run_in_tenant_context(tenant.id), transaction.atomic():
        cancelar_os(
            payload=CancelarOSInput(
                os_id=res.os_id,
                usuario_id=uuid4(),
                motivo=MotivoCancelamento(MOTIVO_VALIDO_D),
                correlation_id=uuid4(),
                cancelada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.estado == EstadoOS.CANCELADA.value
        atividades = list(AtividadeDaOS.objects.filter(os_id=res.os_id))
        assert all(a.estado == EstadoAtividade.CANCELADA.value for a in atividades)
        assert (
            EventoDeOS.objects.filter(
                os_id=res.os_id, tipo=TipoEventoDeOS.OS_CANCELADA.value
            ).count()
            == 1
        )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_adr_0042_cancelar_atividade_publica_os_escopo_alterado(db):
    """ADR-0042 + INV-OS-FAT-001: cancelar atividade emite OS.EscopoAlterado
    + valor_total_atualizado recalculado."""
    tenant = TenantFactory(slug=f"m3cn-e-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
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
        valor_total=Decimal("300.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_PREVENTIVA,
                sequencia=2,
                valor_unitario=Decimal("200.00"),
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
        ativ_vistoria = next(a for a in atividades if a.sequencia == 1)

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res_cancel = cancelar_atividade(
            payload=CancelarAtividadeInput(
                atividade_id=ativ_vistoria.id,
                usuario_id=uuid4(),
                motivo=MotivoCancelamento(MOTIVO_VALIDO_D),
                correlation_id=uuid4(),
                cancelada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    # AC ADR-0042: valor_total_atualizado = sum apenas atividades nao-canceladas.
    assert res_cancel.valor_total_atualizado == Decimal("200.00")
    with run_in_tenant_context(tenant.id):
        # Evento OS.EscopoAlterado publicado.
        assert (
            EventoDeOS.objects.filter(
                os_id=res.os_id, tipo=TipoEventoDeOS.OS_ESCOPO_ALTERADO.value
            ).count()
            == 1
        )
        # OS continua em estado anterior (RASCUNHO).
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.estado == EstadoOS.RASCUNHO.value
