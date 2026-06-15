"""INV-ORC-APROVADO-ENVELOPE — teste de CONTRATO produtor↔consumidor (T-ORC-052).

O que mais nenhum teste prova: que o PRODUTOR real do envelope
(`montar_envelope_orcamento_aprovado`, no domínio de orçamentos) e o CONSUMIDOR
real (`handle_orcamento_aprovado._parse_input`, na OS) batem por CONTRATO. Os
testes de `test_osme_fatia2.py` montam o envelope À MÃO — não pegariam um produtor
que renomeasse/removesse uma chave. Aqui o envelope nasce da função de produção e
é entregue ao consumidor de produção, fechando o gap (ADR-0082, equipamento POR ITEM).

Cobre (R3 / INV-ORC-APROVADO-ENVELOPE):
  1. Envelope real (1 item técnico + 1 item comercial) → 1 OS com 1 AtividadeDaOS
     (equipamento certo) + 1 ItemComercialOS (tipo=OUTRO, descrição derivada do
     placeholder — documenta o GATE-ORC-ITEMCOMERCIAL-DESCRICAO / MÉDIO-2).
  2. Replay do MESMO envelope (mesmo event_id) → continua 1 OS (dedup via
     consumer_idempotencia / INV-BUS-001).
  3. UNHAPPY: OS avulsa publica `os.aberta` SEM `orcamento_id` → `handle_os_aberta`
     é no-op (não converte nada — TL-ORC ALTO-1).

Cuidados do projeto: PG-real (--reuse-db), TenantFactory + run_in_tenant_context;
nunca dropar test_afere nem usar --create-db.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    ItemOrcamento,
    Orcamento,
)
from src.domain.comercial.orcamentos.enums import (
    EstadoOrcamento,
    TipoAtividadeAlvo,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.transicoes import (
    montar_envelope_orcamento_aprovado,
)
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.operacao.os.value_objects import TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.orcamento import (
    handle_orcamento_aprovado,
)
from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS, ItemComercialOS

from tests.factories import TenantFactory

_DBS = ["default", "breaker_writer"]


# ---------------------------------------------------------------------------
# Setup DB-real: equipamento + cliente (a OS precisa de FK reais)
# ---------------------------------------------------------------------------


def _criar_equip_e_cliente(tenant) -> tuple[Equipamento, Cliente]:
    sfx = uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento=f"{uuid4().int % 99999999999999:014d}",
            nome=f"Cliente Envelope {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equip = Equipamento.objects.create(
            tenant=tenant,
            tag=f"ENV-{sfx}",
            numero_serie=f"NS-ENV-{sfx}",
            fabricante="Toledo",
            modelo="Prix",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
            status=EquipamentoStatus.ATIVO,
        )
    return equip, cliente


# ---------------------------------------------------------------------------
# Builders de domínio (produtor) — valores reais de tenant/cliente/equipamento
# ---------------------------------------------------------------------------


def _preco_resolvido(valor: str) -> PrecoResolvido:
    return PrecoResolvido(
        item_id=uuid4(),
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=uuid4(),
        preco=Preco(Decimal(valor)),
        data_referencia=datetime(2026, 1, 1, tzinfo=UTC),
        origem_preco=OrigemPreco.MANUAL,
    )


def _orcamento(*, tenant_id: UUID, cliente_id: UUID, liquido: int) -> Orcamento:
    return Orcamento(
        id=uuid4(),
        tenant_id=tenant_id,
        cliente_atual_id=cliente_id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="v1",
        numero=1,
        estado=EstadoOrcamento.APROVADO_PENDENTE_OS,
        validade=JanelaVigencia(inicio=datetime(2026, 1, 1, tzinfo=UTC)),
        total_bruto=Dinheiro(liquido),
        descontos=Dinheiro(0),
        impostos=Dinheiro(0),
        liquido=Dinheiro(liquido),
        comissao_prevista=Dinheiro(0),
        condicoes_pagamento=CondicoesPagamento.a_vista_pix(),
        criado_em=datetime(2026, 1, 1, tzinfo=UTC),
        criado_por=uuid4(),
    )


def _item_tecnico(*, tenant_id: UUID, equipamento_id: UUID) -> ItemOrcamento:
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=tenant_id,
        catalogo_item_id=uuid4(),
        sequencia=1,
        preco_resolvido=_preco_resolvido("150.00"),
        preco_final=Dinheiro(15000),
        desconto_pct=Decimal("0"),
        desconto_valor=Dinheiro(0),
        quantidade=Decimal("1"),
        total=Dinheiro(15000),
        semaforo="verde",
        descricao_snapshot="Calibracao balanca 30kg",
        equipamento_id=equipamento_id,
        tipo_atividade_alvo=TipoAtividadeAlvo.CALIBRACAO,
        grandeza_solicitada="massa",
        faixa_solicitada_min=Decimal("0"),
        faixa_solicitada_max=Decimal("30"),
        unidade_solicitada="kg",
    )


def _item_comercial(*, tenant_id: UUID) -> ItemOrcamento:
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=tenant_id,
        catalogo_item_id=uuid4(),
        sequencia=2,
        preco_resolvido=_preco_resolvido("80.00"),
        preco_final=Dinheiro(8000),
        desconto_pct=Decimal("0"),
        desconto_valor=Dinheiro(0),
        quantidade=Decimal("1"),
        total=Dinheiro(8000),
        semaforo="verde",
        descricao_snapshot="Taxa de deslocamento",
        equipamento_id=None,
        tipo_item_comercial=TipoItemComercial.TAXA_VISITA,
    )


def _analise(orcamento_id: UUID, tenant_id: UUID) -> AnaliseCriticaOrcamento:
    return AnaliseCriticaOrcamento(
        id=uuid4(),
        orcamento_id=orcamento_id,
        versao_id=uuid4(),
        tenant_id=tenant_id,
        perfil_no_evento="D",
        veredito=VeredictoAnaliseCritica.DESABILITADA,
        norma_referencia="ISO/IEC 17025:2017 cl. 7.1.1",
        itens_avaliados=(),
        snapshot_hash="b" * 64,
        avaliada_em=datetime(2026, 1, 2, tzinfo=UTC),
        avaliada_por=str(uuid4()),
    )


def _envelope_bus(payload: dict, *, tenant_id: UUID, event_id: UUID | None = None) -> dict:
    """Embrulha o payload do PRODUTOR no envelope de bus que o consumidor lê."""
    corr = uuid4()
    return {
        "event_id": str(event_id or uuid4()),
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": payload,
    }


# ---------------------------------------------------------------------------
# 1. Contrato: produtor real → consumidor real → OS coerente
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_aprovado_envelope_contrato_produtor_consumidor() -> None:
    """INV-ORC-APROVADO-ENVELOPE: o envelope do produtor abre a OS exata no consumidor.

    1 item técnico (equipamento) → 1 AtividadeDaOS com o equipamento certo;
    1 item comercial (sem equipamento) → 1 ItemComercialOS (tipo=OUTRO; descrição
    derivada do placeholder — GATE-ORC-ITEMCOMERCIAL-DESCRICAO / MÉDIO-2).
    """
    tenant = TenantFactory(slug=f"orc-env-{uuid4().hex[:6]}")
    equip, cliente = _criar_equip_e_cliente(tenant)

    orc = _orcamento(tenant_id=tenant.id, cliente_id=cliente.id, liquido=23000)
    itens = [
        _item_tecnico(tenant_id=tenant.id, equipamento_id=equip.id),
        _item_comercial(tenant_id=tenant.id),
    ]
    analise = _analise(orc.id, tenant.id)

    # PRODUTOR real: monta o payload orcamento.aprovado.
    payload = montar_envelope_orcamento_aprovado(
        orcamento=orc,
        itens=itens,
        analise_critica=analise,
        regra_decisao_acordada="default",
        abertura_at=datetime.now(UTC),
    )

    # O contrato em si: chaves de header + chaves por item presentes.
    assert payload["orcamento_id"] == str(orc.id)
    assert payload["cliente_id"] == str(cliente.id)
    assert payload["valor_total"] == "230.00"
    assert len(payload["itens"]) == 2
    item_tec = next(i for i in payload["itens"] if i["equipamento_id"] is not None)
    item_com = next(i for i in payload["itens"] if i["equipamento_id"] is None)
    assert item_tec["tipo"] == "calibracao"
    assert item_tec["equipamento_id"] == str(equip.id)
    assert item_com["descricao"] == "Taxa de deslocamento"  # campo aditivo Wave A

    # CONSUMIDOR real: abre a OS a partir do envelope do produtor.
    envelope = _envelope_bus(payload, tenant_id=tenant.id)
    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)

        oss = list(OS.objects.filter(tenant=tenant))
        assert len(oss) == 1, f"esperada 1 OS, achou {len(oss)}"
        os_obj = oss[0]
        # 1 item técnico (equip único) → OS single-equip: OS.equipamento_id = equip
        # (D-OSME-2; só fica NULL em OS multi-equipamento, com >1 equip distinto).
        assert os_obj.equipamento_id == equip.id

        atividades = list(AtividadeDaOS.objects.filter(os=os_obj))
        assert len(atividades) == 1, "item técnico vira exatamente 1 atividade"
        assert atividades[0].equipamento_id == equip.id

        comerciais = list(ItemComercialOS.objects.filter(os=os_obj))
        assert len(comerciais) == 1, "item comercial vira exatamente 1 ItemComercialOS"
        # GATE-ORC-ITEMCOMERCIAL-DESCRICAO (MÉDIO-2): a OS ignora `descricao` do
        # envelope hoje e deriva do placeholder de tipo ("vistoria" → "Vistoria").
        assert comerciais[0].tipo == "outro"
        assert comerciais[0].valor == Decimal("80.00")
        assert comerciais[0].descricao_publica == "Vistoria"


# ---------------------------------------------------------------------------
# 2. Replay do mesmo envelope → 1 OS (dedup INV-BUS-001)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_aprovado_envelope_replay_nao_duplica_os() -> None:
    """Replay do MESMO event_id → continua 1 OS (consumer_idempotencia / INV-BUS-001)."""
    tenant = TenantFactory(slug=f"orc-env-rp-{uuid4().hex[:6]}")
    equip, cliente = _criar_equip_e_cliente(tenant)

    orc = _orcamento(tenant_id=tenant.id, cliente_id=cliente.id, liquido=15000)
    itens = [_item_tecnico(tenant_id=tenant.id, equipamento_id=equip.id)]
    payload = montar_envelope_orcamento_aprovado(
        orcamento=orc,
        itens=itens,
        analise_critica=_analise(orc.id, tenant.id),
        regra_decisao_acordada="default",
        abertura_at=datetime.now(UTC),
    )
    envelope = _envelope_bus(payload, tenant_id=tenant.id, event_id=uuid4())

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)
        handle_orcamento_aprovado(envelope)  # replay do MESMO event_id
        assert OS.objects.filter(tenant=tenant).count() == 1
        os_obj = OS.objects.filter(tenant=tenant).first()
        assert AtividadeDaOS.objects.filter(os=os_obj).count() == 1


# ---------------------------------------------------------------------------
# 3. UNHAPPY: os.aberta sem orcamento_id → handle_os_aberta no-op (ALTO-1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_os_aberta_avulsa_sem_orcamento_id_noop() -> None:
    """OS avulsa publica os.aberta SEM orcamento_id → consumer de orçamentos é no-op."""
    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.consumers.os_aberta import handle_os_aberta

    tenant = TenantFactory(slug=f"orc-env-noop-{uuid4().hex[:6]}")
    corr = uuid4()
    envelope_sem_orc = {
        "event_id": str(uuid4()),
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "tenant_id": str(tenant.id),
        "acao": "os.aberta",
        "payload": {"numero_os": "OS-2026-000999", "atividades_planejadas": []},
    }
    with run_in_tenant_context(tenant.id):
        # Não deve levantar nem publicar orcamento.convertido.
        handle_os_aberta(envelope_sem_orc)
        assert not BusOutbox.objects.filter(acao="orcamento.convertido").exists()
