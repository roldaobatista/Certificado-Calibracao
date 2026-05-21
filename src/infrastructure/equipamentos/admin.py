"""Django admin do modulo equipamentos (T-EQP-001 base)."""

from django.contrib import admin

from .models import Equipamento


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ("tag", "fabricante", "modelo", "cliente_atual", "status", "criado_em")
    list_filter = ("status", "tenant")
    search_fields = ("tag", "numero_serie", "modelo")
    readonly_fields = (
        "id",
        "criado_em",
        "atualizado_em",
        "perfil_tenant_snapshot",
        "snapshot_schema_version",
    )
