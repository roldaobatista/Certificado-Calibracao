from django.apps import AppConfig


class TenantConfig(AppConfig):
    name = "src.infrastructure.tenant"
    label = "tenant"
    verbose_name = "Tenants (clientes do sistema)"
    default_auto_field = "django.db.models.BigAutoField"
