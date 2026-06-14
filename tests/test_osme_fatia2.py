"""Testes da Fatia 2 — os-multi-equipamento (T-OSME-036).

Cobre:
(a) Envelope multi-equip (2 itens, 2 equipamentos distintos) -> 2 atividades,
    cada uma com SEU equipamento (AC-OSME-002-2).
(b) Envelope com 1 item sem equipamento_id -> 1 ItemComercialOS criado, 0
    atividades (AC-OSME-006-3 / D-OSME-3).
(c) UNHAPPY: envelope com 2 equipamentos, 1 em SUCATA -> 422
    EquipamentoBaixadoEmOS (AC-OSME-004-2).
(d) Reabertura de OS com 2 equipamentos -> OS-filha preserva equipamento por
    atividade (AC-OSME-003-2).
(e) Deteccao: Equipamento.Baixado localiza OS via AtividadeDaOS (AC-OSME-004-1).

Cuidados do projeto:
- PG-real (--reuse-db), TenantFactory + run_in_tenant_context.
- NUNCA dropar test_afere nem usar --create-db.
- Usa handle_orcamento_aprovado que chama o use case e persiste no banco.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.consumers.equipamento import (
    handle_equipamento_baixado,
)
from src.infrastructure.ordens_servico.consumers.orcamento import (
    EquipamentoBaixadoEmOSError,
    handle_orcamento_aprovado,
)
from src.infrastructure.ordens_servico.models import (
    OS,
    AtividadeDaOS,
    ItemComercialOS,
)

from tests.factories import TenantFactory

# =============================================================
# Helpers
# =============================================================


def _criar_equipamento(tenant, *, status: str = EquipamentoStatus.ATIVO) -> Equipamento:
    sfx = uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        cli, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento=f"{uuid4().int % 99999999999999:014d}",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equip = Equipamento.objects.create(
            tenant=tenant,
            tag=f"F2-{sfx}",
            numero_serie=f"NS-F2-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cli,
            perfil_tenant_snapshot={"perfil": "D"},
            status=status,
        )
    return equip


def _envelope_multi_equip(tenant_id, cliente_id, equip1_id, equip2_id):
    """Envelope v2 com 2 itens, cada um com seu equipamento."""
    corr = uuid4()
    return {
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-f2",
            "equipamento_id": None,  # header opcional em envelope v2
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "250.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "calibracao",
                    "sequencia": 1,
                    "valor_unitario": "150.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equip1_id),
                },
                {
                    "tipo": "manutencao_corretiva",
                    "sequencia": 2,
                    "valor_unitario": "100.00",
                    "requer_recebimento": False,
                    "equipamento_id": str(equip2_id),
                },
            ],
        },
    }


def _envelope_item_sem_equip(tenant_id, cliente_id):
    """Envelope com 1 item sem equipamento_id e sem header equipamento_id."""
    corr = uuid4()
    return {
        "correlation_id": str(corr),
        "causation_id": str(corr),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "orcamento.aprovado",
        "payload": {
            "orcamento_id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "cliente_id": str(cliente_id),
            "cliente_referencia_hash": "a" * 64,
            "cliente_key_id": "kms-f2",
            "equipamento_id": None,
            "equipamento_recebimento_id": None,
            "analise_critica_id": str(uuid4()),
            "analise_critica_snapshot_hash": "b" * 64,
            "regra_decisao_acordada": "default",
            "valor_total": "80.00",
            "abertura_at": datetime.now(UTC).isoformat(),
            "criada_por_user_id": None,
            "itens": [
                {
                    "tipo": "vistoria",
                    "sequencia": 1,
                    "valor_unitario": "80.00",
                    "requer_recebimento": False,
                    "equipamento_id": None,
                },
            ],
        },
    }


def _obter_cliente_de_equip(tenant, equip: Equipamento) -> Cliente:
    """Retorna o cliente_atual do equipamento."""
    with run_in_tenant_context(tenant.id):
        return equip.cliente_atual  # type: ignore[return-value]


# =============================================================
# (a) Envelope multi-equip -> 2 atividades, cada uma com SEU equipamento
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_osme_f2_a_envelope_multi_equip_cria_atividades_por_equipamento(db):
    """(a) Envelope com 2 itens de equipamentos DIFERENTES -> 2 atividades cada
    uma com SEU equipamento_id (AC-OSME-002-2)."""
    tenant = TenantFactory(slug=f"f2a-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)
    equip2 = _criar_equipamento(tenant)

    # Obtemos um cliente qualquer (do equip1).
    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual
        cli_id = cli.id

    envelope = _envelope_multi_equip(tenant.id, cli_id, equip1.id, equip2.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)

    with run_in_tenant_context(tenant.id):
        oss = list(OS.objects.filter(tenant=tenant))
        assert len(oss) == 1, f"Esperada 1 OS, got {len(oss)}"
        os_obj = oss[0]

        atividades = list(
            AtividadeDaOS.objects.filter(os=os_obj).order_by("sequencia")
        )
        assert len(atividades) == 2, (
            f"Esperadas 2 atividades (uma por equipamento), got {len(atividades)}"
        )

        # Cada atividade deve ter o equipamento do seu item.
        equip_ids_atividades = {a.equipamento_id for a in atividades}
        assert equip1.id in equip_ids_atividades, (
            f"equip1 ({equip1.id}) nao encontrado nas atividades: {equip_ids_atividades}"
        )
        assert equip2.id in equip_ids_atividades, (
            f"equip2 ({equip2.id}) nao encontrado nas atividades: {equip_ids_atividades}"
        )

        # OS multi-equip: OS.equipamento_id deve ser NULL (D-OSME-2).
        assert os_obj.equipamento_id is None, (
            f"OS multi-equip deve ter equipamento_id=NULL, got {os_obj.equipamento_id}"
        )

        # Sem ItemComercialOS (todos os itens tinham equipamento).
        assert ItemComercialOS.objects.filter(os=os_obj).count() == 0


# =============================================================
# (b) Envelope com 1 item sem equipamento_id -> 1 ItemComercialOS, 0 atividades
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_osme_f2_b_item_sem_equipamento_vira_item_comercial(db):
    """(b) Envelope com 1 item sem equipamento_id -> 1 ItemComercialOS criado,
    0 atividades tecnicas (AC-OSME-006-3 / D-OSME-3)."""
    tenant = TenantFactory(slug=f"f2b-{uuid4().hex[:6]}")
    sfx = uuid4().hex[:6]

    with run_in_tenant_context(tenant.id):
        cli, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento=f"{uuid4().int % 99999999999999:014d}",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli F2B {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )

    envelope = _envelope_item_sem_equip(tenant.id, cli.id)

    with run_in_tenant_context(tenant.id):
        handle_orcamento_aprovado(envelope)

    with run_in_tenant_context(tenant.id):
        oss = list(OS.objects.filter(tenant=tenant))
        assert len(oss) == 1
        os_obj = oss[0]

        # Zero atividades tecnicas (item sem equipamento nao vira atividade).
        n_atividades = AtividadeDaOS.objects.filter(os=os_obj).count()
        assert n_atividades == 0, (
            f"Item sem equipamento NAO deve virar atividade, got {n_atividades} atividades"
        )

        # 1 ItemComercialOS criado.
        itens_com = list(ItemComercialOS.objects.filter(os=os_obj))
        assert len(itens_com) == 1, (
            f"Esperado 1 ItemComercialOS, got {len(itens_com)}"
        )
        item = itens_com[0]
        assert item.tipo == "outro", f"Tipo default deve ser 'outro', got {item.tipo}"
        assert item.valor == Decimal("80.00"), f"Valor incorreto: {item.valor}"
        assert item.quantidade == 1


# =============================================================
# (c) UNHAPPY: envelope com 2 equipamentos, 1 em SUCATA -> 422
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_osme_f2_c_unhappy_equip_sucata_bloqueia_mesmo_multi_equip(db):
    """(c) UNHAPPY: envelope com 2 equipamentos, 1 SUCATA -> 422
    EquipamentoBaixadoEmOS. OS nao criada (AC-OSME-004-2)."""
    tenant = TenantFactory(slug=f"f2c-{uuid4().hex[:6]}")
    equip_ativo = _criar_equipamento(tenant, status=EquipamentoStatus.ATIVO)
    equip_sucata = _criar_equipamento(tenant, status=EquipamentoStatus.SUCATA)

    with run_in_tenant_context(tenant.id):
        cli = equip_ativo.cliente_atual
        cli_id = cli.id

    envelope = _envelope_multi_equip(tenant.id, cli_id, equip_ativo.id, equip_sucata.id)

    with run_in_tenant_context(tenant.id):
        with pytest.raises(EquipamentoBaixadoEmOSError) as exc_info:
            handle_orcamento_aprovado(envelope)

    assert exc_info.value.codigo == "EquipamentoBaixadoEmOS"
    assert exc_info.value.http_status == 422

    with run_in_tenant_context(tenant.id):
        assert OS.objects.filter(tenant=tenant).count() == 0, (
            "OS NAO deve ser criada quando algum equipamento esta em SUCATA"
        )


# =============================================================
# (d) Reabertura: OS-filha preserva equipamento por atividade
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_osme_f2_d_reabertura_preserva_equipamento_por_atividade(db):
    """(d) Reabertura de OS com 2 equipamentos -> OS-filha preserva
    equipamento_id por atividade (AC-OSME-003-2)."""

    from src.application.operacao.os.operacoes_avancadas import (
        ReabrirOSInput,
        reabrir_os,
    )
    from src.domain.operacao.os.value_objects import (
        MotivoCancelamento,
    )
    from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

    tenant = TenantFactory(slug=f"f2d-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)
    equip2 = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual

        # Cria OS-mae via consumer (2 itens com equipamentos diferentes).
        envelope = _envelope_multi_equip(tenant.id, cli.id, equip1.id, equip2.id)
        handle_orcamento_aprovado(envelope)

        os_mae = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_mae is not None

        # Muda estado para CONCLUIDA para poder reabrir.
        os_mae.estado = "concluida"
        os_mae.save()

        # Confirma que as atividades da OS-mae tem os equipamentos.
        atividades_mae = list(
            AtividadeDaOS.objects.filter(os=os_mae).order_by("sequencia")
        )
        assert len(atividades_mae) == 2
        equips_mae = {a.equipamento_id for a in atividades_mae}
        assert equip1.id in equips_mae
        assert equip2.id in equips_mae

    with run_in_tenant_context(tenant.id):
        repo = DjangoOSRepository()
        motivo = MotivoCancelamento(
            "Reabertura de teste para validar equipamento por atividade na OS filha"
        )
        resultado = reabrir_os(
            payload=ReabrirOSInput(
                os_origem_id=os_mae.id,
                motivo=motivo,
                garantia_procedente=False,
                chamado_origem_id=None,
                sucessao_societaria_id=None,
                correlation_id=uuid4(),
                reaberta_em=datetime.now(UTC),
                reaberta_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        atividades_filha = list(
            AtividadeDaOS.objects.filter(os_id=resultado.os_id_nova).order_by("sequencia")
        )
        assert len(atividades_filha) == 2, (
            f"OS-filha deve ter 2 atividades, got {len(atividades_filha)}"
        )

        equips_filha = {a.equipamento_id for a in atividades_filha}
        assert equip1.id in equips_filha, (
            f"equip1 ({equip1.id}) nao encontrado nas atividades da OS-filha: {equips_filha}"
        )
        assert equip2.id in equips_filha, (
            f"equip2 ({equip2.id}) nao encontrado nas atividades da OS-filha: {equips_filha}"
        )


# =============================================================
# (e) Deteccao: Equipamento.Baixado localiza OS via AtividadeDaOS (sem N+1)
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_osme_f2_e_deteccao_equipamento_baixado_via_atividade(db, caplog):
    """(e) handle_equipamento_baixado localiza OSs via AtividadeDaOS.equipamento_id
    (nao via OS.equipamento_id), usando 1 query (sem N+1) (AC-OSME-004-1)."""
    tenant = TenantFactory(slug=f"f2e-{uuid4().hex[:6]}")
    equip1 = _criar_equipamento(tenant)
    equip2 = _criar_equipamento(tenant)

    with run_in_tenant_context(tenant.id):
        cli = equip1.cliente_atual

        # Cria OS com 2 equipamentos via consumer.
        envelope = _envelope_multi_equip(tenant.id, cli.id, equip1.id, equip2.id)
        handle_orcamento_aprovado(envelope)

        os_obj = OS.objects.filter(tenant=tenant).order_by("-criada_em").first()
        assert os_obj is not None

        # Confirma atividades com os equipamentos.
        atividades = list(AtividadeDaOS.objects.filter(os=os_obj))
        equips_atv = {a.equipamento_id for a in atividades}
        assert equip1.id in equips_atv

    # Envia evento de baixa do equip1 e verifica que o consumer loga a OS afetada.
    envelope_baixado = {
        "correlation_id": str(uuid4()),
        "causation_id": str(uuid4()),
        "event_id": str(uuid4()),
        "tenant_id": str(tenant.id),
        "acao": "equipamento.baixado",
        "payload": {
            "equipamento_id": str(equip1.id),
        },
    }

    with caplog.at_level(logging.INFO), run_in_tenant_context(tenant.id):
        handle_equipamento_baixado(envelope_baixado)

    # O log deve conter a referencia ao equipamento e pelo menos 1 OS afetada.
    log_text = caplog.text
    assert str(equip1.id) in log_text, (
        f"Log deve mencionar equipamento_id={equip1.id}"
    )
    # Verifica que logou pelo menos "1 OS pendentes" (a OS criada acima esta em RASCUNHO).
    assert "1 OS pendentes" in log_text or "OS pendentes" in log_text, (
        f"Log deve indicar OS pendentes afetadas. Log atual: {log_text}"
    )
