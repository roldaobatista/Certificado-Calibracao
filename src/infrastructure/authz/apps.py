from django.apps import AppConfig


class AuthzConfig(AppConfig):
    """App de autorização (porta `AuthorizationProvider` + adapters).

    Foundation F-B (Marco F-B 1 em 2026-05-18).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.authz"
    label = "authz"
    verbose_name = "Autorização (RBAC + audit + AuthorizationProvider)"
