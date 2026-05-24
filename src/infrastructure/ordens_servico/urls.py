"""URL routing M3 OS Fase 8 (T-OS-094..104)."""

from rest_framework.routers import DefaultRouter

from .views import AtividadeViewSet, OSViewSet

router = DefaultRouter()
router.register("os", OSViewSet, basename="os")
router.register("atividades", AtividadeViewSet, basename="atividade")

urlpatterns = [
    *router.urls,
]
