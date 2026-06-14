"""Testes de API REST — frente os-multi-equipamento (T-OSME-035 / ADR-0082).

Fecha a lacuna de cobertura via APIClient apontada no P9 (auditor-produto +
auditor-qualidade):
- `ItemComercialOSViewSet` (adicionar / remover / authz) via HTTP real — o teste
  de OS terminal (422) antes so verificava o enum, nao o ViewSet (achado M1).
- `AtividadeViewSet.criar` com `equipamento_id` + pre-check INV-OS-EQP-001
  (AC-OSME-003-1) — endpoint REST passou a aceitar o equipamento e bloquear
  equipamento BAIXADO/DESCARTADO (achado M5).

Cada POST usa Idempotency-Key (IDEMP-001). OS criada via use case direto
(consumer `Orcamento.Aprovado` e a via primaria de abertura).
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
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import OS, AtividadeDaOS
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_BASE_ITEM = "/api/v1/item-comercial-os/os/{os_id}/itens-comerciais/"
_BASE_ATIV = "/api/v1/atividades/os/{os_id}/atividades/"


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


def _criar_equip(cenario, status: str = EquipamentoStatus.ATIVO) -> Equipamento:
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(cenario["tenant"].id):
        return Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag=f"OSME-API2-{sfx}",
            numero_serie=f"NS2-{sfx}",
            fabricante="Toledo",
            modelo="Y",
            cliente_atual=cenario["cliente"],
            perfil_tenant_snapshot={"perfil": "D"},
            status=status,
        )


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"osmeapi-{sfx}")
    admin_u = UsuarioFactory(email=f"adm-{sfx}@osme.local")
    atendente_u = UsuarioFactory(email=f"atd-{sfx}@osme.local")
    tecnico_u = UsuarioFactory(email=f"tec-{sfx}@osme.local")
    UsuarioPerfilTenantFactory(usuario=admin_u, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente_u, tenant=tenant, perfil="atendente")
    UsuarioPerfilTenantFactory(
        usuario=tecnico_u, tenant=tenant, perfil="metrologista_bancada"
    )
    for u in (admin_u, atendente_u, tecnico_u):
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
        equip = Equipamento.objects.create(
            tenant=tenant,
            tag=f"OSME-API-{sfx}",
            numero_serie=f"NS-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {
        "tenant": tenant,
        "admin": admin_u,
        "atendente": atendente_u,
        "tecnico": tecnico_u,
        "cliente": cliente,
        "equip": equip,
    }


def _abrir_os(cenario, equipamento_id=None):
    repo = DjangoOSRepository()
    eid = equipamento_id if equipamento_id is not None else cenario["equip"].id
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=cenario["tenant"].id,
        cliente_id=cenario["cliente"].id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test",
        equipamento_id=None,
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
                equipamento_id=eid,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(cenario["tenant"].id), transaction.atomic():
        return abrir_os_via_orcamento(payload=payload, repository=repo)


# =============================================================
# ItemComercialOSViewSet via APIClient
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_item_comercial_adicionar_happy_201(cenario):
    """POST item comercial -> 201; valor soma em OS.valor_total_atualizado."""
    res = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["atendente"], cenario["tenant"])
    resp = client.post(
        _BASE_ITEM.format(os_id=res.os_id),
        data={
            "tipo": "deslocamento",
            "descricao_publica": "Deslocamento 50km",
            "valor": "80.00",
            "quantidade": 1,
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["tipo"] == "deslocamento"
    with run_in_tenant_context(cenario["tenant"].id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.valor_total_atualizado == Decimal("180.00")


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_item_comercial_os_terminal_422(cenario):
    """M1 (P9): exercita o ViewSet via HTTP — OS terminal -> 422 REAL.

    O teste de dominio anterior so verificava EstadoOS.terminal (enum), sem
    chamar o endpoint; aqui o caminho 422 do ViewSet e de fato exercitado.
    """
    res = _abrir_os(cenario)
    with run_in_tenant_context(cenario["tenant"].id):
        os_obj = OS.objects.get(id=res.os_id)
        os_obj.estado = "concluida"
        os_obj.save()

    client = APIClient()
    _autenticar(client, cenario["atendente"], cenario["tenant"])
    resp = client.post(
        _BASE_ITEM.format(os_id=res.os_id),
        data={"tipo": "taxa_visita", "descricao_publica": "Taxa", "valor": "50.00"},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 422, resp.content
    assert resp.json()["codigo"] == "OSTerminalNaoPermiteItemComercial"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_item_comercial_authz_tecnico_403(cenario):
    """metrologista_bancada NAO tem os.gerir_item_comercial -> 403."""
    res = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["tecnico"], cenario["tenant"])
    resp = client.post(
        _BASE_ITEM.format(os_id=res.os_id),
        data={"tipo": "outro", "descricao_publica": "X", "valor": "10.00"},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 403, resp.content


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_item_comercial_remover_subtrai_valor(cenario):
    """DELETE item comercial -> 200; valor subtraido de OS.valor_total_atualizado."""
    res = _abrir_os(cenario)
    client = APIClient()
    _autenticar(client, cenario["atendente"], cenario["tenant"])
    add = client.post(
        _BASE_ITEM.format(os_id=res.os_id),
        data={"tipo": "outro", "descricao_publica": "Item", "valor": "80.00"},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert add.status_code == 201, add.content
    item_id = add.json()["item_id"]

    rem = client.delete(
        f"{_BASE_ITEM.format(os_id=res.os_id)}{item_id}/",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert rem.status_code == 200, rem.content
    with run_in_tenant_context(cenario["tenant"].id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.valor_total_atualizado == Decimal("100.00")


# =============================================================
# AtividadeViewSet.criar com equipamento_id (AC-OSME-003-1)
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_adicionar_atividade_equip_ativo_happy(cenario):
    """POST atividade com equipamento_id -> 201; atividade carrega o equipamento."""
    res = _abrir_os(cenario)
    equip2 = _criar_equip(cenario, EquipamentoStatus.ATIVO)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    resp = client.post(
        _BASE_ATIV.format(os_id=res.os_id),
        data={
            "tipo": "calibracao",
            "sequencia": 2,
            "valor_unitario": "200.00",
            "equipamento_id": str(equip2.id),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 201, resp.content
    ativ_id = resp.json()["atividade_id"]
    with run_in_tenant_context(cenario["tenant"].id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert str(ativ.equipamento_id) == str(equip2.id)


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_api_adicionar_atividade_equip_baixado_422(cenario):
    """M5 (P9): AC-OSME-003-1 — equipamento SUCATA bloqueia adicionar atividade
    via REST (INV-OS-EQP-001 enforcement no caller, antes inexistente)."""
    res = _abrir_os(cenario)
    equip_sucata = _criar_equip(cenario, EquipamentoStatus.SUCATA)
    client = APIClient()
    _autenticar(client, cenario["admin"], cenario["tenant"])
    resp = client.post(
        _BASE_ATIV.format(os_id=res.os_id),
        data={
            "tipo": "calibracao",
            "sequencia": 2,
            "valor_unitario": "200.00",
            "equipamento_id": str(equip_sucata.id),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 422, resp.content
    assert resp.json()["codigo"] == "EquipamentoBaixadoEmOS"
    # Nenhuma atividade nova criada — transacao abortada.
    with run_in_tenant_context(cenario["tenant"].id):
        assert AtividadeDaOS.objects.filter(os_id=res.os_id).count() == 1
