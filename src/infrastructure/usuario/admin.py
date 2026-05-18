from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario, UsuarioPerfilTenant


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ("email", "nome_completo", "is_active", "is_staff", "mfa_obrigatorio")
    list_filter = ("is_active", "is_staff", "is_superuser", "mfa_obrigatorio")
    search_fields = ("email", "nome_completo")
    ordering = ("email",)
    readonly_fields = ("id", "criado_em", "atualizado_em", "last_login")
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Dados pessoais", {"fields": ("nome_completo",)}),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "mfa_obrigatorio",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Timestamps", {"fields": ("last_login", "criado_em", "atualizado_em")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "nome_completo"),
            },
        ),
    )


@admin.register(UsuarioPerfilTenant)
class UsuarioPerfilTenantAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tenant", "perfil", "valido_de", "valido_ate")
    list_filter = ("perfil", "tenant")
    search_fields = ("usuario__email", "tenant__slug", "perfil")
    autocomplete_fields = ("usuario", "tenant")
    readonly_fields = ("id", "criado_em")
