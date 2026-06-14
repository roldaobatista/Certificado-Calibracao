"""Testes de integracao do use case `adicionar_atividade` (T-OS-048).

Cobre AC-OS-002-1 (happy), AC-OS-002-2 (OS terminal), AC-OS-002-4
(sequencia pos-terminal) — todos contra `DjangoOSRepository` real.
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
from src.application.operacao.os.adicionar_atividade import (
    AdicionarAtividadeInput,
    ErroAdicionarAtividade,
    adicionar_atividade,
)
from src.domain.operacao.os.entities import OSSnapshot
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import AtividadeDaOS, EventoDeOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _setup_cliente_equipamento(tenant):
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
            tag=f"M3-AT-{sfx}",
            numero_serie=f"NS-AT-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_os_basica(tenant, cliente, equipamento) -> AbrirOSInput:
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
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_CORRETIVA,
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
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        return abrir_os_via_orcamento(payload=payload, repository=repo)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_002_1_happy_adiciona_atividade_pendente(db):
    """AC-OS-002-1: OS nao-terminal aceita nova atividade em PENDENTE."""
    tenant = TenantFactory(slug=f"m3at-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)
    res_abrir = _abrir_os_basica(tenant, cliente, equipamento)

    repo = DjangoOSRepository()
    payload = AdicionarAtividadeInput(
        os_id=res_abrir.os_id,
        tipo=TipoAtividade.VISTORIA,
        sequencia=2,
        valor_unitario=Decimal("75.00"),
        correlation_id=uuid4(),
        solicitada_em=datetime.now(UTC),
        solicitada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        resultado = adicionar_atividade(payload=payload, repository=repo)

    assert resultado.sequencia == 2
    with run_in_tenant_context(tenant.id):
        atividades = list(
            AtividadeDaOS.objects.filter(os_id=res_abrir.os_id).order_by("sequencia")
        )
        assert len(atividades) == 2
        assert atividades[1].tipo == TipoAtividade.VISTORIA.value
        assert atividades[1].estado == EstadoAtividade.PENDENTE.value

        eventos = list(
            EventoDeOS.objects.filter(
                os_id=res_abrir.os_id,
                tipo=TipoEventoDeOS.ATIVIDADE_ADICIONADA.value,
            )
        )
        assert len(eventos) == 1
        assert eventos[0].payload_data["sequencia"] == 2


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_002_2_unhappy_os_terminal_bloqueia_412(db):
    """AC-OS-002-2: OS em CONCLUIDA bloqueia adicao -> 412 OSEmEstadoTerminal."""
    tenant = TenantFactory(slug=f"m3at-u2-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)
    res_abrir = _abrir_os_basica(tenant, cliente, equipamento)

    # Forca OS pra estado terminal via UPDATE direto no adapter.
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        snap = repo.get_os_by_id(res_abrir.os_id)
        assert snap is not None
        # Reusa snapshot trocando estado.
        terminal = OSSnapshot(
            id=snap.id,
            tenant_id=snap.tenant_id,
            numero_os=snap.numero_os,
            cliente_id=snap.cliente_id,
            cliente_referencia_hash=snap.cliente_referencia_hash,
            cliente_key_id=snap.cliente_key_id,
            equipamento_id=snap.equipamento_id,
            equipamento_recebimento_id=snap.equipamento_recebimento_id,
            orcamento_origem_id=snap.orcamento_origem_id,
            os_origem_id=snap.os_origem_id,
            sucessao_societaria_id=snap.sucessao_societaria_id,
            estado=EstadoOS.CONCLUIDA,
            tipo_predominante="manutencao_corretiva",
            nao_conformidade_global=False,
            valor_total=snap.valor_total,
            valor_total_atualizado=snap.valor_total_atualizado,
            analise_critica_id=snap.analise_critica_id,
            analise_critica_snapshot_hash=snap.analise_critica_snapshot_hash,
            regra_decisao_acordada=snap.regra_decisao_acordada,
            criada_em=snap.criada_em,
            atualizada_em=snap.atualizada_em,
            criada_por_user_id=snap.criada_por_user_id,
        )
        repo.salvar_os(terminal)

    payload = AdicionarAtividadeInput(
        os_id=res_abrir.os_id,
        tipo=TipoAtividade.VISTORIA,
        sequencia=2,
        valor_unitario=Decimal("75.00"),
        correlation_id=uuid4(),
        solicitada_em=datetime.now(UTC),
        solicitada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAdicionarAtividade) as exc:
        adicionar_atividade(payload=payload, repository=repo)

    assert exc.value.codigo == "OSEmEstadoTerminal"
    assert exc.value.http_status == 412


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_os_002_4_unhappy_sequencia_invalida_pos_terminal_412(db):
    """AC-OS-002-4: sequencia <= menor concluida -> 412 SequenciaInvalidaPosTerminal."""
    tenant = TenantFactory(slug=f"m3at-u4-{uuid4().hex[:6]}")
    cliente, equipamento = _setup_cliente_equipamento(tenant)
    res_abrir = _abrir_os_basica(tenant, cliente, equipamento)

    # Forca atividade 1 a CONCLUIDA via UPDATE direto.
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id):
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        assert len(atividades) == 1
        original = atividades[0]
        from src.domain.operacao.os.entities import AtividadeSnapshot

        concluida = AtividadeSnapshot(
            id=original.id,
            tenant_id=original.tenant_id,
            os_id=original.os_id,
            tipo=original.tipo,
            sequencia=original.sequencia,
            estado=EstadoAtividade.CONCLUIDA,
            tecnico_executor_id=original.tecnico_executor_id,
            agendada_para=original.agendada_para,
            iniciada_em=original.iniciada_em,
            concluida_em=datetime.now(UTC),
            valor_unitario_snapshot=original.valor_unitario_snapshot,
            link_modulo_tecnico_id=original.link_modulo_tecnico_id,
            geo_lat=original.geo_lat,
            geo_long=original.geo_long,
            geo_municipio_hash=original.geo_municipio_hash,
            equipamento_id=original.equipamento_id,
            tipo_bloqueia_concorrencia=original.tipo_bloqueia_concorrencia,
        )
        repo.salvar_atividade(concluida)

    # Tenta adicionar com sequencia=1 (= menor concluida) -> deve bloquear.
    payload = AdicionarAtividadeInput(
        os_id=res_abrir.os_id,
        tipo=TipoAtividade.VISTORIA,
        sequencia=1,
        valor_unitario=Decimal("75.00"),
        correlation_id=uuid4(),
        solicitada_em=datetime.now(UTC),
        solicitada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAdicionarAtividade) as exc:
        adicionar_atividade(payload=payload, repository=repo)

    assert exc.value.codigo == "SequenciaInvalidaPosTerminal"
    assert exc.value.http_status == 412
