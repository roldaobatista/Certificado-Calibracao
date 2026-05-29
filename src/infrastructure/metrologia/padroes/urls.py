"""URL routing M5 padroes (T-PAD-042).

PadraoViewSet registrado via DefaultRouter (`padroes`). Actions custom usam
url_path proprio. Plugado em config/urls.py raiz (licao T-CAL-124 — nao deixar
orfa).
"""

from rest_framework.routers import DefaultRouter

from .views import PadraoViewSet

router = DefaultRouter()
router.register("padroes", PadraoViewSet, basename="padrao")

urlpatterns = [
    *router.urls,
]
