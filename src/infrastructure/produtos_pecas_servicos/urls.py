"""URL routing da frente `produtos-pecas-servicos` (T-PPS-033).

2 ViewSets via DefaultRouter (`catalogo/{itens,tabelas}`). Plugado em
config/urls.py raiz (lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import ItemCatalogoViewSet, TabelaPrecoViewSet

router = DefaultRouter()
router.register("catalogo/itens", ItemCatalogoViewSet, basename="catalogo-itens")
router.register("catalogo/tabelas", TabelaPrecoViewSet, basename="catalogo-tabelas")

urlpatterns = [
    *router.urls,
]
