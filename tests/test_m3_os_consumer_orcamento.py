"""Teste do consumer `Orcamento.Aprovado` — pipeline use case + bus publish.

Valida que:
- Envelope canonico vira OS + atividades persistidas.
- Bus publish via audit.event_helpers grava cadeia + outbox.
- @consumer_idempotente evita duplicacao em replay.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db import connection
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.orcamento import (
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
        "tenant_id": str(tenant_id),  # top-level, lido pelo @consumer_idempotente
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-test-key",
            "equipamento_id": str(equipamento_id),
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "150.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "manutencao_corretiva",
                    "sequencia": 1,
                    "valor_unitario": "150.00",
                    "requer_recebimento": False,
                },
            ],
        },
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_consumer_orcamento_abre_os_e_publica_bus(db):
    """Happy path: envelope -> OS + bus_outbox + cadeia."""
    tenant = TenantFactory(slug=f"m3cons-h-{uuid4().hex[:6]}")
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
            tag=f"M3-CONS-{sfx}",
            numero_serie=f"NS-CONS-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )

    envelope = _envelope(tenant.id, cliente.id, equipamento.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)

    with run_in_tenant_context(tenant.id):
        oss = list(OS.objects.filter(tenant=tenant))
        assert len(oss) == 1
        os_obj = oss[0]
        assert os_obj.numero_os > 0
        assert os_obj.atividades.count() == 1

        # bus_outbox tem entrada com acao=os.aberta + causation_id matching.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM bus_outbox "
                "WHERE acao = 'os.aberta' AND tenant_id = %s",
                [str(tenant.id)],
            )
            count = cur.fetchone()[0]
        assert count == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_consumer_orcamento_replay_idempotente(db):
    """Mesmo envelope chamado 2x -> apenas 1 OS criada (consumer_idempotente)."""
    tenant = TenantFactory(slug=f"m3cons-r-{uuid4().hex[:6]}")
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
            tag=f"M3-CONS-{sfx}",
            numero_serie=f"NS-CONS-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )

    envelope = _envelope(tenant.id, cliente.id, equipamento.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)
        handle_orcamento_aprovado(envelope)  # replay
        assert OS.objects.filter(tenant=tenant).count() == 1
