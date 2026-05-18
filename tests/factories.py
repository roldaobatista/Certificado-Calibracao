"""Factories factory-boy pros modelos-nucleo do Marco 2.

Uso:
    from tests.factories import TenantFactory, UsuarioFactory

    @pytest.mark.django_db
    def test_x():
        t = TenantFactory()
        u = UsuarioFactory()
        UsuarioPerfilTenantFactory(usuario=u, tenant=t, perfil="admin_tenant")
"""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.feature_flag.models import FeatureFlag, FonteFlag
from src.infrastructure.tenant.models import StatusLifecycle, Tenant
from src.infrastructure.usuario.models import Usuario, UsuarioPerfilTenant


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"tenant-{n}")
    nome_fantasia = factory.LazyAttribute(lambda obj: f"Empresa {obj.slug.title()}")
    plano = "placeholder"
    status_lifecycle = StatusLifecycle.ATIVO


class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = Usuario
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@teste.local")
    nome_completo = Faker("name", locale="pt_BR")
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs: object) -> None:
        if not create:
            return
        self.set_password(extracted or "senha-teste-12-chars")
        self.save()


class UsuarioPerfilTenantFactory(DjangoModelFactory):
    class Meta:
        model = UsuarioPerfilTenant

    usuario = factory.SubFactory(UsuarioFactory)
    tenant = factory.SubFactory(TenantFactory)
    perfil = "admin_tenant"


class FeatureFlagFactory(DjangoModelFactory):
    class Meta:
        model = FeatureFlag
        django_get_or_create = ("tenant", "modulo", "feature_key")

    tenant = factory.SubFactory(TenantFactory)
    modulo = "calibracao"
    feature_key = factory.Sequence(lambda n: f"feature-{n}")
    ativo = False
    fonte = FonteFlag.PLANO


class AuditoriaFactoryNoChain(DjangoModelFactory):
    """Auditoria SEM hash chain — usar apenas em testes que NAO testam chain.

    Pra testes do hash chain, use o service `registrar_auditoria()` diretamente.
    """

    class Meta:
        model = Auditoria

    tenant = factory.SubFactory(TenantFactory)
    usuario = factory.SubFactory(UsuarioFactory)
    action = "usuario.criado"
    resource_summary = factory.Sequence(lambda n: f"recurso-{n}")
    payload_jsonb = factory.LazyAttribute(lambda obj: {"action": obj.action})
    hash_anterior = None
    hash_atual = "placeholder-sem-chain-test"
