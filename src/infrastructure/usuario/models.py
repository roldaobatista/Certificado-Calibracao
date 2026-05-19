"""Modelo Usuario (custom AUTH_USER_MODEL) + tabela M:N de perfis por tenant.

Usuario:
- email como USERNAME_FIELD (citext via constraint, case-insensitive unique)
- MFA via django-otp em F-B; campo mfa_obrigatorio aqui pra preparar
- AbstractBaseUser + PermissionsMixin (granularidade maxima)

UsuarioPerfilTenant (M:N):
- Fonte de verdade da LISTA de tenants permitidos pra um usuario (ADR-0002 v2 §3)
- valido_de/ate suporta perfis temporarios (auditor RBC visitante, contractor)
- Indice composto pra resolucao rapida no middleware (Marco 3)
"""

from __future__ import annotations

import typing
import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from src.infrastructure.tenant.models import Tenant


class UsuarioManager(BaseUserManager["Usuario"]):
    """Manager custom — Django exige quando AbstractBaseUser eh usado."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra: Any) -> Usuario:
        if not email:
            raise ValueError("Email obrigatorio")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> Usuario:
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> Usuario:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser exige is_staff=True")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser exige is_superuser=True")
        return self._create_user(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Pessoa que loga no sistema. Pode pertencer a N tenants via UsuarioPerfilTenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        max_length=254,
        help_text="Normalizado pra lowercase. Identificador unico de login.",
    )
    nome_completo = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Acesso ao /admin/ Django (independente de perfis de aplicacao).",
    )
    mfa_obrigatorio = models.BooleanField(
        default=False,
        help_text="True para perfis sensiveis (RT, admin_tenant). Marco F-B liga django-otp.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: typing.ClassVar[list[str]] = []

    class Meta:
        app_label = "usuario"
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return self.nome_completo or self.email

    def get_short_name(self) -> str:
        return (self.nome_completo or self.email).split()[0]


class UsuarioPerfilTenant(models.Model):
    """M:N usuario × tenant com perfil + janela de validade.

    Fonte de verdade pra ADR-0002 v2 (middleware setLISTA de tenants) +
    INV-AUTHZ-003 (lista permitida vem deste registro, nunca do cliente).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="perfis_tenant",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="perfis_usuario",
    )
    perfil = models.CharField(
        max_length=50,
        help_text=(
            "Identificador do perfil (ex: 'admin_tenant', 'tecnico', 'rt_signatario', "
            "'cliente_externo_leitura'). Catalogo completo entra Marco F-B (ADR-0012)."
        ),
    )
    valido_de = models.DateTimeField(default=timezone.now)
    valido_ate = models.DateTimeField(
        null=True,
        blank=True,
        help_text="NULL = sem expiracao. Perfis temporarios (auditor visitante) usam.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "usuario"
        db_table = "usuario_perfil_tenant"
        verbose_name = "Perfil do usuario por tenant"
        verbose_name_plural = "Perfis do usuario por tenant"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "tenant", "perfil"],
                name="uq_usuario_tenant_perfil",
            ),
        ]
        indexes = [
            # Resolucao do middleware (Marco 3): "quais tenants este usuario tem agora?"
            models.Index(
                fields=["usuario", "valido_de", "valido_ate"],
                name="ix_perfil_resolucao",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.usuario.email} @ {self.tenant.slug} ({self.perfil})"
