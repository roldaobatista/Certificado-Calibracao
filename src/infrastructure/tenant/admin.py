from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("nome_fantasia", "slug", "plano", "status_lifecycle", "criado_em")
    list_filter = ("status_lifecycle", "plano")
    search_fields = ("nome_fantasia", "slug")
    readonly_fields = ("id", "criado_em", "atualizado_em")
    fieldsets = (
        (None, {"fields": ("id", "slug", "nome_fantasia")}),
        ("Estado", {"fields": ("plano", "status_lifecycle")}),
        ("Timestamps", {"fields": ("criado_em", "atualizado_em")}),
    )
