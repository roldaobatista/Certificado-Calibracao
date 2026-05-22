"""T-EQP-018+020+021+022 (US-EQP-002b) — testes do fluxo de aprovacao
gestor_qualidade.

Cobre:
1. Happy: solicitar + aprovar publica `equipamento.versao_aprovada`.
2. Happy: solicitar + rejeitar publica `equipamento.versao_rejeitada`.
3. INV-EQP-002 (CHECK no banco) — solicitante == decisor em INSERT.
4. INV-EQP-002 (service) — solicitante == decisor em aprovar.
5. INV-EQP-VERSAO-001 — parecer_gestor_texto anti-PII.
6. parecer_gestor_texto >=30 chars (AC-EQP-002b-4).
7. Motivo nao-aprovavel rejeita ao solicitar.
8. Trigger PG anti-mutation pos-terminal (UPDATE em aprovada falha).
9. expirar publica `equipamento.versao_expirada` sem decisor.
10. Aprovar/rejeitar 2x falha (AprovacaoJaDecidida).
11. RLS cross-tenant — aprovacao de outro tenant invisivel.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError, ProgrammingError
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    MotivoMudancaEquipamentoVersao,
    StatusAprovacaoVersao,
)
from src.infrastructure.equipamentos.services_aprovacao import (
    AprovacaoJaDecidida,
    DadosSolicitacaoAprovacao,
    MotivoNaoExigeAprovacao,
    SegregacaoFuncoesViolada,
    aprovar,
    expirar,
    rejeitar,
    solicitar_aprovacao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

JUSTIFICATIVA_100 = (
    "Substituicao planejada do componente principal apos auditoria interna "
    "do ciclo 2026; rastreabilidade preservada por procedimento PROC-001."
)
PARECER_OK_30 = "Aprovado conforme dossie tecnico anexo neste protocolo."


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"eqp-apv-{sfx}")
    solicitante = UsuarioFactory(email=f"sol-{sfx}@c.local")
    decisor = UsuarioFactory(email=f"dec-{sfx}@c.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Aprovacao",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="APV-001",
            numero_serie="NS-APV-1",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
    return {
        "tenant": tenant,
        "cliente": cliente,
        "equipamento": equipamento,
        "solicitante": solicitante,
        "decisor": decisor,
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
# Happy
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_solicitar_e_aprovar_publica_evento(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        assert apv.status == StatusAprovacaoVersao.PENDENTE
        resultado = aprovar(
            tenant_id=cenario["tenant"].id,
            aprovacao=apv,
            decisor_id=cenario["decisor"].id,
            parecer_gestor_texto=PARECER_OK_30,
        )
        eventos = list(
            Auditoria.objects.filter(action="equipamento.versao_aprovada")
        )
    assert resultado.aprovacao.status == StatusAprovacaoVersao.APROVADA
    assert len(eventos) == 1


@pytest.mark.django_db(transaction=True)
def test_solicitar_e_rejeitar_publica_evento(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        rejeitar(
            tenant_id=cenario["tenant"].id,
            aprovacao=apv,
            decisor_id=cenario["decisor"].id,
            parecer_gestor_texto="Rejeitado por divergencia documental no dossie tecnico.",
        )
        eventos = list(
            Auditoria.objects.filter(action="equipamento.versao_rejeitada")
        )
        apv.refresh_from_db()
    assert apv.status == StatusAprovacaoVersao.REJEITADA
    assert len(eventos) == 1


# ----------------------------------------------------------------------
# INV-EQP-002 — segregacao de funcoes
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_inv_eqp_002_solicitante_eq_decisor_em_aprovar_bloqueado(cenario):
    """Service-side defesa em profundidade (alem do CHECK)."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        with pytest.raises(SegregacaoFuncoesViolada):
            aprovar(
                tenant_id=cenario["tenant"].id,
                aprovacao=apv,
                decisor_id=cenario["solicitante"].id,  # mesmo!
                parecer_gestor_texto=PARECER_OK_30,
            )


# ----------------------------------------------------------------------
# Parecer anti-PII + min chars
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_parecer_gestor_anti_pii_cpf_bloqueado(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        with pytest.raises(ValidationError, match="PII direta"):
            aprovar(
                tenant_id=cenario["tenant"].id,
                aprovacao=apv,
                decisor_id=cenario["decisor"].id,
                parecer_gestor_texto=(
                    "Aprovado conforme analise CPF 123.456.789-01 do gestor."
                ),
            )


@pytest.mark.django_db(transaction=True)
def test_parecer_gestor_min_chars_30(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        with pytest.raises(ValidationError, match=">=30"):
            aprovar(
                tenant_id=cenario["tenant"].id,
                aprovacao=apv,
                decisor_id=cenario["decisor"].id,
                parecer_gestor_texto="curto",
            )


# ----------------------------------------------------------------------
# Motivo nao-aprovavel
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_motivo_que_nao_obriga_aprovacao_bloqueado(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(MotivoNaoExigeAprovacao):
            solicitar_aprovacao(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["equipamento"],
                solicitante_id=cenario["solicitante"].id,
                dados=DadosSolicitacaoAprovacao(
                    campo="modelo",
                    valor_anterior="A",
                    valor_novo="B",
                    motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL.value,
                    motivo_detalhe=JUSTIFICATIVA_100,
                ),
            )


# ----------------------------------------------------------------------
# Trigger PG anti-mutation pos-terminal
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_trigger_pg_anti_mutacao_pos_terminal(cenario):
    """AC-EQP-002b-1 — UPDATE em aprovacao com status=aprovada falha."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        aprovar(
            tenant_id=cenario["tenant"].id,
            aprovacao=apv,
            decisor_id=cenario["decisor"].id,
            parecer_gestor_texto=PARECER_OK_30,
        )
        with pytest.raises(ProgrammingError, match="estado terminal"):
            AprovacaoPendenteEquipamentoVersao.objects.filter(pk=apv.pk).update(
                parecer_gestor_texto="Mutacao tardia tentada apos terminal."
            )


# ----------------------------------------------------------------------
# Expirar (job-driven)
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_expirar_publica_evento_sem_decisor(cenario):
    """T-EQP-019 helper — expirar nao precisa decisor nem parecer."""
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        expirar(
            tenant_id=cenario["tenant"].id,
            aprovacao=apv,
        )
        eventos = list(
            Auditoria.objects.filter(action="equipamento.versao_expirada")
        )
        apv.refresh_from_db()
    assert apv.status == StatusAprovacaoVersao.EXPIRADA
    assert len(eventos) == 1
    assert apv.decisor_id is None


# ----------------------------------------------------------------------
# Decisao duplicada
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_aprovar_apos_rejeitar_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        apv = solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
        rejeitar(
            tenant_id=cenario["tenant"].id,
            aprovacao=apv,
            decisor_id=cenario["decisor"].id,
            parecer_gestor_texto="Rejeitado por divergencia documental no dossie.",
        )
        with pytest.raises(AprovacaoJaDecidida):
            aprovar(
                tenant_id=cenario["tenant"].id,
                aprovacao=apv,
                decisor_id=cenario["decisor"].id,
                parecer_gestor_texto=PARECER_OK_30,
            )


# ----------------------------------------------------------------------
# CHECK no banco (INSERT direto bloqueado quando solicitante=decisor)
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_check_solicitante_eq_decisor_em_insert_bloqueado(cenario):
    """CHECK `ck_aprovacao_solicitante_neq_decisor` bloqueia INSERT
    direto via ORM com decisor preenchido igual ao solicitante."""
    from django.utils import timezone

    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises((IntegrityError, ValidationError)):
            AprovacaoPendenteEquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                solicitante=cenario["solicitante"],
                decisor=cenario["solicitante"],  # mesmo!
                campo="modelo",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
                motivo_detalhe=JUSTIFICATIVA_100,
                sla_vencimento=timezone.now(),
                status=StatusAprovacaoVersao.APROVADA.value,
                parecer_gestor_texto=PARECER_OK_30,
                decidida_em=timezone.now(),
            )


# ----------------------------------------------------------------------
# RLS cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_cross_tenant_aprovacao_invisivel(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        solicitar_aprovacao(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            solicitante_id=cenario["solicitante"].id,
            dados=_dados_outros(),
        )
    tenant_b = TenantFactory(slug=f"apv-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant_b.id):
        visiveis = AprovacaoPendenteEquipamentoVersao.objects.count()
    assert visiveis == 0
