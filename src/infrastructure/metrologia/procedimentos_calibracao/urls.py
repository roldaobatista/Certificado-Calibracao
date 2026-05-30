"""URL routing M7 procedimentos-calibracao (T-PROC-037).

ProcedimentoCalibracaoViewSet via DefaultRouter (`procedimentos-calibracao`).
Plugado em config/urls.py raiz (lição T-CAL-124 — não deixar órfã).
"""

from rest_framework.routers import DefaultRouter

from .views import ProcedimentoCalibracaoViewSet

router = DefaultRouter()
router.register(
    "procedimentos-calibracao",
    ProcedimentoCalibracaoViewSet,
    basename="procedimento-calibracao",
)

urlpatterns = [
    *router.urls,
]
