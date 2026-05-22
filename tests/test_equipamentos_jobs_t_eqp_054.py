"""T-EQP-054 (US-EQP-006 AC-EQP-006-7 + US-EQP-002b AC-EQP-002b-2 /
P-EQP-T9 + P-EQP-R5) — jobs Marco 2:

1. `marcar_equipamentos_orfaos_pendentes` — sweep multi-tenant
   detectando cliente_atual_id NULL em status nao-terminal.
2. `alertar_aprovacoes_d1` — sweep multi-tenant publicando
   `equipamento.versao_aprovacao_alerta_d1` para aprovacoes vencendo.
3. Helper `processar_em_contexto_tenant` itera tenants + roda
   funcao em `run_in_tenant_context`.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    EquipamentoStatus,
    MotivoMudancaEquipamentoVersao,
    StatusAprovacaoVersao,
)
from src.infrastructure.equipamentos.services_aprovacao import (
    DadosSolicitacaoAprovacao,
    alertar_aprovacoes_d1,
    solicitar_aprovacao,
)
from src.infrastructure.equipamentos.services_orfaos import (
    marcar_equipamentos_orfaos_pendentes,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.multitenant.jobs import (
    processar_em_contexto_tenant,
)

from tests.factories import TenantFactory, UsuarioFactory

# ====================================================================
# Helper processar_em_contexto_tenant
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_processar_em_contexto_tenant_executa_por_tenant():
    t1 = TenantFactory(slug=f"job-a-{uuid4().hex[:6]}")
    t2 = TenantFactory(slug=f"job-b-{uuid4().hex[:6]}")
    chamadas = []

    def coletor(tenant):
        chamadas.append(tenant.id)
        return tenant.slug

    resultado = processar_em_contexto_tenant(coletor, tenants=[t1, t2])
    assert set(resultado.keys()) == {t1.id, t2.id}
    assert resultado[t1.id] == t1.slug
    assert resultado[t2.id] == t2.slug
    assert set(chamadas) == {t1.id, t2.id}


# ====================================================================
# T-EQP-054 — marcar equipamentos orfaos
# ====================================================================


@pytest.fixture
def cenario_orfaos(db):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"orfao-{sfx}")
    operador = UsuarioFactory(email=f"op-orfao-{sfx}@e.local")
    with run_in_tenant_context(tenant.id):
        # eq_ativo nasce ja orfao (cliente_atual=None) com status=ativo
        # simulando inconsistencia que o sweep deve corrigir. Trigger
        # BEFORE UPDATE nao fire em INSERT, entao o estado persiste.
        eq_ativo = Equipamento.objects.create(
            tenant=tenant,
            tag=f"EQA-{sfx}",
            numero_serie=f"NSORA-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=None,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        eq_ja_sucata = Equipamento.objects.create(
            tenant=tenant,
            tag=f"EQS-{sfx}",
            numero_serie=f"NSORS-{sfx}",
            fabricante="Toledo",
            modelo="Y",
            cliente_atual=None,
            perfil_tenant_snapshot={"perfil": "D"},
            status=EquipamentoStatus.SUCATA.value,
        )
    return {
        "tenant": tenant,
        "operador": operador,
        "eq_ativo": eq_ativo,
        "eq_ja_sucata": eq_ja_sucata,
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_marcar_equipamentos_orfaos_pendentes(cenario_orfaos):
    with run_in_tenant_context(cenario_orfaos["tenant"].id):
        marcados = marcar_equipamentos_orfaos_pendentes(
            tenant_id=cenario_orfaos["tenant"].id
        )
    assert len(marcados) == 1
    assert marcados[0].equipamento_id == cenario_orfaos["eq_ativo"].id
    assert marcados[0].status_anterior == EquipamentoStatus.ATIVO.value

    with run_in_tenant_context(cenario_orfaos["tenant"].id):
        eq = Equipamento.objects.get(id=cenario_orfaos["eq_ativo"].id)
    assert eq.status == EquipamentoStatus.ORFAO_PENDENTE_DECISAO.value

    # Sucata nao deve mudar.
    with run_in_tenant_context(cenario_orfaos["tenant"].id):
        eq_sucata = Equipamento.objects.get(id=cenario_orfaos["eq_ja_sucata"].id)
    assert eq_sucata.status == EquipamentoStatus.SUCATA.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_marcar_orfao_publica_evento(cenario_orfaos):
    with run_in_tenant_context(cenario_orfaos["tenant"].id):
        marcar_equipamentos_orfaos_pendentes(
            tenant_id=cenario_orfaos["tenant"].id
        )
        evento = (
            Auditoria.objects.filter(
                action="equipamento.orfao_marcado_pelo_job",
            )
            .filter(
                payload_jsonb__equipamento_id=str(cenario_orfaos["eq_ativo"].id)
            )
            .first()
        )
    assert evento is not None
    assert evento.payload_jsonb["status_anterior"] == EquipamentoStatus.ATIVO.value
    assert (
        evento.payload_jsonb["motivo"]
        == "cliente_atual_id_nulo_sem_status_terminal"
    )
    # Payload sanitizado — sem tag/cliente.
    assert "tag" not in evento.payload_jsonb
    assert "cliente_atual_id" not in evento.payload_jsonb


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_marcar_orfao_segunda_passada_e_no_op(cenario_orfaos):
    with run_in_tenant_context(cenario_orfaos["tenant"].id):
        marcar_equipamentos_orfaos_pendentes(
            tenant_id=cenario_orfaos["tenant"].id
        )
        marcados_2 = marcar_equipamentos_orfaos_pendentes(
            tenant_id=cenario_orfaos["tenant"].id
        )
    assert marcados_2 == []


# ====================================================================
# T-EQP-054 — alertar aprovacoes D-1
# ====================================================================


@pytest.fixture
def cenario_aprovacao_d1(db):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"d1-{sfx}")
    solicitante = UsuarioFactory(email=f"sol-d1-{sfx}@e.local")
    with run_in_tenant_context(tenant.id, solicitante.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente D1",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"D1EQ-{sfx}",
            numero_serie=f"NSD1-{sfx}",
            fabricante="Toledo",
            modelo="Z",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        aprov_perto_vencer = solicitar_aprovacao(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitante_id=solicitante.id,
            dados=DadosSolicitacaoAprovacao(
                campo="numero_serie",
                valor_anterior="NSANTIGO",
                valor_novo="NSNOVO",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
                motivo_detalhe=(
                    "Substituicao do numero de serie por mudanca de PCB "
                    "principal pos-falha de hardware com rastreabilidade. "
                    "RT supervisionou."
                ),
            ),
        )
        # Forca sla_vencimento para D+0.5 (12h).
        AprovacaoPendenteEquipamentoVersao.objects.filter(
            id=aprov_perto_vencer.id
        ).update(sla_vencimento=timezone.now() + timedelta(hours=12))

        aprov_distante = solicitar_aprovacao(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitante_id=solicitante.id,
            dados=DadosSolicitacaoAprovacao(
                campo="fabricante",
                valor_anterior="Toledo",
                valor_novo="Filizola",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
                motivo_detalhe=(
                    "Substituicao do fabricante mantendo modelo equivalente. "
                    "Cliente solicitou troca por compatibilidade de pecas. "
                    "RT supervisionou."
                ),
            ),
        )
        AprovacaoPendenteEquipamentoVersao.objects.filter(
            id=aprov_distante.id
        ).update(sla_vencimento=timezone.now() + timedelta(days=5))
    return {
        "tenant": tenant,
        "solicitante": solicitante,
        "aprov_perto_vencer": aprov_perto_vencer,
        "aprov_distante": aprov_distante,
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_alertar_aprovacoes_d1_so_alerta_dentro_janela(cenario_aprovacao_d1):
    with run_in_tenant_context(cenario_aprovacao_d1["tenant"].id):
        alertadas = alertar_aprovacoes_d1(
            tenant_id=cenario_aprovacao_d1["tenant"].id,
            horas_maximas_para_alerta=24,
        )
    assert alertadas == [cenario_aprovacao_d1["aprov_perto_vencer"].id]


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_alertar_aprovacoes_d1_publica_evento_payload_sanitizado(
    cenario_aprovacao_d1,
):
    with run_in_tenant_context(cenario_aprovacao_d1["tenant"].id):
        alertar_aprovacoes_d1(
            tenant_id=cenario_aprovacao_d1["tenant"].id,
            horas_maximas_para_alerta=24,
        )
        evento = (
            Auditoria.objects.filter(
                action="equipamento.versao_aprovacao_alerta_d1",
            )
            .filter(
                payload_jsonb__aprovacao_id=str(
                    cenario_aprovacao_d1["aprov_perto_vencer"].id
                )
            )
            .first()
        )
    assert evento is not None
    payload = evento.payload_jsonb
    assert payload["aprovacao_id"] == str(
        cenario_aprovacao_d1["aprov_perto_vencer"].id
    )
    assert payload["horas_restantes"] >= 0
    assert payload["horas_restantes"] <= 24
    # Sem PII.
    assert "parecer_gestor_texto" not in payload
    assert "motivo_detalhe" not in payload
    assert "valor_anterior_hash" not in payload


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_alertar_aprovacoes_d1_aprovacao_decidida_nao_alerta(
    cenario_aprovacao_d1,
):
    with run_in_tenant_context(cenario_aprovacao_d1["tenant"].id):
        AprovacaoPendenteEquipamentoVersao.objects.filter(
            id=cenario_aprovacao_d1["aprov_perto_vencer"].id
        ).update(status=StatusAprovacaoVersao.APROVADA.value)
        alertadas = alertar_aprovacoes_d1(
            tenant_id=cenario_aprovacao_d1["tenant"].id,
            horas_maximas_para_alerta=24,
        )
    assert alertadas == []
