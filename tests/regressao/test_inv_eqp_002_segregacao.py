"""Anti-regressao INV-EQP-002 (T-EQP-091 — AC-EQP-002b-3 / ISO 17025 cl. 6.2).

Segregacao de funcoes: solicitante de aprovacao NAO PODE ser o mesmo
que o decisor. Defesa em 3 camadas:
1. CHECK constraint Django (ck_aprovacao_solicitante_neq_decisor).
2. clean() do modelo.
3. assert no service `_decidir`.

>=3 testes: happy (decisor != solicitante) + unhappy decisor==solicitante
(service raise) + cross-tenant (RLS isola visibilidade).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    MotivoMudancaEquipamentoVersao,
)
from src.infrastructure.equipamentos.services_aprovacao import (
    DadosSolicitacaoAprovacao,
    SegregacaoFuncoesViolada,
    aprovar,
    solicitar_aprovacao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


def _cenario_basico(slug_prefix: str):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"{slug_prefix}-{sfx}")
    operador = UsuarioFactory(email=f"op-{slug_prefix}-{sfx}@x.local")
    gestor = UsuarioFactory(email=f"gestor-{slug_prefix}-{sfx}@x.local")
    with run_in_tenant_context(tenant.id, operador.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome=f"Cli {slug_prefix} {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV002-{slug_prefix}-{sfx}",
            numero_serie=f"NSINV002-{slug_prefix}-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return tenant, operador, gestor, eq


def _dados_solicitacao():
    return DadosSolicitacaoAprovacao(
        campo="fabricante",
        valor_anterior="Toledo",
        valor_novo="Filizola",
        motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
        motivo_detalhe=(
            "Substituicao de fabricante por compatibilidade tecnica. "
            "Cliente solicitou. RT validou. Documentado em ata."
        ),
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_decisor_distinto_aprova(db):
    tenant, operador, gestor, eq = _cenario_basico("inv002-h")
    with run_in_tenant_context(tenant.id, operador.id):
        aprov = solicitar_aprovacao(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitante_id=operador.id,
            dados=_dados_solicitacao(),
        )
    with run_in_tenant_context(tenant.id, gestor.id):
        resultado = aprovar(
            tenant_id=tenant.id,
            aprovacao=aprov,
            decisor_id=gestor.id,
            parecer_gestor_texto=(
                "Mudanca validada pelo RT. Documentacao completa. Aprovo."
            ),
        )
    assert resultado.aprovacao.decisor_id == gestor.id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_solicitante_eq_decisor_bloqueado(db):
    tenant, operador, _gestor, eq = _cenario_basico("inv002-u")
    with run_in_tenant_context(tenant.id, operador.id):
        aprov = solicitar_aprovacao(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitante_id=operador.id,
            dados=_dados_solicitacao(),
        )
    with run_in_tenant_context(tenant.id, operador.id):
        with pytest.raises(SegregacaoFuncoesViolada, match=r"INV-EQP-002"):
            aprovar(
                tenant_id=tenant.id,
                aprovacao=aprov,
                decisor_id=operador.id,  # mesmo que solicitante
                parecer_gestor_texto=(
                    "Auto-aprovacao tentativa — deve falhar por segregacao."
                ),
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cross_tenant_aprovacao_invisivel(db):
    """Tenant B nao enxerga aprovacao em A — RLS isola."""
    tenant_a, operador_a, _gestor_a, eq_a = _cenario_basico("inv002-ca")
    with run_in_tenant_context(tenant_a.id, operador_a.id):
        aprov = solicitar_aprovacao(
            tenant_id=tenant_a.id,
            equipamento=eq_a,
            solicitante_id=operador_a.id,
            dados=_dados_solicitacao(),
        )

    tenant_b = TenantFactory(slug=f"inv002-cb-{uuid4().hex[:6]}")
    operador_b = UsuarioFactory(email=f"op-b-{uuid4().hex[:6]}@x.local")
    from src.infrastructure.equipamentos.models import (
        AprovacaoPendenteEquipamentoVersao,
    )

    with run_in_tenant_context(tenant_b.id, operador_b.id):
        # Sem visibilidade da aprovacao de A.
        assert not AprovacaoPendenteEquipamentoVersao.objects.filter(
            id=aprov.id
        ).exists()
