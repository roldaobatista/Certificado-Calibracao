"""URL routing do modulo `orcamentos` (Fatia 2 — T-ORC-037).

  /api/v1/orcamentos/                          OrcamentoViewSet (create/list)
  /api/v1/orcamentos/{id}/                     retrieve
  /api/v1/orcamentos/{id}/itens/               adicionar_item
  /api/v1/orcamentos/{id}/itens/{item_id}/editar/  editar_item

Endpoint publico (token) e TemplateViewSet entram nas ondas 2c/2e.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from src.infrastructure.orcamentos.views import OrcamentoViewSet

router = DefaultRouter()
router.register(r"orcamentos", OrcamentoViewSet, basename="orcamento")

urlpatterns: list[URLPattern | URLResolver] = router.urls
