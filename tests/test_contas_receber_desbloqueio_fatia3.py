"""Fatia 3c — desbloqueio ao quitar (T-CR-045 / D-CR-11). Verificação 3 (parte desbloqueio).

Cobre o consumer novo de `clientes` para `contas_receber.pago` (INV-FIN-REATIV-001 /
GATE-CLI-6):
  - happy: quitação zera a dívida vencida → encerra bloqueio automático + publica
    `cliente.desbloqueado`;
  - AC-CR-006-2: outra vencida em aberto → mantém bloqueio;
  - pagamento parcial (título vira `parcialmente_pago`, ainda vencido) → mantém;
  - bloqueio MANUAL (quebra de confiança) NÃO é desfeito por pagamento;
  - cliente anonimizado (cliente_atual_id NULL) → no-op resiliente;
  - sem bloqueio ativo → no-op (não publica desbloqueio);
  - idempotência: replay do mesmo event_id desbloqueia 1x só.

Também cobre as queries read-only expostas por CR (`queries_desbloqueio`).
"""

from __future__ import annotations

import json as _json
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.db import connection
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel
from src.infrastructure.clientes.bloqueio import (
    CAUSATION_MANUAL_DECISAO_ADMIN,
    CAUSATION_TITULO_VENCIDO,
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
    MOTIVO_MANUAL_QUEBRA_CONFIANCA,
)
from src.infrastructure.clientes.consumers.contas_receber_eventos import (
    handle_contas_receber_pago,
)
from src.infrastructure.contas_receber import queries_desbloqueio
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _hash_cliente() -> str:
    return uuid4().hex + uuid4().hex


def _criar_cliente(tenant, *, email: str = "cli@cliente.local"):
    from src.infrastructure.clientes.models import Cliente, TipoPessoa

    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="Cliente Teste Desbloqueio",
        email=email,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


def _criar_titulo(
    tenant,
    *,
    estado: EstadoTitulo,
    dias_vencido: int,
    cliente_id,
    perfil: str = "A",
) -> Titulo:
    """Cria um Titulo no estado pedido. `dias_vencido` define data_vencimento (pode ser <0=futuro)."""
    titulo = Titulo(
        titulo_id=uuid4(),
        tenant_id=tenant.id,
        cliente_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=cliente_id, hash_original=_hash_cliente(), key_id="v1"
        ),
        valor_original=Dinheiro(centavos=100000, moeda="BRL"),
        data_emissao=date.today() - timedelta(days=dias_vencido + 30),
        data_vencimento=date.today() - timedelta(days=dias_vencido),
        estado=estado,
        meio=MeioCobranca.BOLETO,
        categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
        perfil_no_evento=perfil,
        origem=OrigemTitulo.MANUAL,
        revision=0,
        criado_em=datetime.now(UTC),
    )
    DjangoTituloRepository().salvar_novo_titulo(titulo)
    return titulo


def _criar_bloqueio(tenant, cliente, *, motivo: str = MOTIVO_AUTOMATICO_INADIMPLENCIA_90D):
    from src.infrastructure.clientes.models import ClienteBloqueio

    causation = (
        CAUSATION_TITULO_VENCIDO
        if motivo == MOTIVO_AUTOMATICO_INADIMPLENCIA_90D
        else CAUSATION_MANUAL_DECISAO_ADMIN
    )
    return ClienteBloqueio.objects.create(
        cliente=cliente,
        tenant=tenant,
        motivo_categoria=motivo,
        motivo_observacao="",
        justificativa_bruta="bloqueio de teste para a fatia de desbloqueio (>=30 chars)",
        causation_type=causation,
        confirmacao_comunicacao_previa=True,
        bloqueado_por_usuario_id=None,
    )


def _rodar_consumer(tenant_id, titulo_id, *, event_id=None) -> None:
    envelope = {
        "event_id": str(event_id or uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "contas_receber.pago",
        "payload": {"titulo_id": str(titulo_id), "novo_estado": "pago"},
    }
    with run_in_tenant_context(tenant_id):
        handle_contas_receber_pago(envelope)


def _bloqueio_recarregado(tenant_id, bloqueio_id):
    from src.infrastructure.clientes.models import ClienteBloqueio

    with run_in_tenant_context(tenant_id):
        return ClienteBloqueio.objects.get(id=bloqueio_id)


def _eventos_desbloqueado(tenant_id) -> list[dict]:
    with run_in_tenant_context(tenant_id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE acao = %s",
                ["cliente.desbloqueado"],
            )
            rows = cur.fetchall()
    return [r[0] if isinstance(r[0], dict) else _json.loads(r[0]) for r in rows]


# ============================================================
# Queries read-only expostas por CR (queries_desbloqueio)
# ============================================================


@pytest.mark.django_db(transaction=True)
def test_query_cliente_atual_id_do_titulo():
    tenant = TenantFactory(perfil_a=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        t = _criar_titulo(tenant, estado=EstadoTitulo.PAGO, dias_vencido=10, cliente_id=cli)
        achado = queries_desbloqueio.cliente_atual_id_do_titulo(
            tenant_id=tenant.id, titulo_id=t.titulo_id
        )
        inexistente = queries_desbloqueio.cliente_atual_id_do_titulo(
            tenant_id=tenant.id, titulo_id=uuid4()
        )
    assert achado == cli
    assert inexistente is None


@pytest.mark.django_db(transaction=True)
def test_query_tem_outra_vencida_em_aberto_estados():
    """VENCIDO e PARCIALMENTE_PAGO (vencido) contam; PAGO/CANCELADO e futuro não."""
    tenant = TenantFactory(perfil_a=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        # só PAGO + futuro → sem dívida vencida em aberto
        _criar_titulo(tenant, estado=EstadoTitulo.PAGO, dias_vencido=20, cliente_id=cli)
        _criar_titulo(tenant, estado=EstadoTitulo.EMITIDO, dias_vencido=-5, cliente_id=cli)
        assert not queries_desbloqueio.tem_outra_vencida_em_aberto(
            tenant_id=tenant.id, cliente_id=cli
        )
        # adiciona um PARCIALMENTE_PAGO vencido → conta como em aberto
        _criar_titulo(
            tenant, estado=EstadoTitulo.PARCIALMENTE_PAGO, dias_vencido=10, cliente_id=cli
        )
        assert queries_desbloqueio.tem_outra_vencida_em_aberto(
            tenant_id=tenant.id, cliente_id=cli
        )


# ============================================================
# Consumer de desbloqueio
# ============================================================


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_happy_quitou_unica_divida():
    """Quitação zera a dívida vencida → encerra bloqueio automático + publica evento."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        bloqueio = _criar_bloqueio(tenant, cliente)
        # única dívida do cliente já quitada (estado PAGO)
        t = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=cliente.id
        )

    _rodar_consumer(tenant.id, t.titulo_id)

    recarregado = _bloqueio_recarregado(tenant.id, bloqueio.id)
    assert recarregado.desbloqueado_em is not None
    assert recarregado.desbloqueado_motivo == "pagamento_quitou_inadimplencia"
    assert recarregado.desbloqueado_por_usuario_id is None

    eventos = _eventos_desbloqueado(tenant.id)
    assert len(eventos) == 1
    payload = eventos[0]["payload"]
    assert payload["cliente_id"] == str(cliente.id)
    assert payload["motivo"] == "pagamento_quitou_inadimplencia"
    assert payload["titulo_id_quitado"] == str(t.titulo_id)


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_mantem_se_outra_vencida_em_aberto():
    """AC-CR-006-2: paga 1 título mas há OUTRA vencida em aberto → NÃO desbloqueia."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        bloqueio = _criar_bloqueio(tenant, cliente)
        pago = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=cliente.id
        )
        # outra dívida ainda vencida em aberto
        _criar_titulo(
            tenant, estado=EstadoTitulo.VENCIDO, dias_vencido=40, cliente_id=cliente.id
        )

    _rodar_consumer(tenant.id, pago.titulo_id)

    recarregado = _bloqueio_recarregado(tenant.id, bloqueio.id)
    assert recarregado.desbloqueado_em is None  # mantém bloqueio
    assert _eventos_desbloqueado(tenant.id) == []


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_pagamento_parcial_mantem():
    """Pagamento parcial: o próprio título fica `parcialmente_pago` vencido → mantém."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        bloqueio = _criar_bloqueio(tenant, cliente)
        parcial = _criar_titulo(
            tenant,
            estado=EstadoTitulo.PARCIALMENTE_PAGO,
            dias_vencido=50,
            cliente_id=cliente.id,
        )

    _rodar_consumer(tenant.id, parcial.titulo_id)

    recarregado = _bloqueio_recarregado(tenant.id, bloqueio.id)
    assert recarregado.desbloqueado_em is None
    assert _eventos_desbloqueado(tenant.id) == []


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_nao_desfaz_bloqueio_manual():
    """Bloqueio MANUAL (quebra de confiança) NÃO é desfeito por pagamento (D-CR-11)."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        bloqueio = _criar_bloqueio(
            tenant, cliente, motivo=MOTIVO_MANUAL_QUEBRA_CONFIANCA
        )
        t = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=cliente.id
        )

    _rodar_consumer(tenant.id, t.titulo_id)

    recarregado = _bloqueio_recarregado(tenant.id, bloqueio.id)
    assert recarregado.desbloqueado_em is None  # bloqueio manual intacto
    assert _eventos_desbloqueado(tenant.id) == []


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_cliente_anonimizado_no_op():
    """Título com cliente_atual_id NULL (anonimizado LGPD) → no-op resiliente."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        t = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=None
        )
    # não levanta; nenhum evento
    _rodar_consumer(tenant.id, t.titulo_id)
    assert _eventos_desbloqueado(tenant.id) == []


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_sem_bloqueio_ativo_no_op():
    """Cliente nunca bloqueado paga → no-op (não publica desbloqueio)."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        t = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=cliente.id
        )
    _rodar_consumer(tenant.id, t.titulo_id)
    assert _eventos_desbloqueado(tenant.id) == []


@pytest.mark.django_db(transaction=True)
def test_desbloqueio_idempotente_replay():
    """Replay do MESMO event_id desbloqueia 1x só (publica 1 evento)."""
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant)
        bloqueio = _criar_bloqueio(tenant, cliente)
        t = _criar_titulo(
            tenant, estado=EstadoTitulo.PAGO, dias_vencido=60, cliente_id=cliente.id
        )

    evento_id = uuid4()
    _rodar_consumer(tenant.id, t.titulo_id, event_id=evento_id)
    _rodar_consumer(tenant.id, t.titulo_id, event_id=evento_id)  # replay

    recarregado = _bloqueio_recarregado(tenant.id, bloqueio.id)
    assert recarregado.desbloqueado_em is not None
    assert len(_eventos_desbloqueado(tenant.id)) == 1
