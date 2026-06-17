"""URLconf da frente agenda (Fatia 2 — T-AGE-031..038)."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from src.infrastructure.agenda.views import AgendaViewSet

router = DefaultRouter()
router.register(r"agenda", AgendaViewSet, basename="agenda")

urlpatterns = router.urls
