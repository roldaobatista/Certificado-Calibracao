"""URL routing Marco 2 — Equipamentos."""

from rest_framework.routers import DefaultRouter

from .views import EquipamentoViewSet

router = DefaultRouter()
router.register("equipamentos", EquipamentoViewSet, basename="equipamento")

urlpatterns = router.urls
