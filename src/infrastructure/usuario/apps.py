from django.apps import AppConfig


class UsuarioConfig(AppConfig):
    name = "src.infrastructure.usuario"
    label = "usuario"
    verbose_name = "Usuarios + perfis de acesso por tenant"
    default_auto_field = "django.db.models.BigAutoField"
