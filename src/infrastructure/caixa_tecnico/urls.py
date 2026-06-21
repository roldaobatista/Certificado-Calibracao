"""URL routing da frente caixa-tecnico (T-CT-032 / Fatia 2).

ViewSets via DefaultRouter:
  - DespesaCaixaViewSet    → /api/v1/caixa-tecnico/despesas/
  - AdiantamentoCaixaViewSet → /api/v1/caixa-tecnico/adiantamentos/
  - PrestacaoContasViewSet → /api/v1/caixa-tecnico/prestacoes/

Plugado em config/urls.py raiz com ``path("api/v1/", include("src.infrastructure.caixa_tecnico.urls"))``.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    AdiantamentoCaixaViewSet,
    DespesaCaixaViewSet,
    PrestacaoContasViewSet,
)

router = DefaultRouter()
router.register(
    "caixa-tecnico/despesas",
    DespesaCaixaViewSet,
    basename="caixa-tecnico-despesas",
)
router.register(
    "caixa-tecnico/adiantamentos",
    AdiantamentoCaixaViewSet,
    basename="caixa-tecnico-adiantamentos",
)
router.register(
    "caixa-tecnico/prestacoes",
    PrestacaoContasViewSet,
    basename="caixa-tecnico-prestacoes",
)

urlpatterns = router.urls
