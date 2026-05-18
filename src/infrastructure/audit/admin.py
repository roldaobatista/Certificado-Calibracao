"""Admin somente-leitura pra Auditoria.

Mesmo o /admin/ Django (acesso de staff) NAO pode editar ou apagar. Defesa
em profundidade: codigo + trigger PG + admin readonly + (Marco 5) hook
audit-immutability-check no pre-commit.
"""

from django.contrib import admin
from django.http import HttpRequest

from .models import Auditoria


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "tenant", "usuario", "action", "resource_summary")
    list_filter = ("action", "tenant")
    search_fields = ("resource_summary", "usuario__email", "tenant__slug", "action")
    readonly_fields = (
        "id",
        "tenant",
        "usuario",
        "action",
        "resource_summary",
        "payload_jsonb",
        "hash_anterior",
        "hash_atual",
        "timestamp",
    )
    date_hierarchy = "timestamp"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # Auditoria so e inserida via use cases, nunca via /admin/

    def has_change_permission(self, request: HttpRequest, obj: Auditoria | None = None) -> bool:
        return False  # readonly

    def has_delete_permission(self, request: HttpRequest, obj: Auditoria | None = None) -> bool:
        return False  # imutavel
