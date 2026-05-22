"""URL routing Marco 2 — Equipamentos."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EquipamentoViewSet
from .views_qr_publico import qr_publico_view

router = DefaultRouter()
router.register("equipamentos", EquipamentoViewSet, basename="equipamento")

urlpatterns = [
    # T-EQP-025+026+033 — GET /api/v1/qr/{hash}/ (3 escopos publico).
    # Hash inclui ':' (formato `qrN:<base64url>`) — regex `[^/]+` aceita.
    path("qr/<path:hash>/", qr_publico_view, name="qr-publico"),
    *router.urls,
]
