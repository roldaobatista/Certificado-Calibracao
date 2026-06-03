"""URL routing M9 licencas-acreditacoes (T-LIC-044).

`DocumentoRegulatorioViewSet` via DefaultRouter (`licencas`). Plugado em
config/urls.py raiz (lição T-CAL-124 — não deixar órfã). Diferente do M8, este
módulo É um app Django (migrations próprias em `migrations/`).
"""

from rest_framework.routers import DefaultRouter

from .views import DocumentoRegulatorioViewSet

router = DefaultRouter()
router.register("licencas", DocumentoRegulatorioViewSet, basename="licenca")

urlpatterns = [
    *router.urls,
]
