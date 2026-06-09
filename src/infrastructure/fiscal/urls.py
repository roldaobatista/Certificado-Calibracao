"""URL routing da frente fiscal/NFS-e (T-FIS-032).

NotaFiscalServicoViewSet via DefaultRouter (`fiscal/nfse`). Plugado em
config/urls.py raiz (lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import NotaFiscalServicoViewSet

router = DefaultRouter()
router.register("fiscal/nfse", NotaFiscalServicoViewSet, basename="fiscal-nfse")

urlpatterns = [
    *router.urls,
]
