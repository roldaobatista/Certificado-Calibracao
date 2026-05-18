from django.contrib import admin

from .models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("modulo", "feature_key", "tenant", "ativo", "fonte", "atualizado_em")
    list_filter = ("ativo", "fonte", "modulo")
    search_fields = ("modulo", "feature_key", "tenant__slug")
    autocomplete_fields = ("tenant",)
    readonly_fields = ("id", "criado_em", "atualizado_em")
    list_editable = ("ativo",)
