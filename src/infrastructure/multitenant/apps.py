from django.apps import AppConfig


class MultitenantConfig(AppConfig):
    name = "src.infrastructure.multitenant"
    label = "multitenant"
    verbose_name = "Trava de isolamento entre tenants (RLS + middleware)"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Conecta signal que reseta variaveis PG no checkout de conexao do pool."""
        from . import connection  # noqa: F401 — registra signal connection_created
