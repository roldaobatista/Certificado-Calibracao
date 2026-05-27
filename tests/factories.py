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

from uuid import uuid4

import factory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.feature_flag.models import FeatureFlag, FonteFlag
from src.infrastructure.tenant.models import StatusLifecycle, Tenant
from src.infrastructure.usuario.models import Usuario, UsuarioPerfilTenant


class TenantFactory(DjangoModelFactory):
    """Factory canonica do Tenant.

    T-SAN-PERFIL-023 (Sprint 2 ADR-0067): aceita trait/param `perfil` em
    {'A', 'B', 'C', 'D'} via TenantFactory(perfil='A') OU TenantFactory.perfil_a().

    Default: perfil='D' (conservador — sem rituais ISO 17025). Use traits
    explicitos pra testes que validam comportamento por perfil. Bug que so
    aparece em perfil 'A' (5% do ICP) escapava da suite quando default era
    implicitamente 'D' (FAIL L9 da auditoria 10 lentes 2026-05-27).

    Uso pra cenarios regulados:
        tenant_acreditado = TenantFactory.perfil_a()  # com numero RBC fake
        tenant_balancas = TenantFactory.perfil_b()    # rastreavel — caminho Roldao
        tenant_trilha = TenantFactory.perfil_c()      # em preparacao
        tenant_simples = TenantFactory.perfil_d()     # comercial puro (default)
    """

    class Meta:
        model = Tenant
        django_get_or_create = ("slug",)

    slug = factory.LazyFunction(lambda: f"tenant-{uuid4().hex[:8]}")
    nome_fantasia = factory.LazyAttribute(lambda obj: f"Empresa {obj.slug.title()}")
    plano = "placeholder"
    status_lifecycle = StatusLifecycle.ATIVO

    # Default conservador — perfil D (sem ISO 17025).
    perfil_regulatorio = "D"

    class Params:
        # Trait .perfil_a() — laboratorio acreditado RBC.
        perfil_a = factory.Trait(
            perfil_regulatorio="A",
            acreditacao_cgcre_numero=factory.LazyFunction(
                lambda: f"CRL {1000 + (uuid4().int % 9000):04d}"
            ),
            ilac_mra_aderido=True,
        )
        # Trait .perfil_b() — rastreavel nao-acreditado (caminho Roldao/Balancas Solution).
        perfil_b = factory.Trait(perfil_regulatorio="B")
        # Trait .perfil_c() — em preparacao para acreditar (trilha D->A).
        perfil_c = factory.Trait(perfil_regulatorio="C")
        # Trait .perfil_d() — comercial puro (explicito; equivale ao default).
        perfil_d = factory.Trait(perfil_regulatorio="D")


class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = Usuario
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.LazyFunction(lambda: f"user-{uuid4().hex[:8]}@teste.local")
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
    feature_key = factory.LazyFunction(lambda: f"feature-{uuid4().hex[:8]}")
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
    resource_summary = factory.LazyFunction(lambda: f"recurso-{uuid4().hex[:8]}")
    payload_jsonb = factory.LazyAttribute(lambda obj: {"action": obj.action})
    hash_anterior = None
    hash_atual = "placeholder-sem-chain-test"
