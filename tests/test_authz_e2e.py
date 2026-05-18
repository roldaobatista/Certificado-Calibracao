"""E2E F-B — 16 cenarios cobrindo 4 perfis × 4 acoes × pos+neg.

Cobre INV-AUTHZ-001 (toda decisao passa pelo provider) + cenarios de
mortalidade da fase F-B em docs/faseamento-foundation-waves.md §3.

Perfis seed (criados pela migration 0003):
    admin_tenant, tecnico, rt_signatario, cliente_externo_leitura

Acoes testadas (matriz da migration 0003):
    os.criar, os.ler, certificado.emitir, fatura.estornar

Matriz esperada (P = permitido, X = bloqueado):

                       os.criar  os.ler  certificado.emitir  fatura.estornar
admin_tenant              P        P             P                P
tecnico                   P        P             X                X
rt_signatario             X        P             P                X
cliente_externo_leitura   X        P             X                X
"""

from __future__ import annotations

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


# Matriz pos/neg explicita — 16 celulas exatas (4 perfis × 4 acoes).
MATRIZ_ESPERADA = [
    # (perfil, acao, esperado_allowed)
    ("admin_tenant", "os.criar", True),
    ("admin_tenant", "os.ler", True),
    ("admin_tenant", "certificado.emitir", True),
    ("admin_tenant", "fatura.estornar", True),
    ("tecnico", "os.criar", True),
    ("tecnico", "os.ler", True),
    ("tecnico", "certificado.emitir", False),
    ("tecnico", "fatura.estornar", False),
    ("rt_signatario", "os.criar", False),
    ("rt_signatario", "os.ler", True),
    ("rt_signatario", "certificado.emitir", True),
    ("rt_signatario", "fatura.estornar", False),
    ("cliente_externo_leitura", "os.criar", False),
    ("cliente_externo_leitura", "os.ler", True),
    ("cliente_externo_leitura", "certificado.emitir", False),
    ("cliente_externo_leitura", "fatura.estornar", False),
]


@pytest.fixture
def cenario_basico(db):
    """Cria 1 tenant + 4 usuarios (um por perfil) ja vinculados.

    Retorna dict {perfil_codigo: usuario}.
    Slugs/emails dinamicos pra evitar colisao em parametrize de transaction.
    """
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"tenant-authz-{suffix}")
    usuarios = {}
    for codigo in ["admin_tenant", "tecnico", "rt_signatario", "cliente_externo_leitura"]:
        u = UsuarioFactory(email=f"{codigo}-{suffix}@teste-authz.local")
        UsuarioPerfilTenantFactory(usuario=u, tenant=tenant, perfil=codigo)
        usuarios[codigo] = u
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "usuarios": usuarios}


@pytest.fixture
def provider():
    return DjangoAuthorizationProvider()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("perfil,acao,esperado", MATRIZ_ESPERADA)
def test_inv_authz_001_matriz_4perfis_x_4acoes(
    cenario_basico, provider, perfil, acao, esperado
):
    """INV-AUTHZ-001: cada decisao passa pelo provider e devolve o que a matriz diz."""
    tenant = cenario_basico["tenant"]
    usuario = cenario_basico["usuarios"][perfil]

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        decision = provider.can(
            usuario_id=usuario.id,
            action=acao,
            tenant_id=tenant.id,
            purpose="execucao_contrato",
        )

    assert decision.allowed is esperado, (
        f"Perfil {perfil} acao {acao}: esperava allowed={esperado}, "
        f"veio {decision.allowed} (reason={decision.reason})"
    )

    if esperado:
        assert decision.reason == "ok"
        assert perfil in decision.perfis_aplicados
    else:
        assert decision.reason in ("rbac_denied", "sem_perfil_no_tenant")
