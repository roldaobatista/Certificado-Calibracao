from django.apps import AppConfig


class FeatureFlagConfig(AppConfig):
    name = "src.infrastructure.feature_flag"
    label = "feature_flag"
    verbose_name = "Feature flags (ativacao por tenant)"
    default_auto_field = "django.db.models.BigAutoField"
