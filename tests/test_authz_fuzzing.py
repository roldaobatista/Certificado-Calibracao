"""Fuzzing cross-tenant da camada authz — drill F-B.

Criterio de saida (faseamento-foundation-waves §3): usuario multi-tenant
tentando acessar tenant fora da lista = bloqueio em 100% das tentativas.

Replica o pattern do test_isolamento_cross_tenant.py de F-A mas focado
no AuthorizationProvider.can() ao inves do RLS bruto.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
@pytest.mark.slow
def test_fuzzing_500_tentativas_cross_tenant_zero_vazamento():
    """500 chamadas can() tentando tenant fora da lista → todas denied.

    Numero menor que F-A (5000) porque cada decisao grava em audit
    sincronamente. Suficiente pra demonstrar isolamento da porta.
    """
    suffix = uuid4().hex[:8]
    # 5 tenants
    tenants = [TenantFactory(slug=f"f{suffix}-{i}") for i in range(5)]
    # Usuario com perfil em tenants[0] e tenants[1] APENAS
    usuario = UsuarioFactory(email=f"f-{suffix}@fuzz.local")
    for t in tenants[:2]:
        UsuarioPerfilTenantFactory(usuario=usuario, tenant=t, perfil="admin_tenant")
    for t in tenants:
        invalidate_user_cache(usuario.id, t.id)

    provider = DjangoAuthorizationProvider()
    vazamentos = 0

    for i in range(500):
        # Alterna entre tentar tenant 0/1 (permitido) e 2/3/4 (proibido)
        idx_alvo = i % 5
        alvo = tenants[idx_alvo]

        with run_in_tenant_context(alvo.id, usuario_id=usuario.id):
            decision = provider.can(
                usuario_id=usuario.id,
                action="os.criar",
                tenant_id=alvo.id,
            )

        if idx_alvo in (0, 1):
            # Permitido — espera allowed
            if not decision.allowed:
                vazamentos += 1  # bug: bloqueou onde devia permitir
        else:
            # Proibido — espera denied
            if decision.allowed:
                vazamentos += 1  # bug: vazamento cross-tenant

    assert vazamentos == 0, f"Fuzzing detectou {vazamentos}/500 decisoes erradas"
