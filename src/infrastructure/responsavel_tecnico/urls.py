"""URL routing US-EQP-007 — Responsavel Tecnico."""

from rest_framework.routers import DefaultRouter

from .views import ResponsavelTecnicoViewSet

router = DefaultRouter()
router.register(
    "responsaveis-tecnicos",
    ResponsavelTecnicoViewSet,
    basename="responsavel-tecnico",
)

urlpatterns = router.urls
