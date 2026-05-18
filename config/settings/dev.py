"""Settings de desenvolvimento (local docker compose)."""

from .base import *  # noqa: F401,F403 — overlay padrao Django: base define tudo, dev sobrepoe

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Toolbar/extensoes uteis em dev (sem mascarar regra de prod).
# F405 reclama que INSTALLED_APPS vem de star import; e o pattern padrao Django settings.
INSTALLED_APPS += ["django_extensions"]  # noqa: F405 — INSTALLED_APPS vem do star import de base.py (padrao Django settings overlay)

# Logging verboso pra agente IA debugar.
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405 — LOGGING vem do star import de base.py

# Em dev permite SECRET_KEY default insegura via .env, mas registra warning.
# Em prod (config/settings/prod.py) SECRET_KEY sem default — falha duro.
