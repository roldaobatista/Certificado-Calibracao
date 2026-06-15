"""URL routing do modulo `orcamentos` (Fatia 2 — T-ORC-037/038).

  /api/v1/orcamentos/                          OrcamentoViewSet (create/list)
  /api/v1/orcamentos/{id}/                     retrieve
  /api/v1/orcamentos/{id}/itens/               adicionar_item
  /api/v1/orcamentos/{id}/itens/{item_id}/editar/  editar_item
  /api/v1/orcamento-templates/                 TemplateViewSet CRUD (gate selo RBC — T-ORC-039)
  /api/v1/orcamento-templates/{id}/            retrieve/update/destroy(soft-delete)
  /api/v1/public/orcamentos/{token}/           GET preview (publico, Onda 2e)
  /api/v1/public/orcamentos/{token}/aprovar/   POST aprovacao 1-clique (publico)

O endpoint publico (token resolve tenant SEM RLS — D-ORC-19) fica no allowlist do
TenantMiddleware (`/api/v1/public/orcamentos/`). Templates em rota propria
(`orcamento-templates`) — evita colisao com `/orcamentos/{pk}`.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path
from rest_framework.routers import DefaultRouter

from src.infrastructure.orcamentos.views import OrcamentoViewSet
from src.infrastructure.orcamentos.views_publicas import orcamento_publico_view
from src.infrastructure.orcamentos.views_template import TemplateViewSet

router = DefaultRouter()
router.register(r"orcamentos", OrcamentoViewSet, basename="orcamento")
router.register(r"orcamento-templates", TemplateViewSet, basename="orcamento-template")

urlpatterns: list[URLPattern | URLResolver] = [
    # Endpoint publico (token opaco). POST /aprovar e GET preview na mesma view.
    path(
        "public/orcamentos/<str:token>/aprovar/",
        orcamento_publico_view,
        name="orcamento-publico-aprovar",
    ),
    path("public/orcamentos/<str:token>/", orcamento_publico_view, name="orcamento-publico"),
    *router.urls,
]
