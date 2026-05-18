"""Isolamento cross-tenant na camada de authz (INV-AUTHZ-003).

Cenarios:
1. Usuario com perfil em tenant A NAO consegue agir em tenant B (sem perfil la).
2. Usuario multi-tenant {A, B} TENTA acessar tenant C → bloqueado.
3. authz_decisions de tenant A nao sao visiveis na sessao de tenant B (RLS).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
)
from src.infrastructure.authz.models import AuthzDecision
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_authz_003_usuario_sem_perfil_em_tenant_e_negado():
    """Usuario com perfil so em tenant A, ao tentar em tenant B = denied."""
    suffix = uuid4().hex[:8]
    tenant_a = TenantFactory(slug=f"a-{suffix}")
    tenant_b = TenantFactory(slug=f"b-{suffix}")
    usuario = UsuarioFactory(email=f"u-{suffix}@iso.local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant_a, perfil="admin_tenant")
    invalidate_user_cache(usuario.id, tenant_a.id)
    invalidate_user_cache(usuario.id, tenant_b.id)

    provider = DjangoAuthorizationProvider()

    with run_in_tenant_context(tenant_b.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action="os.criar",
            tenant_id=tenant_b.id,
        )

    assert decision.allowed is False
    assert decision.reason == "sem_perfil_no_tenant"


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_authz_003_multi_tenant_nao_acessa_tenant_fora_da_lista():
    """Usuario admin em A e B tenta agir em C (sem perfil) = denied."""
    suffix = uuid4().hex[:8]
    tenant_a = TenantFactory(slug=f"a-{suffix}")
    tenant_b = TenantFactory(slug=f"b-{suffix}")
    tenant_c = TenantFactory(slug=f"c-{suffix}")
    usuario = UsuarioFactory(email=f"u-{suffix}@iso.local")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=usuario, tenant=tenant_b, perfil="admin_tenant")
    for t in (tenant_a, tenant_b, tenant_c):
        invalidate_user_cache(usuario.id, t.id)

    provider = DjangoAuthorizationProvider()

    # Simulamos middleware injetando lista {A, B} mas request pede acao em C.
    # No fluxo real, o middleware rejeitaria antes de chegar aqui (active_tenant
    # nao na lista). Mas aqui testamos o provider isoladamente — ele tem que
    # tambem dizer denied (defesa em profundidade #3).
    with run_in_tenant_context(tenant_c.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action="os.criar",
            tenant_id=tenant_c.id,
        )

    assert decision.allowed is False
    assert decision.reason == "sem_perfil_no_tenant"


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
def test_inv_authz_003_authz_decisions_isoladas_por_tenant():
    """Decisao gravada em tenant A nao e visivel na sessao de tenant B (RLS)."""
    suffix = uuid4().hex[:8]
    tenant_a = TenantFactory(slug=f"a-{suffix}")
    tenant_b = TenantFactory(slug=f"b-{suffix}")
    usuario_a = UsuarioFactory(email=f"a-{suffix}@iso.local")
    usuario_b = UsuarioFactory(email=f"b-{suffix}@iso.local")
    UsuarioPerfilTenantFactory(usuario=usuario_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=usuario_b, tenant=tenant_b, perfil="admin_tenant")
    invalidate_user_cache(usuario_a.id, tenant_a.id)
    invalidate_user_cache(usuario_b.id, tenant_b.id)

    provider = DjangoAuthorizationProvider()

    # Decisao em tenant A
    with run_in_tenant_context(tenant_a.id, usuario_id=usuario_a.id):
        d_a = provider.can(usuario_id=usuario_a.id, action="os.criar", tenant_id=tenant_a.id)
        # Dentro do contexto A, decisao A e visivel
        assert AuthzDecision.objects.filter(id=d_a.audit_id).exists()

    # Na sessao de tenant B, decisao A NAO e visivel (RLS)
    with run_in_tenant_context(tenant_b.id, usuario_id=usuario_b.id):
        visivel = AuthzDecision.objects.filter(id=d_a.audit_id).exists()
        assert visivel is False, (
            "VAZAMENTO CROSS-TENANT! Decisao authz do tenant A foi visivel na "
            "sessao do tenant B."
        )
