"""URL routing M4 P4 Fase 8 (T-CAL-135)."""

from rest_framework.routers import DefaultRouter

from .views import CalibracaoViewSet

router = DefaultRouter()
router.register("calibracoes", CalibracaoViewSet, basename="calibracao")

urlpatterns = [
    *router.urls,
]
