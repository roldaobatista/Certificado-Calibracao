"""Anti-regressao INV-OS-EQP-001 (AC-OS-001-5) — equipamento BAIXADO/DESCARTADO
bloqueia abertura de OS.

Pre-check do consumer `Orcamento.Aprovado` (T-OS-044): `equipamento.status IN
{sucata, extraviado}` -> erro `EquipamentoBaixadoEmOS` http 422, sem criar OS.

≥3 testes: happy (ativo abre), unhappy (sucata bloqueia), cross-status
(extraviado bloqueia).
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
from src.infrastructure.ordens_servico.models import OS

from tests.factories import TenantFactory


def _envelope(tenant_id, cliente_id, equipamento_id):
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
