from django.contrib import admin

from .models import AuthzDecision, Perfil, PerfilAcao


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "tenant_id", "criado_em")
    search_fields = ("codigo", "nome")
    list_filter = ("tenant_id",)
    readonly_fields = ("id", "criado_em")


@admin.register(PerfilAcao)
class PerfilAcaoAdmin(admin.ModelAdmin):
    list_display = ("perfil", "acao", "pode_executar", "criado_em")
    list_filter = ("perfil", "pode_executar")
    search_fields = ("perfil__codigo", "acao")
    readonly_fields = ("id", "criado_em")


@admin.register(AuthzDecision)
class AuthzDecisionAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario_id", "tenant_id", "action", "decision", "reason")
    list_filter = ("decision", "action")
    search_fields = ("usuario_id", "action", "reason")
    readonly_fields = tuple(f.name for f in AuthzDecision._meta.fields)

    def has_add_permission(self, request) -> bool:  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # type: ignore[no-untyped-def]
        return False
