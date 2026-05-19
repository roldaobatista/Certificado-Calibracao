"""FB-C1+C3 — cadeia hash authz por-tenant + pré-tenant POR-USUÁRIO.

Cobre o design conjunto aprovado pelo tech-lead
(docs/faseamento/auditorias/FB-C1-design-cadeia-compartilhada.md, seção
"FB-C1+C3 CONJUNTO" + 4 bloqueantes absorvidos). Prova:

- cadeia pré-tenant POR-USUÁRIO encadeia (não bifurca) — BLOQ #1;
- isolamento pré-tenant entre usuários (RLS por-usuário) — FB-C3;
- cadeia do tenant independente (espelho T1 do audit);
- advisory lock authz isolado do de auditoria — classes distintas;
- normalização de `resource` fail-loud CEDO (fora da transação) — BLOQ #2;
- round-trip de integridade com tipos ricos (persistido == hasheado) — BLOQ #4;
- INSERT sob run_as_system NEGADO (sem permissivo morto) — review Q4;
- can() pré-tenant sem usuário falha alto (não reinicia cadeia) — BLOQ #2.
"""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db.utils import IntegrityError, InternalError, ProgrammingError
from django.utils import timezone
from src.infrastructure.audit.services import (
    _ADVISORY_LOCK_CLASSE_AUDIT,
    _ADVISORY_LOCK_CLASSE_AUTHZ,
    registrar_auditoria,
)
from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    invalidate_user_cache,
    verificar_integridade_cadeia_authz,
)
from src.infrastructure.authz.models import AuthzDecision
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
    run_in_user_context,
)

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

pytestmark = pytest.mark.tenant_isolation  # exige PG real (RLS/policies)


@pytest.mark.django_db(transaction=True)
class TestCadeiaPreTenantPorUsuario:
    def test_pre_tenant_mesmo_usuario_encadeia(self) -> None:
        """BLOQ #1: 2 can() pré-tenant do MESMO usuário encadeiam (não bifurca).

        Roda DENTRO de run_in_user_context (contexto REAL de login), NÃO
        montando GUC à mão — exigência do review tech-lead.
        """
        with run_as_system():
            usuario = UsuarioFactory()
        provider = DjangoAuthorizationProvider()

        with run_in_user_context(usuario.id):
            d1 = provider.can(
                usuario_id=usuario.id, action="tenant.listar", tenant_id=None
            )
            d2 = provider.can(
                usuario_id=usuario.id, action="tenant.listar", tenant_id=None
            )
            l1 = AuthzDecision.objects.get(id=d1.audit_id)
            l2 = AuthzDecision.objects.get(id=d2.audit_id)

        assert l1.tenant_id is None
        assert l1.hash_anterior is None  # 1ª linha da cadeia pré-tenant DESTE user
        assert l2.hash_anterior == l1.hash_atual  # encadeou — NÃO bifurcou

    def test_pre_tenant_isolado_entre_usuarios(self) -> None:
        """FB-C3: usuário B não vê nem encadeia na cadeia pré-tenant de A."""
        with run_as_system():
            ua, ub = UsuarioFactory(), UsuarioFactory()
        provider = DjangoAuthorizationProvider()

        with run_in_user_context(ua.id):
            da = provider.can(usuario_id=ua.id, action="tenant.listar", tenant_id=None)
            la = AuthzDecision.objects.get(id=da.audit_id)

        with run_in_user_context(ub.id):
            # B NÃO enxerga a linha pré-tenant de A (RLS por-usuário)
            visiveis = list(
                AuthzDecision.objects.filter(tenant_id__isnull=True).values_list(
                    "id", flat=True
                )
            )
            assert la.id not in visiveis
            db = provider.can(usuario_id=ub.id, action="tenant.listar", tenant_id=None)
            lb = AuthzDecision.objects.get(id=db.audit_id)

        # B começa a PRÓPRIA cadeia — não encadeia no elo de A
        assert lb.hash_anterior is None
        assert lb.hash_anterior != la.hash_atual

    def test_cadeia_tenant_independente(self) -> None:
        """Espelho T1 do audit: 2 tenants intercalados encadeiam cada um."""
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua, ub = UsuarioFactory(), UsuarioFactory()
            UsuarioPerfilTenantFactory(usuario=ua, tenant=ta, perfil="admin_tenant")
            UsuarioPerfilTenantFactory(usuario=ub, tenant=tb, perfil="admin_tenant")
        invalidate_user_cache(ua.id, ta.id)
        invalidate_user_cache(ub.id, tb.id)
        provider = DjangoAuthorizationProvider()

        with run_in_tenant_context(ta.id, usuario_id=ua.id):
            a1 = provider.can(usuario_id=ua.id, action="os.criar", tenant_id=ta.id)
            la1 = AuthzDecision.objects.get(id=a1.audit_id)
        with run_in_tenant_context(tb.id, usuario_id=ub.id):
            provider.can(usuario_id=ub.id, action="os.criar", tenant_id=tb.id)
        with run_in_tenant_context(ta.id, usuario_id=ua.id):
            a2 = provider.can(usuario_id=ua.id, action="os.criar", tenant_id=ta.id)
            la2 = AuthzDecision.objects.get(id=a2.audit_id)

        # A2 encadeia em A1 — NÃO no B que entrou no meio.
        assert la2.hash_anterior == la1.hash_atual

    def test_lock_authz_isolado_do_audit(self) -> None:
        """Classes de advisory lock distintas; INSERT de auditoria intercalado
        NÃO contamina a cadeia authz (espaços de lock separados)."""
        assert _ADVISORY_LOCK_CLASSE_AUTHZ != _ADVISORY_LOCK_CLASSE_AUDIT

        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()

        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            d1 = provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            registrar_auditoria(
                tenant_id=tenant.id,
                usuario_id=usuario.id,
                action="ruido.audit",
                resource_summary="r",
                payload={"x": 1},
            )
            d2 = provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            l1 = AuthzDecision.objects.get(id=d1.audit_id)
            l2 = AuthzDecision.objects.get(id=d2.audit_id)

        assert l2.hash_anterior == l1.hash_atual  # audit no meio não quebrou authz

    def test_resource_tipo_invalido_erro_claro_sem_gravar(self) -> None:
        """BLOQ #2: tipo não serializável → ValueError claro ANTES da
        transação; nenhuma linha gravada pela metade."""
        with run_as_system():
            usuario = UsuarioFactory()
        provider = DjangoAuthorizationProvider()

        class Opaco:
            pass

        with run_in_user_context(usuario.id):
            antes = AuthzDecision.objects.filter(tenant_id__isnull=True).count()
            with pytest.raises(ValueError, match="não serializável"):
                provider.can(
                    usuario_id=usuario.id,
                    action="tenant.listar",
                    resource={"obj": Opaco()},
                    tenant_id=None,
                )
            depois = AuthzDecision.objects.filter(tenant_id__isnull=True).count()
        assert depois == antes  # nada gravado

    def test_roundtrip_integridade_tipos_ricos(self) -> None:
        """BLOQ #4: can() com resource de tipos ricos (Decimal/UUID/set/
        datetime tz-aware) → verificação recomputa hash do PERSISTIDO →
        íntegro (persistido == hasheado)."""
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()

        resource = {
            "valor": Decimal("12.34"),
            "ref": uuid4(),
            "quando": timezone.now().astimezone(UTC),
            "tags": {"b", "a", "c"},
            "nested": {"lista": [1, "x", Decimal("0.1")]},
        }
        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            for _ in range(3):
                provider.can(
                    usuario_id=usuario.id,
                    action="os.criar",
                    resource=resource,
                    tenant_id=tenant.id,
                )
            ok, total, quebrados = verificar_integridade_cadeia_authz(
                {"tenant_id": tenant.id}
            )
        assert ok is True, f"cadeia acusou adulteração falsa: {quebrados}"
        assert total >= 3
        assert quebrados == []

    def test_adulteracao_no_meio_quebra_todos_os_seguintes(self) -> None:
        """FB-C5 (prova cripto, espelha T4 do audit): elo envenenado no MEIO
        quebra ESSE elo E TODOS os seguintes — `verificar_integridade_cadeia_
        authz` recomputa sha256 e encadeia no RECALCULADO (não no salvo)."""
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
            UsuarioPerfilTenantFactory(
                usuario=usuario, tenant=tenant, perfil="admin_tenant"
            )
        invalidate_user_cache(usuario.id, tenant.id)
        provider = DjangoAuthorizationProvider()

        with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
            provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            # Elo ENVENENADO: hash_atual não corresponde ao payload.
            AuthzDecision.objects.create(
                usuario_id=usuario.id,
                tenant_id=tenant.id,
                action="os.criar",
                resource_summary={},
                purpose="execucao_contrato",
                decision="allowed",
                reason="ok",
                perfis_aplicados=["admin_tenant"],
                escopo_avaliado={},
                hash_anterior="0" * 64,
                hash_atual="0" * 64,
            )
            provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            provider.can(usuario_id=usuario.id, action="os.criar", tenant_id=tenant.id)
            ok, total, quebrados = verificar_integridade_cadeia_authz(
                {"tenant_id": tenant.id}
            )
        assert ok is False
        assert total == 5
        # Elo envenenado + os 2 seguintes (encadeiam no recalculado): >=3.
        assert len(quebrados) >= 3

    def test_insert_sob_run_as_system_negado(self) -> None:
        """Review Q4: NÃO há branch `modo_sistema` no INSERT (permissivo
        morto = furo). INSERT em authz_decisions sob run_as_system → negado."""
        with run_as_system():
            with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
                AuthzDecision.objects.create(
                    usuario_id=uuid4(),
                    tenant_id=None,
                    action="forjado",
                    resource_summary={},
                    purpose="execucao_contrato",
                    decision="allowed",
                    reason="x",
                    perfis_aplicados=[],
                    escopo_avaliado={},
                    hash_atual="0" * 64,
                )

    def test_pre_tenant_sem_usuario_falha_alto(self) -> None:
        """BLOQ #2: gravar decisão pré-tenant sem usuário reiniciaria a cadeia
        silenciosamente — guard fail-loud no _gravar_audit."""
        provider = DjangoAuthorizationProvider()
        with pytest.raises(ValueError, match="POR-USUÁRIO"):
            provider._gravar_audit(
                usuario_id=None,  # type: ignore[arg-type]
                tenant_id=None,
                action="tenant.listar",
                resource={},
                purpose="execucao_contrato",
                decision=False,
                reason="x",
                perfis_aplicados=(),
                escopo_avaliado={},
            )
