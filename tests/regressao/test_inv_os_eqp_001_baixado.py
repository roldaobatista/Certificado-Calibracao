"""Anti-regressao INV-OS-EQP-001 (AC-OS-001-5) — equipamento BAIXADO/DESCARTADO
bloqueia abertura de OS.

Pre-check do consumer `Orcamento.Aprovado` (T-OS-044): `equipamento.status IN
{sucata, extraviado}` -> erro `EquipamentoBaixadoEmOS` http 422, sem criar OS.

≥3 testes base: happy (ativo abre), unhappy (sucata bloqueia), cross-status
(extraviado bloqueia).

Cenarios multi-equipamento (AC-OSME-004 / retrofit ADR-0082):
- unhappy_multi: 2 itens com equipamentos distintos, 1 SUCATA -> 422 (o ativo nao salva a abertura).
- happy_multi: 2 equipamentos ativos -> OS multi-equipamento abre OK (OS.equipamento=NULL).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.orcamento import (
    EquipamentoBaixadoEmOSError,
    handle_orcamento_aprovado,
)
from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS

from tests.factories import TenantFactory


def _envelope(tenant_id, cliente_id, equipamento_id):
    """Envelope v1 legado — equipamento_id no header; item sem equipamento_id proprio."""
    correlation_id = uuid4()
    return {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-test",
            "equipamento_id": str(equipamento_id),
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "100.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "vistoria",
                    "sequencia": 1,
                    "valor_unitario": "100.00",
                    "requer_recebimento": False,
                },
            ],
        },
    }


def _envelope_multi(tenant_id, cliente_id, equipamento_id_1, equipamento_id_2):
    """Envelope v2 multi-equipamento — 2 itens com equipamento_id POR ITEM (ADR-0082).

    Usado pelos cenarios multi-equipamento do INV-OS-EQP-001.
    """
    correlation_id = uuid4()
    return {
        "correlation_id": str(correlation_id),
        "causation_id": str(correlation_id),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-test",
            "equipamento_id": None,
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "200.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "vistoria",
                    "sequencia": 1,
                    "valor_unitario": "100.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equipamento_id_1),
                },
                {
                    "tipo": "vistoria",
                    "sequencia": 2,
                    "valor_unitario": "100.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equipamento_id_2),
                },
            ],
        },
    }


def _setup(tenant, status: str = EquipamentoStatus.ATIVO):
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
            tag=f"INV-EQP-{sfx}",
            numero_serie=f"NS-EQP-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
            status=status,
        )
    return cliente, equipamento


def _create_equipamento(tenant, cliente, status: str = EquipamentoStatus.ATIVO):
    """Cria um equipamento adicional para cenarios multi-equipamento."""
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV-EQP2-{sfx}",
            numero_serie=f"NS-EQP2-{sfx}",
            fabricante="Toledo",
            modelo="Y",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
            status=status,
        )
    return equipamento


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_eqp_001_happy_ativo_abre_os(db):
    tenant = TenantFactory(slug=f"inv-eqp-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant, EquipamentoStatus.ATIVO)
    envelope = _envelope(tenant.id, cliente.id, equipamento.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)
        assert OS.objects.filter(equipamento=equipamento).count() == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_eqp_001_unhappy_sucata_bloqueia(db):
    tenant = TenantFactory(slug=f"inv-eqp-s-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant, EquipamentoStatus.SUCATA)
    envelope = _envelope(tenant.id, cliente.id, equipamento.id)

    with run_in_tenant_context(tenant.id), pytest.raises(EquipamentoBaixadoEmOSError) as exc:
        handle_orcamento_aprovado(envelope)
    assert exc.value.codigo == "EquipamentoBaixadoEmOS"
    assert exc.value.http_status == 422
    with run_in_tenant_context(tenant.id):
        assert OS.objects.filter(equipamento=equipamento).count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_eqp_001_unhappy_extraviado_bloqueia(db):
    tenant = TenantFactory(slug=f"inv-eqp-x-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant, EquipamentoStatus.EXTRAVIADO)
    envelope = _envelope(tenant.id, cliente.id, equipamento.id)

    with run_in_tenant_context(tenant.id), pytest.raises(EquipamentoBaixadoEmOSError):
        handle_orcamento_aprovado(envelope)
    with run_in_tenant_context(tenant.id):
        assert OS.objects.filter(equipamento=equipamento).count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_eqp_001_unhappy_multi_um_sucata_bloqueia_toda_os(db):
    """Unhappy multi-equip: OS via envelope v2 com 2 itens de equipamentos distintos,
    1 deles SUCATA -> 422 EquipamentoBaixadoEmOS. O equipamento ativo nao salva a
    abertura — a OS inteira e rejeitada (AC-OSME-004 / pre-check todos os itens).
    """
    tenant = TenantFactory(slug=f"inv-eqp-mu-{uuid4().hex[:6]}")
    cliente, equip_ativo = _setup(tenant, EquipamentoStatus.ATIVO)
    equip_sucata = _create_equipamento(tenant, cliente, EquipamentoStatus.SUCATA)
    envelope = _envelope_multi(tenant.id, cliente.id, equip_ativo.id, equip_sucata.id)

    with run_in_tenant_context(tenant.id), pytest.raises(EquipamentoBaixadoEmOSError) as exc:
        handle_orcamento_aprovado(envelope)
    assert exc.value.codigo == "EquipamentoBaixadoEmOS"
    assert exc.value.http_status == 422
    # Nenhuma OS criada — transacao atomica inteira foi abortada.
    with run_in_tenant_context(tenant.id):
        assert OS.objects.count() == 0
        assert AtividadeDaOS.objects.count() == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_eqp_001_happy_multi_dois_ativos_abre_os_multi_equipamento(db):
    """Happy multi-equip: OS via envelope v2 com 2 itens de equipamentos DISTINTOS
    e ambos ATIVOS -> OS multi-equipamento criada com sucesso. OS.equipamento_id=NULL
    (D-OSME-2); cada atividade carrega o SEU equipamento_id (ADR-0082).
    """
    tenant = TenantFactory(slug=f"inv-eqp-mh-{uuid4().hex[:6]}")
    cliente, equip_1 = _setup(tenant, EquipamentoStatus.ATIVO)
    equip_2 = _create_equipamento(tenant, cliente, EquipamentoStatus.ATIVO)
    envelope = _envelope_multi(tenant.id, cliente.id, equip_1.id, equip_2.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)
        # OS multi-equipamento: equipamento_id=NULL na cabeca (D-OSME-2).
        os_obj = OS.objects.get()
        assert os_obj.equipamento_id is None, "OS multi-equip deve ter equipamento_id=NULL no header"
        # Cada atividade tem o SEU equipamento_id (ADR-0082).
        atividades = list(AtividadeDaOS.objects.filter(os=os_obj))
        assert len(atividades) == 2
        equip_ids_nas_atividades = {str(a.equipamento_id) for a in atividades}
        assert str(equip_1.id) in equip_ids_nas_atividades
        assert str(equip_2.id) in equip_ids_nas_atividades
