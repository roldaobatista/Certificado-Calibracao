"""URL routing da frente `produtos-pecas-servicos` (T-PPS-033/042).

3 ViewSets via DefaultRouter (`catalogo/{itens,tabelas,importacoes}`). Plugado
em config/urls.py raiz (lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import (
    ImportacaoCatalogoViewSet,
    ItemCatalogoViewSet,
    TabelaPrecoViewSet,
)

router = DefaultRouter()
router.register("catalogo/itens", ItemCatalogoViewSet, basename="catalogo-itens")
router.register("catalogo/tabelas", TabelaPrecoViewSet, basename="catalogo-tabelas")
router.register(
    "catalogo/importacoes", ImportacaoCatalogoViewSet, basename="catalogo-importacoes"
)

urlpatterns = [
    *router.urls,
]
