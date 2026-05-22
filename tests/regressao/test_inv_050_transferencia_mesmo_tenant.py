"""Anti-regressao INV-050 (T-EQP-096 — AC-EQP-004-2 / US-EQP-004).

Transferencia de equipamento PROIBE cessionario em tenant diferente
do cedente. Service `solicitar_transferencia` levanta
`CessionarioCrossTenant("cliente nao encontrado neste tenant")` →
422 (sem oracle cross-tenant: mesma mensagem do "id inexistente").

≥3 testes (padrao TST-004): happy + unhappy cross-tenant + unhappy
cessionario inexistente (mesma mensagem que cross-tenant).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    MotivoCategoriaTransferencia,
    ViaAceiteTransferencia,
)
from src.infrastructure.equipamentos.services_transferencia import (
    Aceite,
    CessionarioCrossTenant,
    DadosSolicitacaoTransferencia,
    solicitar_transferencia,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


def _criar_tenant_com_cliente_e_eq(slug_prefix: str, doc: str):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"{slug_prefix}-{sfx}")
    operador = UsuarioFactory(email=f"op-{slug_prefix}-{sfx}@x.local")
    with run_in_tenant_context(tenant.id, operador.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento=doc,
            nome=f"Cli {slug_prefix} {sfx}",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV050-{slug_prefix}-{sfx}",
            numero_serie=f"NSI050-{slug_prefix}-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return tenant, operador, cliente, eq


def _aceite_basico(usuario_id):
    return Aceite(
        tipo=ViaAceiteTransferencia.PRESENCIAL_ATENDENTE.value,
        usuario_id_atendente=usuario_id,
        consentimento_historico_expresso=True,
        nivel_consentimento_historico="completo",
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_happy_mesmo_tenant_efetiva(db):
    tenant, operador, _cedente, eq = _criar_tenant_com_cliente_e_eq(
        "inv050-h", "11222333000181"
    )
    with run_in_tenant_context(tenant.id, operador.id):
        cessionario = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="22333444000281",
            nome="Cessionario H",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        resultado = solicitar_transferencia(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitado_por_id=operador.id,
            dados=DadosSolicitacaoTransferencia(
                cessionario_cliente_id=cessionario.id,
                motivo_categoria=MotivoCategoriaTransferencia.VENDA.value,
                motivo_detalhe=(
                    "Cessao por venda do equipamento usado entre clientes."
                ),
                aceite_cedente=_aceite_basico(operador.id),
                aceite_cessionario=_aceite_basico(operador.id),
            ),
        )
    assert resultado.transferencia.cessionario_cliente_id == cessionario.id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_cessionario_em_outro_tenant(db):
    tenant_a, operador_a, _cedente_a, eq_a = _criar_tenant_com_cliente_e_eq(
        "inv050-a", "11222333000181"
    )
    _tenant_b, _, cessionario_b, _ = _criar_tenant_com_cliente_e_eq(
        "inv050-b", "33444555000381"
    )
    with run_in_tenant_context(tenant_a.id, operador_a.id):
        with pytest.raises(CessionarioCrossTenant):
            solicitar_transferencia(
                tenant_id=tenant_a.id,
                equipamento=eq_a,
                solicitado_por_id=operador_a.id,
                dados=DadosSolicitacaoTransferencia(
                    cessionario_cliente_id=cessionario_b.id,
                    motivo_categoria=(
                        MotivoCategoriaTransferencia.VENDA.value
                    ),
                    motivo_detalhe=(
                        "Tentativa cross-tenant — deve falhar com mensagem "
                        "anti-oracle (sem distinguir de cliente inexistente)."
                    ),
                    aceite_cedente=_aceite_basico(operador_a.id),
                    aceite_cessionario=_aceite_basico(operador_a.id),
                ),
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unhappy_cessionario_inexistente_mesma_mensagem(db):
    """Garantia anti-oracle: cliente inexistente devolve EXATAMENTE
    a mesma excecao que cliente em outro tenant — sem distinguir."""
    tenant, operador, _cedente, eq = _criar_tenant_com_cliente_e_eq(
        "inv050-i", "44555666000481"
    )
    cessionario_fake_id = uuid4()
    with run_in_tenant_context(tenant.id, operador.id):
        with pytest.raises(CessionarioCrossTenant) as exc_info:
            solicitar_transferencia(
                tenant_id=tenant.id,
                equipamento=eq,
                solicitado_por_id=operador.id,
                dados=DadosSolicitacaoTransferencia(
                    cessionario_cliente_id=cessionario_fake_id,
                    motivo_categoria=(
                        MotivoCategoriaTransferencia.VENDA.value
                    ),
                    motivo_detalhe=(
                        "Tentativa com cliente cessionario inexistente — "
                        "mensagem deve ser igual a do caso cross-tenant."
                    ),
                    aceite_cedente=_aceite_basico(operador.id),
                    aceite_cessionario=_aceite_basico(operador.id),
                ),
            )
    # Mesma mensagem do caso cross-tenant.
    assert "cliente nao encontrado" in str(exc_info.value).lower()
