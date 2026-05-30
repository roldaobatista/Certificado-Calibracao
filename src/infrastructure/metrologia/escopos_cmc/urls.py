"""URL routing M6 escopos-cmc (T-ECMC-032).

EscopoCMCViewSet via DefaultRouter (`escopos-cmc`). Plugado em config/urls.py raiz
(lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import EscopoCMCViewSet

router = DefaultRouter()
router.register("escopos-cmc", EscopoCMCViewSet, basename="escopo-cmc")

urlpatterns = [
    *router.urls,
]
