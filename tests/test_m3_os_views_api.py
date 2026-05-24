"""Testes API M3 OS Fase 8 (T-OS-094..099) — endpoints REST via APIClient.

Cobre:
- GET /v1/os/ (listagem)
- GET /v1/os/{id}/ (visao 360)
- GET /v1/os/{id}/timeline/
- POST /v1/atividades/os/{os_id}/atividades/ (adicionar)
- POST /v1/atividades/{id}/iniciar/

Pipeline: cria OS via use case direto (consumer Orcamento.Aprovado eh a
via primaria) + exercita endpoints REST com APIClient autenticado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from rest_framework.test import APIClient
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario,
        name="default",
        defaults={"confirmed": True},
    )
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"m3api-{sfx}")
    admin_u = UsuarioFactory(email=f"adm-{sfx}@os.local")
    tecnico_u = UsuarioFactory(email=f"tec-{sfx}@os.local")
    UsuarioPerfilTenantFactory(usuario=admin_u, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(
        usuario=tecnico_u, tenant=tenant, perfil="metrologista_bancada"
    )
    for u in (admin_u, tecnico_u):
        invalidate_user_cache(u.id, tenant.id)

    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"M3-API-{sfx}",
            numero_serie=f"NS-API-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "admin": admin_u,
        "tecnico": tecnico_u,
        "cliente": cliente,
        "equipamento": equipamento,
    }


def _abrir_os(cenario):
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=cenario["tenant"].id,
        cliente_id=cenario["cliente"].id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=cenario["equipamento"].id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(cenario["tenant"].id), transaction.atomic():
        return abrir_os_via_orcamento(payload=payload, repository=repo)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_get_os_lista_retorna_items_do_tenant(cenario):
    res_abrir = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    resp = client.get("/api/v1/os/")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["os_id"] == str(res_abrir.os_id)
    assert body["items"][0]["estado"] == "rascunho"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_get_os_retrieve_retorna_visao_360(cenario):
    res_abrir = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    resp = client.get(f"/api/v1/os/{res_abrir.os_id}/")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["os_id"] == str(res_abrir.os_id)
    assert body["numero_os"] == res_abrir.numero_os
    assert len(body["atividades"]) == 1
    assert body["atividades"][0]["tipo"] == "vistoria"
    assert body["atividades"][0]["tem_aceite"] is False


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_get_os_retrieve_404(cenario):
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    resp = client.get(f"/api/v1/os/{uuid4()}/")
    assert resp.status_code == 404
    assert resp.json()["codigo"] == "OSNaoEncontrada"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_get_timeline_retorna_eventos(cenario):
    res_abrir = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])

    resp = client.get(f"/api/v1/os/{res_abrir.os_id}/timeline/")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert len(body["items"]) >= 1
    assert any(e["tipo"] == "os_aberta" for e in body["items"])


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_post_atividade_iniciar_happy(cenario):
    """Pipeline: cria OS + atribui tecnico + chama POST iniciar via API."""
    res_abrir = _abrir_os(cenario)
    repo = DjangoOSRepository()
    with run_in_tenant_context(cenario["tenant"].id), transaction.atomic():
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=atividades[0].id,
                        tecnico_executor_id=cenario["tecnico"].id,
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    resp = client.post(
        f"/api/v1/atividades/{atividades[0].id}/iniciar/",
        data={"client_event_id": str(uuid4())},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["os_transitou_para_em_execucao"] is True


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_get_os_sem_auth_retorna_403(cenario):
    """RequireAuthz global bloqueia request sem sessao/MFA."""
    client = APIClient()
    resp = client.get("/api/v1/os/")
    assert resp.status_code in (401, 403)
