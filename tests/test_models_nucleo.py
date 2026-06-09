"""Testes dos 4 modelos-nucleo do Marco 2.

Cobertura:
- Instanciacao basica (sem banco — checa que ORM aceita os campos)
- Validacoes hard:
    * Auditoria recusa UPDATE/DELETE (defesa de codigo)
    * UsuarioPerfilTenant respeita unique (usuario, tenant, perfil)
    * Tenant slug e unique
- Testes que dependem de RLS/multi-tenancy ficam no Marco 6 (test_isolamento_cross_tenant.py)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db import IntegrityError
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.feature_flag.models import FeatureFlag, FonteFlag
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.tenant.models import StatusLifecycle, Tenant
from src.infrastructure.usuario.models import Usuario, UsuarioPerfilTenant


@pytest.mark.django_db
class TestTenantBasico:
    def test_cria_tenant_com_default_ativo(self) -> None:
        t = Tenant.objects.create(
            slug="balancas-solution", nome_fantasia="Balanças Solution",
            perfil_regulatorio="D",
        )
        assert t.status_lifecycle == StatusLifecycle.ATIVO
        assert str(t) == "Balanças Solution (balancas-solution) [perfil=D]"

    def test_slug_unique(self) -> None:
        Tenant.objects.create(slug="dup", nome_fantasia="A", perfil_regulatorio="D")
        with pytest.raises(IntegrityError):
            Tenant.objects.create(slug="dup", nome_fantasia="B", perfil_regulatorio="D")


@pytest.mark.django_db
class TestUsuarioBasico:
    def test_cria_usuario_normaliza_email_lowercase(self) -> None:
        u = Usuario.objects.create_user(email="ROLDAO@example.com", password="senha-12-chars")
        assert u.email == "roldao@example.com"
        assert u.check_password("senha-12-chars")
        assert not u.is_staff
        assert not u.is_superuser

    def test_cria_superuser_seta_flags(self) -> None:
        u = Usuario.objects.create_superuser(email="admin@x.com", password="senha-12-chars")
        assert u.is_staff
        assert u.is_superuser

    def test_email_obrigatorio(self) -> None:
        with pytest.raises(ValueError, match="Email obrigatorio"):
            Usuario.objects.create_user(email="", password="senha-12-chars")

    def test_email_unique(self) -> None:
        Usuario.objects.create_user(email="a@b.com", password="senha-12-chars")
        with pytest.raises(IntegrityError):
            Usuario.objects.create_user(email="a@b.com", password="outra-12-chars")


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
class TestUsuarioPerfilTenant:
    """Tabela usuario_perfil_tenant tem RLS — INSERT exige run_as_system,
    SELECT exige run_in_tenant_context com usuario_id setado.
    """

    def test_unique_constraint_usuario_tenant_perfil(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"upt-u-{uid}", nome_fantasia="UPT", perfil_regulatorio="D"
            )
            u = Usuario.objects.create_user(
                email=f"upt-u-{uid}@x.com", password="senha-teste-12-chars"
            )
            UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")
            with pytest.raises(IntegrityError):
                UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")

    def test_perfis_diferentes_no_mesmo_tenant_sao_permitidos(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"upt-m-{uid}", nome_fantasia="UPT", perfil_regulatorio="D"
            )
            u = Usuario.objects.create_user(
                email=f"upt-m-{uid}@x.com", password="senha-teste-12-chars"
            )
            UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")
            UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="rt_signatario")
        # Leitura requer contexto onde app.usuario_id casa upt_self_select
        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            assert UsuarioPerfilTenant.objects.filter(usuario=u, tenant=t).count() == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
class TestAuditoriaImutabilidadeCodigo:
    """Marco 2 defende em CODIGO. Marco 4 reforca em TRIGGER PG.

    Marcado tenant_isolation porque a tabela auditoria tem RLS — exige
    contexto tenant pra INSERT/SELECT. Roda em ambiente com PG vivo + RLS.
    """

    def _criar_linha_em_contexto(self, tenant_id, usuario_id) -> Auditoria:
        return Auditoria.objects.create(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            action="usuario.criado",
            resource_summary="teste",
            payload_jsonb={"email": "x@y.com"},
            hash_atual="placeholder-marco-4-calcula",
        )

    def test_insert_permitido(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"aud-i-{uid}", nome_fantasia="Aud", perfil_regulatorio="D"
            )
            u = Usuario.objects.create_user(
                email=f"aud-i-{uid}@x.com", password="senha-teste-12-chars"
            )
        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = self._criar_linha_em_contexto(t.id, u.id)
            assert linha.pk is not None

    def test_update_bloqueado_em_codigo(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"aud-u-{uid}", nome_fantasia="Aud", perfil_regulatorio="D"
            )
            u = Usuario.objects.create_user(
                email=f"aud-u-{uid}@x.com", password="senha-teste-12-chars"
            )
        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = self._criar_linha_em_contexto(t.id, u.id)
            linha.action = "usuario.atualizado"
            with pytest.raises(RuntimeError, match="INSERT-only"):
                linha.save()

    def test_delete_bloqueado_em_codigo(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"aud-d-{uid}", nome_fantasia="Aud", perfil_regulatorio="D"
            )
            u = Usuario.objects.create_user(
                email=f"aud-d-{uid}@x.com", password="senha-teste-12-chars"
            )
        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = self._criar_linha_em_contexto(t.id, u.id)
            with pytest.raises(RuntimeError, match="INSERT-only"):
                linha.delete()


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
class TestFeatureFlag:
    """Marcado tenant_isolation pois INSERT em feature_flags passa por policy."""

    def test_flag_por_tenant_unique_com_modulo_e_key(self) -> None:
        uid = uuid4().hex[:8]
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"ff-uniq-{uid}", nome_fantasia="FF", perfil_regulatorio="D"
            )
        with run_in_tenant_context(tenant_id=t.id, usuario_id=None):
            FeatureFlag.objects.create(tenant=t, modulo="m", feature_key=f"k-{uid}", ativo=True)
            with pytest.raises(IntegrityError):
                FeatureFlag.objects.create(
                    tenant=t, modulo="m", feature_key=f"k-{uid}", ativo=False
                )

    def test_flag_global_tenant_null(self) -> None:
        with run_as_system():
            f = FeatureFlag.objects.create(
                modulo="calibracao",
                feature_key="NFS-e-automatico",
                ativo=True,
                fonte=FonteFlag.GLOBAL,
            )
            assert f.tenant is None
            assert "(global)" in str(f)
