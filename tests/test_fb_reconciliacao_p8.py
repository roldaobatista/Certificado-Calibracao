"""Reconciliação F-B P8 — provas dos T-FB (causa-raiz).

- T-FB-01: predicate só roda no ESCOPO declarado; sem escopo → erro de
  registro (import-time); action sem predicate → ABAC neutro (não deny).
- T-FB-02: janela de vigência COMPLETA (fonte única) — perfil sensível
  EXPIRADO não barra mais o MFA (FB-A4).
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
)
from src.infrastructure.authz.predicates import (
    clear_registry,
    predicates_aplicaveis,
    register_predicate,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

pytestmark = pytest.mark.tenant_isolation


class TestPredicateBindingT_FB_01:
    def setup_method(self) -> None:
        clear_registry()

    def teardown_method(self) -> None:
        clear_registry()

    def test_sem_escopo_erro_em_registro(self) -> None:
        """Predicate sem `actions` → ValueError NO REGISTRO (não runtime,
        não global cego — FB-A1)."""
        with pytest.raises(ValueError, match="sem escopo"):
            register_predicate("global_cego", lambda r: (True, ""))

    def test_predicate_so_roda_no_escopo(self) -> None:
        """Predicate de `cliente.*` NÃO é aplicável a `os.criar`."""
        register_predicate(
            "nega_cliente", lambda r: (False, "x"), actions={"cliente."}
        )
        assert [p.nome for p in predicates_aplicaveis("cliente.bloquear")] == [
            "nega_cliente"
        ]
        assert predicates_aplicaveis("os.criar") == []  # fora do escopo

    @pytest.mark.django_db(transaction=True)
    def test_action_sem_predicate_e_abac_neutro_nao_deny(self) -> None:
        """Predicate que SEMPRE nega, escopado a `cliente.*`; `can(os.criar)`
        → não roda o predicate → decisão segue RBAC (allowed), NÃO deny."""
        register_predicate(
            "sempre_nega", lambda r: (False, "nunca"), actions={"cliente."}
        )
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            d = provider.can(
                usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id
            )
        assert d.allowed is True  # ABAC neutro — predicate fora do escopo não rodou
        assert d.reason == "ok"


@pytest.mark.django_db(transaction=True)
class TestVigenciaUnicaT_FB_02:
    def test_perfil_sensivel_expirado_nao_barra_mfa(self) -> None:
        """FB-A4: perfil sensível com `valido_ate` no passado NÃO deve
        contar como sensível (janela completa) — antes barrava o MFA por
        ignorar `valido_ate`."""
        from src.infrastructure.authz.middleware import MfaRequiredMiddleware

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            ontem = timezone.now() - timedelta(days=1)
            UsuarioPerfilTenantFactory(
                usuario=usuario,
                tenant=tenant,
                perfil="admin_tenant",
                valido_de=timezone.now() - timedelta(days=10),
                valido_ate=ontem,  # EXPIRADO
            )
        mw = MfaRequiredMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]

        class _Req:
            method = "GET"
            path = "/api/x"

        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            # perfil expirou → não é sensível → _tem_perfil_sensivel False
            assert mw._tem_perfil_sensivel(_Req()) is False

    def test_perfil_sensivel_vigente_barra_mfa(self) -> None:
        """Não-regressão: perfil sensível VIGENTE ainda é detectado."""
        from src.infrastructure.authz.middleware import MfaRequiredMiddleware

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario,
                tenant=tenant,
                perfil="admin_tenant",
                valido_de=timezone.now() - timedelta(days=1),
                valido_ate=None,  # vigente (sem fim)
            )
        mw = MfaRequiredMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]

        class _Req:
            method = "GET"
            path = "/api/x"

        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            assert mw._tem_perfil_sensivel(_Req()) is True
