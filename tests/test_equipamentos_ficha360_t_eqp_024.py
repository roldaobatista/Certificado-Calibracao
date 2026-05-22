"""T-EQP-024 + T-EQP-030 + T-EQP-031 — endpoint GET
`/api/v1/equipamentos/{id}/ficha360/`.

Cobre:
- AC-EQP-003-1: ficha 360 retorna dados + versoes + aprovacoes +
  certificados + eventos.
- AC-EQP-003-7 / P-EQP-R1: bloco `perfil_no_momento_do_cadastro`
  (snapshot imutavel).
- P-EQP-R7: finalidade obrigatoria (query param enum
  `FinalidadeAcessoCliente`).
- INV-013: grava `AcessoDadosCliente` ANTES de renderizar.
- INV-TENANT-001: tenant A nao ve ficha de tenant B (404).
- INV-AUTHZ-001: perfil sem `equipamentos.ficha360` toma 403.
- Anti-PII (mesmo padrao etiqueta): payload nao vaza CPF/CNPJ direto
  do cliente.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.audit.models import AcessoDadosCliente
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoVersao,
    MotivoMudancaEquipamentoVersao,
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
    tenant_a = TenantFactory(slug=f"f360-a-{sfx}", nome_fantasia="Lab A")
    tenant_b = TenantFactory(slug=f"f360-b-{sfx}", nome_fantasia="Lab B")
    admin_a = UsuarioFactory(email=f"adm-a-{sfx}@e.local")
    admin_b = UsuarioFactory(email=f"adm-b-{sfx}@e.local")
    leitor_a = UsuarioFactory(email=f"ler-a-{sfx}@e.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=leitor_a, tenant=tenant_a, perfil="cliente_externo_leitura")
    for u, t in [(admin_a, tenant_a), (admin_b, tenant_b), (leitor_a, tenant_a)]:
        invalidate_user_cache(u.id, t.id)

    with run_in_tenant_context(tenant_a.id):
        cliente_a = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Privado F360 X-CPF-99988877766",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_a = Equipamento.objects.create(
            tenant=tenant_a,
            tag="F360-A-001",
            numero_serie="NS-F360-A",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente_a,
            perfil_tenant_snapshot={
                "perfil": "D",
                "schema": "1.0.0",
                "grandezas_acreditadas": ["massa"],
            },
            snapshot_schema_version="1.0.0",
        )
        # Cria 1 versao pra ficha mostrar.
        EquipamentoVersao.objects.create(
            tenant=tenant_a,
            equipamento=eq_a,
            campo="modelo",
            valor_anterior_hash="abc",
            valor_novo_hash="def",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL.value,
            criado_por=admin_a,
        )
    with run_in_tenant_context(tenant_b.id):
        eq_b = Equipamento.objects.create(
            tenant=tenant_b,
            tag="F360-B-001",
            numero_serie="NS-F360-B",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={"perfil": "C"},
        )
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "leitor_a": leitor_a,
        "cliente_a": cliente_a,
        "eq_a": eq_a,
        "eq_b": eq_b,
    }


# ----------------------------------------------------------------------
# Happy
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_admin_acessa_ficha360_200(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/"
        "?finalidade=executar_os"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["equipamento"]["id"] == str(cenario["eq_a"].id)
    assert body["equipamento"]["tag"] == "F360-A-001"
    assert "perfil_no_momento_do_cadastro" in body
    assert body["perfil_no_momento_do_cadastro"]["snapshot"]["perfil"] == "D"
    assert body["perfil_no_momento_do_cadastro"]["snapshot_schema_version"] == "1.0.0"
    assert len(body["versoes"]) == 1
    assert body["versoes"][0]["campo"] == "modelo"
    assert body["aprovacoes_pendentes"] == []
    assert body["certificados"]["tem_vigente"] is False
    assert isinstance(body["eventos"], list)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ficha360_bloco_perfil_imutavel(cenario):
    """AC-EQP-003-7 / P-EQP-R1 — bloco perfil_no_cadastro existe sempre."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=auditoria_interna"
    )
    body = resp.json()
    bloco = body["perfil_no_momento_do_cadastro"]
    assert bloco["snapshot"]["perfil"] == "D"
    assert bloco["snapshot"]["grandezas_acreditadas"] == ["massa"]


# ----------------------------------------------------------------------
# INV-013 — log de acesso
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_013_grava_acesso_antes_de_renderizar(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=preparar_orcamento"
    )
    assert resp.status_code == 200, resp.content
    with run_in_tenant_context(cenario["tenant_a"].id):
        acesso = (
            AcessoDadosCliente.objects.filter(
                tenant_id=cenario["tenant_a"].id,
                cliente_id=cenario["cliente_a"].id,
                finalidade="preparar_orcamento",
            )
            .order_by("-id")
            .first()
        )
    assert acesso is not None
    assert acesso.usuario_id == cenario["admin_a"].id
    # R1 advogado — recurso sem PII; apenas UUIDs.
    assert str(cenario["eq_a"].id) in str(acesso.recurso)
    assert "11222333000181" not in str(acesso.recurso)


# ----------------------------------------------------------------------
# Finalidade enum
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_finalidade_invalida_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=nao_existe"
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "finalidade_obrigatoria_e_enum"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_finalidade_ausente_400(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/")
    assert resp.status_code == 400


# ----------------------------------------------------------------------
# RLS cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_cross_tenant_404(cenario):
    """tenant_a tenta ler ficha de equipamento do tenant_b -> 404."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_b'].id}/ficha360/?finalidade=executar_os"
    )
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# Authz
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_perfil_sem_ficha360_toma_403(cenario):
    """cliente_externo_leitura nao tem `equipamentos.ficha360`."""
    client = APIClient()
    _autenticar(client, cenario["leitor_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=executar_os"
    )
    assert resp.status_code == 403


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_unauth_401(cenario):
    client = APIClient()
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=executar_os"
    )
    assert resp.status_code in (401, 403)


# ----------------------------------------------------------------------
# Anti-PII no payload
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_payload_nao_vaza_nome_cliente_cru(cenario):
    """Ficha 360 nao deve trazer nome do cliente em texto cru —
    apenas cliente_atual_id. Wave A expande com porta cliente
    sanitizada se UI precisar do nome."""
    client = APIClient()
    _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
    resp = client.get(
        f"/api/v1/equipamentos/{cenario['eq_a'].id}/ficha360/?finalidade=executar_os"
    )
    body_txt = resp.content.decode("utf-8")
    assert "Cliente Privado F360" not in body_txt
    # cliente_atual_id deve estar visivel
    assert str(cenario["cliente_a"].id) in body_txt
