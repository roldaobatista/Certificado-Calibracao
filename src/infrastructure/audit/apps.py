from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "src.infrastructure.audit"
    label = "audit"
    verbose_name = "Trilha de auditoria imutavel"
    default_auto_field = "django.db.models.BigAutoField"
