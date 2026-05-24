"""App config — webhook_out (F-C1 P4)."""

from django.apps import AppConfig


class WebhookOutConfig(AppConfig):
    default_auto_field = "django.db.models.UUIDField"
    name = "src.infrastructure.webhook_out"
    label = "webhook_out"
    verbose_name = "Webhook out provider (F-C1)"
