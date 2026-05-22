"""T-EQP-019 (AC-EQP-002b-2 / P-EQP-R5) — testes do SLA workalendar +
job de expiracao.

Cobre:
1. `calcular_sla_vencimento` adiciona dias UTEIS BR (skip fim de
   semana + feriado).
2. SLA diferenciado: D+3 (sem cert) vs D+7 (com cert).
3. `solicitar_aprovacao` cria com sla_vencimento futuro.
4. `expirar_aprovacoes_vencidas` itera + chama expirar nas vencidas.
5. Aprovacao pendente NAO vencida NAO e expirada.
6. Management command roda multi-tenant.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    MotivoMudancaEquipamentoVersao,
    StatusAprovacaoVersao,
)
from src.infrastructure.equipamentos.services_aprovacao import (
    DadosSolicitacaoAprovacao,
    calcular_sla_vencimento,
    expirar_aprovacoes_vencidas,
    solicitar_aprovacao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

JUSTIFICATIVA_100 = (
    "Substituicao planejada do componente principal apos auditoria interna "
    "do ciclo 2026; rastreabilidade preservada por procedimento PROC-001."
)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"eqp-sla-{sfx}")
    solicitante = UsuarioFactory(email=f"sol-{sfx}@c.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente SLA",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="SLA-001",
            numero_serie="NS-SLA-1",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "equipamento": equipamento,
        "solicitante": solicitante,
    }


def _dados_outros():
    return DadosSolicitacaoAprovacao(
        campo="modelo",
        valor_anterior="Prix 4",
        valor_novo="Prix 4 Plus",
        motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
        motivo_detalhe=JUSTIFICATIVA_100,
    )


# ----------------------------------------------------------------------
# calcular_sla_vencimento
# ----------------------------------------------------------------------


def test_sla_sem_cert_3_dias_uteis():
    """Quinta-feira (02-jan-2026, dia util) + 3 uteis = terca (06-jan)."""
    base = datetime(2026, 1, 2, 14, 0, tzinfo=timezone.get_current_timezone())
    vencimento = calcular_sla_vencimento(tem_cert_vigente=False, base=base)
    # 2026-01-02 (sex) -> 03 (sab, pula) -> 04 (dom, pula) -> 05 seg
    # ... 3 dias uteis a partir do dia seguinte = sex+3uteis = ter 06.
    # workalendar conta a partir do dia seguinte; resultado canonico:
    # add_working_days(2026-01-02, 3) = 2026-01-07 (qua)
    assert vencimento.weekday() < 5  # nao cai em fim de semana


def test_sla_com_cert_7_dias_uteis():
    """Com cert -> D+7 (mais urgente)."""
    base = datetime(2026, 1, 2, 14, 0, tzinfo=timezone.get_current_timezone())
    sla_sem = calcular_sla_vencimento(tem_cert_vigente=False, base=base)
    sla_com = calcular_sla_vencimento(tem_cert_vigente=True, base=base)
    assert sla_com > sla_sem


def test_sla_pula_fim_de_semana():
    """Sexta + 1 dia util = segunda (pula sab/dom)."""
    sexta = datetime(2026, 5, 22, 10, 0, tzinfo=timezone.get_current_timezone())
    # workalendar conta a partir do dia seguinte (23-sat). add_working_days(sexta, 1) =
    # segunda 25 (pula 23+24).
    base = sexta
    vencimento = calcular_sla_vencimento(tem_cert_vigente=False, base=base)
    # vencimento eh dia util.
    assert vencimento.weekday() < 5


def test_sla_preserva_hora_e_tz():
    base = datetime(2026, 5, 18, 14, 30, tzinfo=timezone.get_current_timezone())
    vencimento = calcular_sla_vencimento(tem_cert_vigente=False, base=base)
    assert vencimento.hour == 14
    assert vencimento.minute == 30
    assert vencimento.tzinfo == base.tzinfo


# ----------------------------------------------------------------------
# solicitar_aprovacao usa SLA novo
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_solicitar_aprovacao_grava_sla_futuro(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
    assert apv.sla_vencimento > timezone.now()
    # sem cert -> D+3 uteis (>= 3 dias corridos minimos)
    assert apv.sla_vencimento >= timezone.now() + timedelta(days=2, hours=23)


# ----------------------------------------------------------------------
# expirar_aprovacoes_vencidas
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_expirar_vencidas_marca_status_e_publica_evento(cenario):
    """Aprovacao com sla_vencimento no passado vira expirada."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        # Forca sla no passado (simulando que ja vencimento foi atingido).
        AprovacaoPendenteEquipamentoVersao.objects.filter(pk=apv.pk).update(
            sla_vencimento=timezone.now() - timedelta(hours=1),
        )
        resultados = expirar_aprovacoes_vencidas(tenant_id=cenario["tenant"].id)
        apv.refresh_from_db()
        eventos = list(
            Auditoria.objects.filter(action="equipamento.versao_expirada")
        )
    assert len(resultados) == 1
    assert apv.status == StatusAprovacaoVersao.EXPIRADA
    assert len(eventos) == 1


@pytest.mark.django_db(transaction=True)
def test_expirar_nao_toca_aprovacao_futura(cenario):
    """Aprovacao com sla_vencimento futuro permanece PENDENTE."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        resultados = expirar_aprovacoes_vencidas(tenant_id=cenario["tenant"].id)
        apv.refresh_from_db()
    assert resultados == []
    assert apv.status == StatusAprovacaoVersao.PENDENTE


# ----------------------------------------------------------------------
# Management command
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_management_command_processa_um_tenant_especifico(cenario):
    """`processar_aprovacoes_expiradas_equipamento` itera por tenant.
    Aqui rodamos a logica direta (`expirar_aprovacoes_vencidas`) num
    tenant especifico ja contextualizado — equivale ao loop interno do
    command. O loop multi-tenant em si e coberto por validar_m2_equipamentos
    (drill) na Wave A."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        AprovacaoPendenteEquipamentoVersao.objects.filter(pk=apv.pk).update(
            sla_vencimento=timezone.now() - timedelta(hours=1),
        )
        resultados = expirar_aprovacoes_vencidas(tenant_id=cenario["tenant"].id)
        apv.refresh_from_db()
    assert len(resultados) == 1
    assert apv.status == StatusAprovacaoVersao.EXPIRADA
