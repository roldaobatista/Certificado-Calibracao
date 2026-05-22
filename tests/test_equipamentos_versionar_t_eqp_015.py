"""T-EQP-015 (US-EQP-002 AC-EQP-002-4 / P-EQP-R2) — despacho automatico
entre criacao direta de versao e solicitacao de aprovacao gestor_qualidade.

Cobre:
- Service `criar_ou_solicitar_versao_equipamento` despacha por motivo.
- Endpoint POST `/equipamentos/{id}/versao/`:
  - motivo livre → 201 com versao_id (cria EquipamentoVersao direto).
  - motivo OBRIGA aprovacao → 202 com aprovacao_id (sem versao).
  - motivo fora do enum → 400.
  - motivo_detalhe curto/PII em motivo que obriga → 400.
- Service `efetivar_versao_a_partir_de_aprovacao` cria versao apos
  aprovacao APROVADA.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    EquipamentoVersao,
    MotivoMudancaEquipamentoVersao,
    StatusAprovacaoVersao,
)
from src.infrastructure.equipamentos.services_aprovacao import aprovar
from src.infrastructure.equipamentos.services_versao import (
    DadosCriacaoVersao,
    criar_ou_solicitar_versao_equipamento,
    efetivar_versao_a_partir_de_aprovacao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"ver-{sfx}")
    operador = UsuarioFactory(email=f"op-ver-{sfx}@e.local")
    gestor = UsuarioFactory(email=f"gestor-ver-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=operador, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=gestor, tenant=tenant, perfil="gestor_qualidade"
    )
    for u in [operador, gestor]:
        invalidate_user_cache(u.id, tenant.id)

    with run_in_tenant_context(tenant.id, operador.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Ver",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"VER-{sfx}",
            numero_serie=f"NSVER-{sfx}",
            fabricante="Toledo",
            modelo="V",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {"tenant": tenant, "operador": operador, "gestor": gestor, "eq": eq}


# ====================================================================
# Service direto
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_livre_cria_versao_direta(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_ou_solicitar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            solicitante_id=cenario["operador"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="V",
                valor_novo="V2",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL.value,
                motivo_detalhe="Correcao de modelo apos confirmacao do cliente.",
            ),
        )
    assert resultado.exige_aprovacao is False
    assert resultado.versao_id is not None
    assert resultado.aprovacao_id is None
    with run_in_tenant_context(cenario["tenant"].id):
        EquipamentoVersao.objects.get(id=resultado.versao_id)  # nao levanta


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_outros_dispara_aprovacao(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_ou_solicitar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            solicitante_id=cenario["operador"].id,
            dados=DadosCriacaoVersao(
                campo="fabricante",
                valor_anterior="Toledo",
                valor_novo="Filizola",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
                motivo_detalhe=(
                    "Substituicao de fabricante por compatibilidade de pecas "
                    "apos descontinuidade de fornecedor. Cliente solicitou "
                    "troca. RT supervisionou."
                ),
            ),
        )
    assert resultado.exige_aprovacao is True
    assert resultado.versao_id is None
    assert resultado.aprovacao_id is not None
    with run_in_tenant_context(cenario["tenant"].id):
        aprov = AprovacaoPendenteEquipamentoVersao.objects.get(
            id=resultado.aprovacao_id
        )
    assert aprov.status == StatusAprovacaoVersao.PENDENTE
    # Nenhuma versao gravada ainda.
    with run_in_tenant_context(cenario["tenant"].id):
        assert not EquipamentoVersao.objects.filter(
            equipamento=cenario["eq"], campo="fabricante"
        ).exists()


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_substituicao_componente_critico_dispara_aprovacao(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_ou_solicitar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            solicitante_id=cenario["operador"].id,
            dados=DadosCriacaoVersao(
                campo="numero_serie",
                valor_anterior="NSANTIGO",
                valor_novo="NSNOVO",
                motivo_mudanca=(
                    MotivoMudancaEquipamentoVersao.SUBSTITUICAO_COMPONENTE_CRITICO.value
                ),
                motivo_detalhe=(
                    "Substituicao da celula de carga apos falha de fabrica. "
                    "Mantem caracteristicas metrologicas do modelo. "
                    "RT supervisionou."
                ),
            ),
        )
    assert resultado.exige_aprovacao is True


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_motivo_atualizacao_firmware_dispara_aprovacao(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_ou_solicitar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            solicitante_id=cenario["operador"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="V",
                valor_novo="V-fw2.1",
                motivo_mudanca=(
                    MotivoMudancaEquipamentoVersao.ATUALIZACAO_FIRMWARE.value
                ),
                motivo_detalhe=(
                    "Atualizacao de firmware para versao 2.1 com correcao "
                    "de bug de medicao em temperatura abaixo de 5C "
                    "(OIML D 31)."
                ),
            ),
        )
    assert resultado.exige_aprovacao is True


# ====================================================================
# Efetivacao apos aprovacao
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_efetivar_versao_a_partir_de_aprovacao_aprovada(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_ou_solicitar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            solicitante_id=cenario["operador"].id,
            dados=DadosCriacaoVersao(
                campo="fabricante",
                valor_anterior="Toledo",
                valor_novo="Filizola",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS.value,
                motivo_detalhe=(
                    "Substituicao de fabricante por compatibilidade de pecas. "
                    "Cliente solicitou troca por padrao novo. RT validou."
                ),
            ),
        )
        aprov = AprovacaoPendenteEquipamentoVersao.objects.get(
            id=resultado.aprovacao_id
        )

    with run_in_tenant_context(cenario["tenant"].id, cenario["gestor"].id):
        aprovar(
            tenant_id=cenario["tenant"].id,
            aprovacao=aprov,
            decisor_id=cenario["gestor"].id,
            parecer_gestor_texto=(
                "Mudanca de fabricante validada pelo RT. Documentacao "
                "completa. Aprovo a versao."
            ),
        )
        aprov.refresh_from_db()

    assert aprov.status == StatusAprovacaoVersao.APROVADA.value

    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado_versao = efetivar_versao_a_partir_de_aprovacao(
            aprovacao=aprov,
            valor_anterior_cru="Toledo",
            valor_novo_cru="Filizola",
        )
    assert resultado_versao.versao.campo == "fabricante"
    assert (
        resultado_versao.versao.motivo_mudanca
        == MotivoMudancaEquipamentoVersao.OUTROS.value
    )


# ====================================================================
# Endpoint
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_endpoint_motivo_livre_retorna_201(cenario):
    client = APIClient()
    _autenticar(client, cenario["operador"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/versao/",
        {
            "campo": "modelo",
            "valor_anterior": "V",
            "valor_novo": "V2",
            "motivo_mudanca": (
                MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL.value
            ),
            "motivo_detalhe": "Correcao de modelo apos confirmacao.",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["exige_aprovacao"] is False
    assert "versao_id" in body


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_endpoint_motivo_obriga_retorna_202(cenario):
    client = APIClient()
    _autenticar(client, cenario["operador"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/versao/",
        {
            "campo": "fabricante",
            "valor_anterior": "Toledo",
            "valor_novo": "Filizola",
            "motivo_mudanca": MotivoMudancaEquipamentoVersao.OUTROS.value,
            "motivo_detalhe": (
                "Substituicao de fabricante por compatibilidade de pecas "
                "apos descontinuidade. Cliente solicitou. RT validou."
            ),
        },
        format="json",
    )
    assert resp.status_code == 202, resp.content
    body = resp.json()
    assert "aprovacao_id" in body
    assert body["status"] == StatusAprovacaoVersao.PENDENTE
    assert body["motivo_mudanca"] == MotivoMudancaEquipamentoVersao.OUTROS.value


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_endpoint_motivo_fora_enum_retorna_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["operador"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/versao/",
        {
            "campo": "modelo",
            "valor_anterior": "V",
            "valor_novo": "V2",
            "motivo_mudanca": "motivo_que_nao_existe",
            "motivo_detalhe": "x",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_endpoint_motivo_detalhe_curto_em_motivo_obrigatorio_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["operador"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/equipamentos/{cenario['eq'].id}/versao/",
        {
            "campo": "fabricante",
            "valor_anterior": "Toledo",
            "valor_novo": "Filizola",
            "motivo_mudanca": MotivoMudancaEquipamentoVersao.OUTROS.value,
            "motivo_detalhe": "curto",  # <100 chars
        },
        format="json",
    )
    assert resp.status_code == 400
