"""Eventos e fan-out do caixa_tecnico — testes (Fatia 3b / T-CT-051).

Cobre:
  (a) assert_acao_canonica não falha para os 9 slugs caixa_tecnico.* (INV-008);
  (b) consumer colaborador.desligado idempotente (replay e já-desligado → no-op);
  (c) fan-out: registrar o consumer NÃO engole o da agenda (mesma ação — R8);
  (d) perfil lido do ENVELOPE (consumer funciona sem perfil-context; não usa
      obter_perfil_tenant_corrente no worker);
  (e) prestacao.fechada publicada dentro do atomic → BusOutbox tem linha após commit.

IMPORTANTE: usa --reuse-db (NUNCA --create-db).
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest
from src.infrastructure.audit.acoes_canonicas import (
    ACOES_CAIXA_TECNICO,
    assert_acao_canonica,
)
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.caixa_tecnico.consumers import handle_colaborador_desligado
from src.infrastructure.caixa_tecnico.models import CaixaTecnico as CaixaTecnicoModel
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

_DBS = ["default", "breaker_writer"]
_HASH_V1 = "v1"


def _envelope(*, acao, tenant_id, perfil="D", payload=None, event_id=None):
    """Envelope do bus (molde agenda `_envelope`)."""
    return {
        "event_id": str(event_id or uuid4()),
        "acao": acao,
        "tenant_id": str(tenant_id),
        "perfil_no_evento": perfil,
        "payload": payload or {},
    }


def _cria_caixa_para(tenant, colaborador_id):
    """CaixaTecnico cujo tecnico_referencia_hash casa com o colaborador_id (mesmo helper)."""
    tecnico_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant.id).split(":", 1)[1]
    with run_in_tenant_context(tenant.id):
        return CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )


def _tenant():
    return TenantFactory(perfil_b=True, slug=f"ct-3b-{uuid4().hex[:8]}")


# (a) =======================================================================
def test_assert_acao_canonica_9_slugs():
    """Os 9 slugs caixa_tecnico.* são canônicos (assert_acao_canonica não levanta)."""
    assert len(ACOES_CAIXA_TECNICO) == 9
    for slug in ACOES_CAIXA_TECNICO:
        assert_acao_canonica(slug)  # não levanta (R4 — senão todo publish caía)
    with pytest.raises(ValueError):
        assert_acao_canonica("caixa_tecnico.inexistente.acao")


# (c) =======================================================================
def test_fanout_nao_engole_consumer_agenda():
    """Registrar o consumer do caixa_tecnico NÃO remove o da agenda (mesma ação — R8)."""
    from src.infrastructure.agenda.consumers.colaborador_eventos import (
        handle_colaborador_desligado as agenda_handler,
    )
    from src.infrastructure.audit.outbox_worker import _REGISTRY, registrar_consumer

    for fn in (agenda_handler, handle_colaborador_desligado):
        try:
            registrar_consumer("colaborador.desligado", fn)
        except ValueError:
            pass  # já registrado no AppConfig.ready()

    consumers = _REGISTRY.get("colaborador.desligado", [])
    assert agenda_handler in consumers, "consumer da agenda foi engolido"
    assert handle_colaborador_desligado in consumers, "consumer do caixa_tecnico não registrado"
    assert len(consumers) >= 2  # fan-out aditivo


# (b) + (d) =================================================================
@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_desliga_caixa():
    """colaborador.desligado → CaixaTecnico marcado como desligado (fail-closed)."""
    tenant = _tenant()
    colaborador_id = uuid4()
    caixa = _cria_caixa_para(tenant, colaborador_id)
    env = _envelope(
        acao="colaborador.desligado",
        tenant_id=tenant.id,
        payload={"colaborador_id": str(colaborador_id)},
    )
    with run_in_tenant_context(tenant.id):
        handle_colaborador_desligado(env)
        caixa.refresh_from_db()
    assert caixa.desligado_em is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_idempotente_replay_e_ja_desligado():
    """Replay (mesmo event_id) → no-op (decorator); já-desligado (event_id novo) → no-op (handler)."""
    tenant = _tenant()
    colaborador_id = uuid4()
    caixa = _cria_caixa_para(tenant, colaborador_id)
    eid = uuid4()
    env = _envelope(
        acao="colaborador.desligado",
        tenant_id=tenant.id,
        event_id=eid,
        payload={"colaborador_id": str(colaborador_id)},
    )
    with run_in_tenant_context(tenant.id):
        handle_colaborador_desligado(env)
        caixa.refresh_from_db()
        dt1 = caixa.desligado_em
        assert dt1 is not None

        # replay: MESMO event_id → marca de idempotência bloqueia (no-op)
        handle_colaborador_desligado(env)
        caixa.refresh_from_db()
        assert caixa.desligado_em == dt1

        # event_id NOVO, mas caixa já desligado → handler no-opa (esta_desligado)
        env2 = _envelope(
            acao="colaborador.desligado",
            tenant_id=tenant.id,
            payload={"colaborador_id": str(colaborador_id)},
        )
        handle_colaborador_desligado(env2)
        caixa.refresh_from_db()
        assert caixa.desligado_em == dt1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_sem_caixa_noop():
    """colaborador sem caixa → no-op (sem erro)."""
    tenant = _tenant()
    env = _envelope(
        acao="colaborador.desligado",
        tenant_id=tenant.id,
        payload={"colaborador_id": str(uuid4())},
    )
    with run_in_tenant_context(tenant.id):
        handle_colaborador_desligado(env)  # não levanta


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_perfil_lido_do_envelope():
    """(d) perfil vem do envelope; consumer funciona sem perfil-context (não usa corrente)."""
    tenant = _tenant()
    colaborador_id = uuid4()
    caixa = _cria_caixa_para(tenant, colaborador_id)
    # perfil só no envelope; nenhum perfil de request/contexto é setado
    env = _envelope(
        acao="colaborador.desligado",
        tenant_id=tenant.id,
        perfil="A",
        payload={"colaborador_id": str(colaborador_id)},
    )
    with run_in_tenant_context(tenant.id):
        handle_colaborador_desligado(env)
        caixa.refresh_from_db()
    assert caixa.desligado_em is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_fail_closed_procede_sem_perfil_no_evento():
    """(fail-closed) Envelope SEM perfil_no_evento → desligamento PROCEDE (estado seguro = inativo).

    Diferenciador da fatia vs molde agenda (que no-opa sem perfil): aqui não marcar deixaria
    técnico desligado com caixa ATIVO (fail-OPEN inseguro). Trava contra regressão que copie
    o early-return da agenda.
    """
    tenant = _tenant()
    colaborador_id = uuid4()
    caixa = _cria_caixa_para(tenant, colaborador_id)
    env = _envelope(
        acao="colaborador.desligado",
        tenant_id=tenant.id,
        payload={"colaborador_id": str(colaborador_id)},
    )
    env.pop("perfil_no_evento")  # envelope SEM perfil
    assert "perfil_no_evento" not in env
    with run_in_tenant_context(tenant.id):
        handle_colaborador_desligado(env)
        caixa.refresh_from_db()
    assert caixa.desligado_em is not None, "fail-closed: deve desligar mesmo sem perfil no envelope"


# (e) =======================================================================
@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_prestacao_fechada_publica_outbox():
    """Fechar prestação publica caixa_tecnico.prestacao.fechada no BusOutbox (dentro do atomic)."""
    from rest_framework.test import APIClient
    from src.infrastructure.audit.models import BusOutbox

    from tests.test_caixa_tecnico_api_fatia2 import (
        URL_FECHAR,
        _autenticar,
        _cenario,
        _cria_caixa,
        _post,
    )

    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    hoje = date.today()
    payload = {
        "caixa_id": str(caixa.id),
        "periodo_de": (hoje - timedelta(days=30)).isoformat(),
        "periodo_ate": (hoje - timedelta(days=1)).isoformat(),
    }
    with run_in_tenant_context(c["tenant"].id):
        antes = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id, acao="caixa_tecnico.prestacao.fechada"
        ).count()

    r = _post(client, URL_FECHAR, payload)
    assert r.status_code == 201, r.content

    with run_in_tenant_context(c["tenant"].id):
        depois = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id, acao="caixa_tecnico.prestacao.fechada"
        ).count()
    assert depois == antes + 1
