from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_pessoa", "documento", "tenant", "criado_em")
    list_filter = ("tipo_pessoa", "tenant")
    search_fields = ("nome", "nome_fantasia", "documento", "email")
    readonly_fields = ("id", "criado_em", "atualizado_em")
