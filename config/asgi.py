"""ASGI entrypoint (uvicorn/daphne — usado quando Wave A precisar de websockets/SSE)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
application = get_asgi_application()
