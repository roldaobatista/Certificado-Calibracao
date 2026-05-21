"""T-CLI-109 — predicate `cliente.bloqueado_para_entrega`.

AC-CLI-004-10: calibração em execução conclui mesmo com cliente bloqueado;
consumer `operacao/certificados` (Wave A) consulta predicate pra rotear pra
retenção física (CC art. 644). Predicate é consulta de domínio, NÃO ABAC —
chamador usa direto. Fail-safe: ID ausente/inválido → retém.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.clientes.bloqueio import (
    MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
    MOTIVO_MANUAL_INADIMPLENCIA,
)
from src.infrastructure.clientes.models import Cliente, ClienteBloqueio, TipoPessoa
from src.infrastructure.clientes.predicates_authz import cliente_bloqueado_para_entrega
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"entrega-{suffix}")
    admin = UsuarioFactory(email=f"adm-{suffix}@entrega.local")
    return {"tenant": tenant, "admin": admin}


def _criar_cliente(tenant, usuario) -> Cliente:
    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Entrega Teste",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )


@pytest.mark.django_db(transaction=True)
def test_cliente_nao_bloqueado_pode_entregar(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id):
        bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": str(cliente.id)})
    assert bloqueado is False
    assert motivo == ""


@pytest.mark.django_db(transaction=True)
def test_cliente_bloqueado_manual_retem_para_entrega(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        ClienteBloqueio.objects.create(
            cliente=cliente,
            tenant=cenario["tenant"],
            motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
            motivo_observacao="",
            justificativa_bruta="Cliente nao pagou 3 faturas e ignorou contatos",
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=cenario["admin"].id,
        )
        bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": str(cliente.id)})
    assert bloqueado is True
    assert motivo == "cliente_bloqueado_manual"


@pytest.mark.django_db(transaction=True)
def test_cliente_bloqueado_inadimplencia_retem_para_entrega(cenario):
    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        ClienteBloqueio.objects.create(
            cliente=cliente,
            tenant=cenario["tenant"],
            motivo_categoria=MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
            motivo_observacao="",
            justificativa_bruta="Inadimplencia automatica 90 dias",
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=None,
        )
        bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": str(cliente.id)})
    assert bloqueado is True
    assert motivo == "cliente_bloqueado_inadimplencia"


@pytest.mark.django_db(transaction=True)
def test_bloqueio_desbloqueado_nao_retem(cenario):
    """Histórico fechado (desbloqueado_em IS NOT NULL) não conta — alinhado com
    AC-CLI-004-5 (reativação)."""
    from django.utils import timezone

    cliente = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        ClienteBloqueio.objects.create(
            cliente=cliente,
            tenant=cenario["tenant"],
            motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
            motivo_observacao="",
            justificativa_bruta="Bloqueio anterior ja desfeito porque quitou",
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=cenario["admin"].id,
            desbloqueado_em=timezone.now(),
            desbloqueado_motivo="Quitou todos os titulos",
        )
        bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": str(cliente.id)})
    assert bloqueado is False
    assert motivo == ""


def test_fail_safe_cliente_id_ausente():
    bloqueado, motivo = cliente_bloqueado_para_entrega({})
    assert bloqueado is True
    assert motivo == "cliente_id_ausente"


def test_fail_safe_cliente_id_invalido():
    bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": "nao-e-uuid"})
    assert bloqueado is True
    assert motivo == "cliente_id_invalido"


@pytest.mark.django_db(transaction=True)
def test_isolamento_por_tenant_via_rls(cenario):
    """Predicate respeita RLS — bloqueio em tenant A não afeta consulta em tenant B."""
    cliente_a = _criar_cliente(cenario["tenant"], cenario["admin"])
    with run_in_tenant_context(cenario["tenant"].id, usuario_id=cenario["admin"].id):
        ClienteBloqueio.objects.create(
            cliente=cliente_a,
            tenant=cenario["tenant"],
            motivo_categoria=MOTIVO_MANUAL_INADIMPLENCIA,
            motivo_observacao="",
            justificativa_bruta="Bloqueio em tenant A para validar isolamento RLS",
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=cenario["admin"].id,
        )

    tenant_b = TenantFactory(slug=f"entrega-b-{uuid4().hex[:6]}")
    with run_in_tenant_context(tenant_b.id):
        bloqueado, motivo = cliente_bloqueado_para_entrega({"cliente_id": str(cliente_a.id)})
    # Tenant B não vê o ClienteBloqueio do tenant A (RLS) → predicate diz "não bloqueado".
    # Isso é correto: do ponto de vista de tenant B, o cliente_id é de outro tenant
    # (ou não existe no contexto dele). Consumer Wave A só consulta no tenant ativo.
    assert bloqueado is False
    assert motivo == ""
