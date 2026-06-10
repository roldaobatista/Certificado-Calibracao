"""URL routing da frente `configuracoes-sistema` (T-CFG-033).

3 ViewSets via DefaultRouter (`configuracoes/{empresa,impostos,series}`).
Plugado em config/urls.py raiz (lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import EmpresaConfigViewSet, ImpostoViewSet, SerieDocumentoViewSet

router = DefaultRouter()
router.register("configuracoes/empresa", EmpresaConfigViewSet, basename="config-empresa")
router.register("configuracoes/impostos", ImpostoViewSet, basename="config-impostos")
router.register("configuracoes/series", SerieDocumentoViewSet, basename="config-series")

urlpatterns = [
    *router.urls,
]
