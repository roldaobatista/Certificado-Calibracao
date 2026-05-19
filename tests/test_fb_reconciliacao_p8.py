"""Reconciliação F-B P8 — provas dos T-FB (causa-raiz).

- T-FB-01: predicate só roda no ESCOPO declarado; sem escopo → erro de
  registro (import-time); action sem predicate → ABAC neutro (não deny).
- T-FB-02: janela de vigência COMPLETA (fonte única) — perfil sensível
  EXPIRADO não barra mais o MFA (FB-A4).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

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
        mw = MfaRequiredMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]  # test double: get_response callable

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
        mw = MfaRequiredMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]  # test double: get_response callable

        class _Req:
            method = "GET"
            path = "/api/x"

        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            assert mw._tem_perfil_sensivel(_Req()) is True


@pytest.mark.django_db(transaction=True)
class TestIpHashT_FB_04:
    def test_ip_hash_preenchido_no_contexto_e_no_hash(self) -> None:
        """T-FB-04: ip_hash do contexto entra na linha E no hash
        (round-trip íntegro); HMAC versionado, nunca IP cru."""
        from src.infrastructure.audit.services import hashear_ip
        from src.infrastructure.authz.django_provider import (
            verificar_integridade_cadeia_authz,
        )
        from src.infrastructure.authz.models import AuthzDecision
        from src.infrastructure.multitenant.context import ip_hash_context

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()
        ip_cru = "203.0.113.7"
        esperado = hashear_ip(ip_cru)
        assert esperado and ip_cru not in esperado  # versionado, sem IP cru

        tok = ip_hash_context.set(esperado)
        try:
            with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
                d = provider.can(
                    usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id
                )
                linha = AuthzDecision.objects.get(id=d.audit_id)
                assert linha.ip_hash == esperado
                ok, _, quebrados = verificar_integridade_cadeia_authz(
                    {"tenant_id": tenant.id}
                )
        finally:
            ip_hash_context.reset(tok)
        assert ok is True, f"ip_hash não coberto pelo hash: {quebrados}"

    def test_sem_request_ip_hash_vazio(self) -> None:
        """Chamada sem request (contexto não setado) → ip_hash vazio,
        não-violação (AC-FB-008-2)."""
        from src.infrastructure.authz.models import AuthzDecision

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
            assert AuthzDecision.objects.get(id=d.audit_id).ip_hash == ""


@pytest.mark.django_db(transaction=True)
class TestResourceAllowlistT_FB_05:
    def test_chave_pii_por_valor_rejeitada(self) -> None:
        """T-FB-05: `cpf`/`nome` no resource → fail-loud ANTES da
        transação; nada gravado."""
        from src.infrastructure.authz.models import AuthzDecision

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            antes = AuthzDecision.objects.filter(tenant_id=tenant.id).count()
            with pytest.raises(ValueError, match="não permitida"):
                provider.can(
                    usuario_id=usuario.id,
                    action="os.criar",
                    resource={"cpf": "12345678900", "nome": "Fulano"},
                    tenant_id=tenant.id,
                )
            assert (
                AuthzDecision.objects.filter(tenant_id=tenant.id).count() == antes
            )

    def test_referencias_e_flags_passam(self) -> None:
        """`*_id`, `recurso_tipo`, `escopo`, flag bool → aceitos."""
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
                usuario_id=usuario.id,
                action="os.criar",
                resource={
                    "cliente_id": str(uuid4()),
                    "recurso_tipo": "os",
                    "urgente": True,
                },
                tenant_id=tenant.id,
            )
        assert d.allowed is True


@pytest.mark.django_db(transaction=True)
class TestRollbackOrfaoT_FB_06:
    def test_rollback_nao_deixa_decisao_orfa(self) -> None:
        """AC-FB-009-5 (BLOQ-4): a garantia REAL é atomicidade — rollback
        da transação ⇒ a linha NÃO persiste (não "commit antes do
        retorno", falso sob ATOMIC_REQUESTS)."""
        from django.db import transaction
        from src.infrastructure.authz.models import AuthzDecision

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()

        class _Boom(Exception):
            pass

        audit_id = None
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            try:
                with transaction.atomic():
                    d = provider.can(
                        usuario_id=usuario.id,
                        action="os.criar",
                        tenant_id=tenant.id,
                    )
                    audit_id = d.audit_id
                    raise _Boom()  # força rollback do savepoint
            except _Boom:
                pass
        assert audit_id is not None
        with run_as_system():
            # decisão NÃO órfã: rollou junto, não persistiu
            assert not AuthzDecision.objects.filter(id=audit_id).exists()

    def test_commit_persiste_decisao(self) -> None:
        """Não-regressão: sem rollback, a decisão persiste."""
        from src.infrastructure.authz.models import AuthzDecision

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
        with run_as_system():
            assert AuthzDecision.objects.filter(id=d.audit_id).exists()


@pytest.mark.django_db(transaction=True)
class TestMfaDjangoOtpRealT_FB_03:
    """FB-A6/AC-FB-007-6: exercita o `is_verified()` REAL do django-otp
    (TOTPDevice + OTPMiddleware), não o stub `_FakeUserMFAOff`."""

    def _request_otp(self, usuario, verificar: bool):
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.test import RequestFactory
        from django_otp import login as otp_login
        from django_otp.middleware import OTPMiddleware
        from django_otp.plugins.otp_totp.models import TOTPDevice

        rf = RequestFactory()
        req = rf.get("/api/os/")
        SessionMiddleware(lambda r: None)(req)
        req.user = usuario
        device = TOTPDevice.objects.create(
            user=usuario, name="t", confirmed=True
        )
        if verificar:
            otp_login(req, device)  # marca verificado na sessão (real)
        OTPMiddleware(lambda r: None)(req)  # embrulha user → is_verified() real
        return req

    def test_perfil_sensivel_otp_real_verificado_passa(self) -> None:
        from src.infrastructure.authz.middleware import MfaRequiredMiddleware

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        req = self._request_otp(usuario, verificar=True)
        assert req.user.is_verified() is True  # django-otp REAL
        passou = {"v": False}

        def nxt(r):
            passou["v"] = True
            return "ok"

        mw = MfaRequiredMiddleware(nxt)
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            assert mw(req) == "ok"
        assert passou["v"]

    def test_perfil_sensivel_otp_real_nao_verificado_401(self) -> None:
        from src.infrastructure.authz.middleware import MfaRequiredMiddleware

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        req = self._request_otp(usuario, verificar=False)
        assert req.user.is_verified() is False  # django-otp REAL, sem stub
        mw = MfaRequiredMiddleware(lambda r: None)  # type: ignore[arg-type,return-value]  # test double: get_response callable
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            resp = mw(req)
        assert resp is not None and resp.status_code == 401
