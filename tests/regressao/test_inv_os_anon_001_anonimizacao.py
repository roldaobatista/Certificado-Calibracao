"""Anti-regressao INV-OS-ANON-001 (T-OS-112) — anonimizacao Zona A/B
cliente x OS aberta + propagacao do consumer.

INV-OS-ANON-001: Cliente com OS em RASCUNHO/AGENDADA/EM_EXECUCAO bloqueia
anonimizacao Zona A/B (ADR-0021). Predicate `cliente_tem_os_aberta()` no
modulo Clientes consulta OS abertas; consumer `os.consumer.cliente_anonimizado`
e defesa em profundidade — preserva audit via `cliente_referencia_hash`
ja gravado no snapshot da abertura.

≥3 testes: happy (anonimizacao com OS terminal zera cliente_id e preserva
hash), unhappy (anonimizacao com OS aberta gera warning de defesa em
profundidade + ainda zera cliente_id), cross-tenant (anonimizacao em
tenant A nao toca OS de tenant B).
"""

from __future__ import annotations

import logging
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
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.cliente import (
    handle_cliente_anonimizado,
)
from src.infrastructure.ordens_servico.models import OS
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
            tag=f"INV-ANON-{sfx}",
            numero_serie=f"NS-ANON-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_os(tenant, cliente, equipamento):
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        return abrir_os_via_orcamento(
            payload=AbrirOSInput(
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
            ),
            repository=repo,
        )


def _envelope_anonimizado(tenant_id, cliente_id):
    return {
        "event_id": str(uuid4()),
        "correlation_id": str(uuid4()),
        "causation_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "cliente.anonimizado",
        "payload": {"cliente_id": str(cliente_id), "tenant_id": str(tenant_id)},
    }


# =============================================================
# Happy: OS terminal -> cliente_id NULL + hash preservado
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anon_001_happy_os_terminal_zera_cliente_e_preserva_hash(db):
    """Happy: cliente com OS em estado terminal eh anonimizavel; consumer
    zera cliente_id em TODAS as OS do cliente, preservando hash."""
    tenant = TenantFactory(slug=f"inv-anon-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res = _abrir_os(tenant, cliente, equipamento)

    # Forca OS pra estado terminal antes da anonimizacao.
    with run_in_tenant_context(tenant.id):
        OS.objects.filter(id=res.os_id).update(estado="concluida")

    cliente_id_original = cliente.id
    envelope = _envelope_anonimizado(tenant.id, cliente_id_original)
    with run_in_tenant_context(tenant.id):
        handle_cliente_anonimizado(envelope)

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.cliente_id is None, "cliente_id deveria ter sido zerado"
        assert os_obj.cliente_referencia_hash == "a" * 64, (
            "cliente_referencia_hash deveria ter sido preservado (snapshot imutavel)"
        )
        assert os_obj.cliente_key_id == "kms"


# =============================================================
# Unhappy: OS aberta dispara warning de defesa em profundidade
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anon_001_unhappy_os_aberta_warning_defesa_em_profundidade(db, caplog):
    """Unhappy: consumer recebe Cliente.Anonimizado mas existe OS aberta —
    Marco 1 deveria ter bloqueado via predicate; consumer registra warning
    e ainda assim zera cliente_id (defesa em profundidade nao re-anuncia)."""
    tenant = TenantFactory(slug=f"inv-anon-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    res = _abrir_os(tenant, cliente, equipamento)

    # OS em estado RASCUNHO (nao-terminal) — anonimizacao deveria ter sido
    # bloqueada pelo predicate em Marco 1. Aqui chega = bug de chamador.
    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.estado == "rascunho", "setup precisa garantir RASCUNHO"

    envelope = _envelope_anonimizado(tenant.id, cliente.id)
    with run_in_tenant_context(tenant.id), caplog.at_level(
        logging.WARNING, logger="src.infrastructure.ordens_servico.consumers.cliente"
    ):
        handle_cliente_anonimizado(envelope)

    # Warning de defesa em profundidade emitido.
    mensagens = [r.getMessage() for r in caplog.records]
    assert any("anonimizacao deveria ter sido bloqueada" in m for m in mensagens), (
        f"warning INV-OS-ANON-001 nao emitido; mensagens={mensagens}"
    )

    # E ainda assim zerou cliente_id (idempotente — consumer faz UPDATE
    # nao-condicional pra garantir convergencia).
    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.cliente_id is None
        assert os_obj.cliente_referencia_hash == "a" * 64


# =============================================================
# Cross-tenant: anonimizacao do tenant A nao toca OS do tenant B
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anon_001_cross_tenant_anonimizacao_a_nao_toca_os_b(db):
    """Cross-tenant: anonimizar cliente em tenant A NAO mexe nas OS de
    tenant B mesmo que UUIDs colidissem por azar (RLS + filtro tenant)."""
    tenant_a = TenantFactory(slug=f"inv-anon-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-anon-ctb-{uuid4().hex[:6]}")
    cliente_a, eq_a = _setup(tenant_a)
    cliente_b, eq_b = _setup(tenant_b)
    res_a = _abrir_os(tenant_a, cliente_a, eq_a)
    res_b = _abrir_os(tenant_b, cliente_b, eq_b)

    # Anonimiza apenas o cliente A. Consumer roda dentro do contexto do
    # tenant A; RLS bloqueia leitura/update de OS de outro tenant.
    envelope = _envelope_anonimizado(tenant_a.id, cliente_a.id)
    with run_in_tenant_context(tenant_a.id):
        handle_cliente_anonimizado(envelope)

    with run_in_tenant_context(tenant_a.id):
        os_a = OS.objects.get(id=res_a.os_id)
        assert os_a.cliente_id is None, "OS tenant A deveria ter cliente zerado"

    with run_in_tenant_context(tenant_b.id):
        os_b = OS.objects.get(id=res_b.os_id)
        assert os_b.cliente_id == cliente_b.id, (
            "OS tenant B NAO deveria ter sido tocada pela anonimizacao do tenant A"
        )
        assert os_b.cliente_referencia_hash == "a" * 64
