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

import pytest
from django.db import IntegrityError

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.feature_flag.models import FeatureFlag, FonteFlag
from src.infrastructure.tenant.models import StatusLifecycle, Tenant
from src.infrastructure.usuario.models import Usuario, UsuarioPerfilTenant


@pytest.mark.django_db
class TestTenantBasico:
    def test_cria_tenant_com_default_ativo(self) -> None:
        t = Tenant.objects.create(slug="balancas-solution", nome_fantasia="Balanças Solution")
        assert t.status_lifecycle == StatusLifecycle.ATIVO
        assert str(t) == "Balanças Solution (balancas-solution)"

    def test_slug_unique(self) -> None:
        Tenant.objects.create(slug="dup", nome_fantasia="A")
        with pytest.raises(IntegrityError):
            Tenant.objects.create(slug="dup", nome_fantasia="B")


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


@pytest.mark.django_db
class TestUsuarioPerfilTenant:
    def test_unique_constraint_usuario_tenant_perfil(self) -> None:
        t = Tenant.objects.create(slug="t1", nome_fantasia="T1")
        u = Usuario.objects.create_user(email="u@x.com", password="senha-12-chars")
        UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")
        with pytest.raises(IntegrityError):
            UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")

    def test_perfis_diferentes_no_mesmo_tenant_sao_permitidos(self) -> None:
        t = Tenant.objects.create(slug="t2", nome_fantasia="T2")
        u = Usuario.objects.create_user(email="u2@x.com", password="senha-12-chars")
        UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="admin_tenant")
        UsuarioPerfilTenant.objects.create(usuario=u, tenant=t, perfil="rt_signatario")
        assert UsuarioPerfilTenant.objects.filter(usuario=u, tenant=t).count() == 2


@pytest.mark.django_db
class TestAuditoriaImutabilidadeCodigo:
    """Marco 2 defende em CODIGO. Marco 4 reforca em TRIGGER PG."""

    def _criar_linha(self) -> Auditoria:
        return Auditoria.objects.create(
            action="usuario.criado",
            resource_summary="teste",
            payload_jsonb={"email": "x@y.com"},
            hash_atual="placeholder-marco-4-calcula",
        )

    def test_insert_permitido(self) -> None:
        linha = self._criar_linha()
        assert linha.pk is not None

    def test_update_bloqueado_em_codigo(self) -> None:
        linha = self._criar_linha()
        linha.action = "usuario.atualizado"
        with pytest.raises(RuntimeError, match="INSERT-only"):
            linha.save()

    def test_delete_bloqueado_em_codigo(self) -> None:
        linha = self._criar_linha()
        with pytest.raises(RuntimeError, match="INSERT-only"):
            linha.delete()


@pytest.mark.django_db
class TestFeatureFlag:
    def test_flag_global_tenant_null(self) -> None:
        f = FeatureFlag.objects.create(
            modulo="calibracao",
            feature_key="NFS-e-automatico",
            ativo=True,
            fonte=FonteFlag.GLOBAL,
        )
        assert f.tenant is None
        assert "(global)" in str(f)

    def test_flag_por_tenant_unique_com_modulo_e_key(self) -> None:
        t = Tenant.objects.create(slug="t3", nome_fantasia="T3")
        FeatureFlag.objects.create(tenant=t, modulo="m", feature_key="k", ativo=True)
        with pytest.raises(IntegrityError):
            FeatureFlag.objects.create(tenant=t, modulo="m", feature_key="k", ativo=False)
