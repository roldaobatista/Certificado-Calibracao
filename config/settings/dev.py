"""Settings de desenvolvimento (local docker compose)."""

from typing import Any, cast

from .base import *  # — overlay padrao Django: base define tudo, dev sobrepoe

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Toolbar/extensoes uteis em dev (sem mascarar regra de prod).
# F405 reclama que INSTALLED_APPS vem de star import; e o pattern padrao Django settings.
INSTALLED_APPS += [
    "django_extensions"
]  # — INSTALLED_APPS vem do star import de base.py (padrao Django settings overlay)

# Logging verboso pra agente IA debugar.
# LOGGING vem do star import de base.py; cast pra dict pra mypy.
_LOGGING: dict[str, Any] = cast(dict[str, Any], LOGGING)  # — star import
_LOGGING["root"]["level"] = "DEBUG"

# Em dev permite SECRET_KEY default insegura via .env, mas registra warning.
# Em prod (config/settings/prod.py) SECRET_KEY sem default — falha duro.
