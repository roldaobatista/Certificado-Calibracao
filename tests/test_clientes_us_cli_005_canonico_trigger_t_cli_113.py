"""T-CLI-113 / AC-CLI-005-7 — testes da trigger PG cliente_canonico_imutavel.

Defesa em profundidade runtime do INV-CLI-001. Trigger BEFORE UPDATE valida
transições — testes garantem que cada regra dispara erro PG.

Cobertura:

1. test_canonico_self_para_vencedor_vivo_permitido — caminho legítimo da
   mesclagem (1ª transição).
2. test_canonico_compress_intermediario_para_final_vivo_permitido —
   path compression (A→B já apontava pra B; agora aponta pra C vivo).
3. test_canonico_para_cliente_inexistente_bloqueado.
4. test_canonico_para_cliente_soft_deletado_bloqueado.
5. test_canonico_cross_tenant_bloqueado.
6. test_canonico_reverter_para_self_bloqueado — só permitido se OLD era self.
7. test_canonico_path_compression_via_resolver_funciona_end_to_end —
   integração com `resolver_cliente_canonico` (que faz UPDATE legítimo).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db.utils import IntegrityError
from src.infrastructure.clientes.canonico import resolver_cliente_canonico
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _criar_pj(tenant, *, documento, nome):
    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento=documento,
        nome=nome,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


@pytest.mark.django_db(transaction=True)
def test_canonico_self_para_vencedor_vivo_permitido():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        venc = _criar_pj(tenant, documento="11222333000181", nome="V")
        perd = _criar_pj(tenant, documento="33000167000101", nome="P")
        # transição legítima: self → vencedor_vivo
        Cliente.all_objects.filter(id=perd.id).update(cliente_canonico_id=venc.id)
        # sucesso — sem exceção
        perd_pos = Cliente.all_objects.get(id=perd.id)
        assert perd_pos.cliente_canonico_id == venc.id


@pytest.mark.django_db(transaction=True)
def test_canonico_compress_intermediario_para_final_vivo_permitido():
    """Fluxo real: A aponta pra B ENQUANTO B está vivo; depois A morre; B aponta
    pra C ENQUANTO C está vivo; depois B morre. Path compression A→C (C ainda
    vivo) deve passar pela trigger.
    """
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c_final = _criar_pj(tenant, documento="11222333000181", nome="C")
        b_meio = _criar_pj(tenant, documento="22333444000172", nome="B")
        a_inicio = _criar_pj(tenant, documento="33000167000101", nome="A")

        # 1ª mesclagem: A→B (B vivo, A morre depois — separar UPDATE de canonico_id
        # do UPDATE de deletado_em pra trigger não pegar B já morto)
        Cliente.all_objects.filter(id=a_inicio.id).update(cliente_canonico_id=b_meio.id)
        Cliente.all_objects.filter(id=a_inicio.id).update(deletado_em=datetime.now(UTC))

        # 2ª mesclagem: B→C (C vivo, B morre depois)
        Cliente.all_objects.filter(id=b_meio.id).update(cliente_canonico_id=c_final.id)
        Cliente.all_objects.filter(id=b_meio.id).update(deletado_em=datetime.now(UTC))

        # Path compression: A.cliente_canonico_id = B.id → A.cliente_canonico_id = C.id
        # Trigger valida que C é vivo do mesmo tenant — passa.
        Cliente.all_objects.filter(id=a_inicio.id).update(cliente_canonico_id=c_final.id)
        a_pos = Cliente.all_objects.get(id=a_inicio.id)
        assert a_pos.cliente_canonico_id == c_final.id


@pytest.mark.django_db(transaction=True)
def test_canonico_para_cliente_inexistente_bloqueado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        perd = _criar_pj(tenant, documento="11222333000181", nome="P")
        with pytest.raises(IntegrityError):
            Cliente.all_objects.filter(id=perd.id).update(cliente_canonico_id=uuid4())


@pytest.mark.django_db(transaction=True)
def test_canonico_para_cliente_soft_deletado_bloqueado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        venc_morto = _criar_pj(tenant, documento="11222333000181", nome="V-morto")
        # mata o "vencedor"
        Cliente.all_objects.filter(id=venc_morto.id).update(deletado_em=datetime.now(UTC))
        perd = _criar_pj(tenant, documento="33000167000101", nome="P")
        with pytest.raises(IntegrityError, match="cliente vivo"):
            Cliente.all_objects.filter(id=perd.id).update(cliente_canonico_id=venc_morto.id)


@pytest.mark.django_db(transaction=True)
def test_canonico_cross_tenant_bloqueado():
    """RLS já bloqueia leitura cross-tenant; trigger reforça com mensagem clara."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    # criar venc em tenant_b
    with run_in_tenant_context(tenant_b.id):
        venc_b = _criar_pj(tenant_b, documento="11222333000181", nome="V-B")
    # tentar apontar perdedor de tenant_a pra venc de tenant_b
    with run_in_tenant_context(tenant_a.id):
        perd_a = _criar_pj(tenant_a, documento="33000167000101", nome="P-A")
        # RLS USING bloqueia leitura → trigger acusa NOT FOUND (no tenant)
        with pytest.raises(IntegrityError):
            Cliente.all_objects.filter(id=perd_a.id).update(cliente_canonico_id=venc_b.id)


@pytest.mark.django_db(transaction=True)
def test_canonico_reverter_para_self_bloqueado():
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        venc = _criar_pj(tenant, documento="11222333000181", nome="V")
        perd = _criar_pj(tenant, documento="33000167000101", nome="P")
        # mesclagem legítima primeiro
        Cliente.all_objects.filter(id=perd.id).update(cliente_canonico_id=venc.id)
        # reverter pra self → bloqueado (OLD = venc.id != OLD.id)
        with pytest.raises(IntegrityError, match="Reverter cliente_canonico_id"):
            Cliente.all_objects.filter(id=perd.id).update(cliente_canonico_id=perd.id)


@pytest.mark.django_db(transaction=True)
def test_canonico_path_compression_via_resolver_funciona_end_to_end():
    """A trigger NÃO deve atrapalhar `resolver_cliente_canonico` que faz
    path compression em UPDATE (caminho legítimo de leitura)."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        c_final = _criar_pj(tenant, documento="11222333000181", nome="C")
        b_meio = _criar_pj(tenant, documento="22333444000172", nome="B")
        a_inicio = _criar_pj(tenant, documento="33000167000101", nome="A")

        # Encadeia A→B→C ENQUANTO targets estão vivos; soft-delete depois.
        Cliente.all_objects.filter(id=a_inicio.id).update(cliente_canonico_id=b_meio.id)
        Cliente.all_objects.filter(id=a_inicio.id).update(deletado_em=datetime.now(UTC))
        Cliente.all_objects.filter(id=b_meio.id).update(cliente_canonico_id=c_final.id)
        Cliente.all_objects.filter(id=b_meio.id).update(deletado_em=datetime.now(UTC))

        # resolver deve seguir cadeia E aplicar path compression
        resultado = resolver_cliente_canonico(a_inicio.id)
        assert resultado == c_final.id

        # A agora aponta direto pra C
        a_pos = Cliente.all_objects.get(id=a_inicio.id)
        assert a_pos.cliente_canonico_id == c_final.id
