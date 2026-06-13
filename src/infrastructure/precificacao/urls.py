"""URL routing da frente `precificacao` (Fatia 1b — placeholder).

Views criadas na Fatia 2 (T-PRC-035). Arquivo presente agora para que
config/urls.py possa incluir sem erro (molde PPS / fiscal).
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver

urlpatterns: list[URLPattern | URLResolver] = []
