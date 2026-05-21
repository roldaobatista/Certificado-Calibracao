"""T-EQP-001/008/010/049 — testes do modelo Equipamento (fundação Marco 2).

Cobertura mínima da fundação:
1. Cadastro básico em multi-tenant (RLS aplicado).
2. INV-049 — TAG única por tenant entre vivos.
3. Soft-delete libera TAG.
4. INV-EQP-001 — `perfil_tenant_snapshot` imutável via trigger PG.
5. AC-EQP-006-3a — transição de status inválida bloqueada.
6. AC-EQP-001-8 — `cliente_atual_id` SET NULL → status orfao_pendente_decisao.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db.utils import ProgrammingError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, EquipamentoStatus
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


@pytest.fixture
def cenario(db):
    tenant = TenantFactory(slug=f"eqp-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Equip Teste",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
    return {"tenant": tenant, "cliente": cliente}


@pytest.mark.django_db(transaction=True)
def test_cadastro_basico_equipamento(cenario):
    """T-EQP-001 — cadastro happy path."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="BAL-001",
            numero_serie="NS-1234",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cenario["cliente"],
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
    assert eq.status == EquipamentoStatus.ATIVO
    assert eq.tag == "BAL-001"


@pytest.mark.django_db(transaction=True)
def test_inv_049_tag_unica_por_tenant_entre_vivos(cenario):
    """INV-049 — TAG duplicada entre vivos rejeita."""
    from django.db.utils import IntegrityError

    with run_in_tenant_context(cenario["tenant"].id):
        Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="DUP-001",
            numero_serie="NS-A",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
        with pytest.raises(IntegrityError):
            Equipamento.objects.create(
                tenant=cenario["tenant"],
                tag="DUP-001",
                numero_serie="NS-B",
                fabricante="F",
                modelo="M",
                perfil_tenant_snapshot={},
            )


@pytest.mark.django_db(transaction=True)
def test_inv_049_soft_delete_libera_tag(cenario):
    """INV-049 — soft-delete libera TAG (UNIQUE parcial WHERE deletado_em IS NULL)."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq1 = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="REC-001",
            numero_serie="NS-A",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
        Equipamento.all_objects.filter(id=eq1.id).update(deletado_em=datetime.now(UTC))
        # Agora pode reusar a TAG
        eq2 = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="REC-001",
            numero_serie="NS-B",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
    assert eq2.id != eq1.id


@pytest.mark.django_db(transaction=True)
def test_inv_eqp_001_perfil_tenant_snapshot_imutavel(cenario):
    """INV-EQP-001 — trigger PG bloqueia mutação de `perfil_tenant_snapshot`."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="IMU-001",
            numero_serie="NS-1",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={"perfil": "D"},
        )
        with pytest.raises(ProgrammingError, match="INV-EQP-001"):
            Equipamento.all_objects.filter(id=eq.id).update(perfil_tenant_snapshot={"perfil": "A"})


@pytest.mark.django_db(transaction=True)
def test_ac_eqp_006_3a_transicao_invalida_bloqueada(cenario):
    """AC-EQP-006-3a — sucata para ativo é bloqueado (terminal-com-exceção sucata→extraviado apenas)."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="STA-001",
            numero_serie="NS-1",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
        # ativo → sucata é permitido
        Equipamento.all_objects.filter(id=eq.id).update(status=EquipamentoStatus.SUCATA)
        # sucata → ativo é proibido (só sucata→extraviado)
        with pytest.raises(ProgrammingError, match="transicao de status invalida"):
            Equipamento.all_objects.filter(id=eq.id).update(status=EquipamentoStatus.ATIVO)


@pytest.mark.django_db(transaction=True)
def test_ac_eqp_006_3a_sucata_para_extraviado_permitido(cenario):
    """AC-EQP-006-3a — única exceção de saída de sucata: extraviado."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="STA-002",
            numero_serie="NS-1",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
        Equipamento.all_objects.filter(id=eq.id).update(status=EquipamentoStatus.SUCATA)
        Equipamento.all_objects.filter(id=eq.id).update(status=EquipamentoStatus.EXTRAVIADO)
        eq.refresh_from_db()
    assert eq.status == EquipamentoStatus.EXTRAVIADO


@pytest.mark.django_db(transaction=True)
def test_ac_eqp_001_8_cliente_null_marca_orfao_pendente(cenario):
    """AC-EQP-001-8 — trigger marca status=orfao_pendente_decisao ao detectar cliente_atual=NULL."""
    with run_in_tenant_context(cenario["tenant"].id):
        eq = Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="ORF-001",
            numero_serie="NS-1",
            fabricante="F",
            modelo="M",
            cliente_atual=cenario["cliente"],
            perfil_tenant_snapshot={},
        )
        Equipamento.all_objects.filter(id=eq.id).update(cliente_atual_id=None)
        eq.refresh_from_db()
    assert eq.status == EquipamentoStatus.ORFAO_PENDENTE_DECISAO


@pytest.mark.django_db(transaction=True)
def test_isolamento_cross_tenant_rls(cenario):
    """INV-TENANT-001/002 — RLS isola equipamentos entre tenants."""
    tenant_b = TenantFactory(slug=f"eqp-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(cenario["tenant"].id):
        Equipamento.objects.create(
            tenant=cenario["tenant"],
            tag="ISO-001",
            numero_serie="NS-1",
            fabricante="F",
            modelo="M",
            perfil_tenant_snapshot={},
        )
    with run_in_tenant_context(tenant_b.id):
        visiveis = Equipamento.objects.count()
    assert visiveis == 0
