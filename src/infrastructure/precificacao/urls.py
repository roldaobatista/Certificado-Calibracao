"""URL routing da frente `precificacao` (Fatia 2 — T-PRC-035).

4 ViewSets:
  RegraFormacaoPrecoViewSet    → /api/v1/precificacao/regras/
  CalculoPrecoView             → /api/v1/precificacao/  (POST calcular)
  AprovacaoDescontoViewSet     → /api/v1/precificacao/aprovacoes/
  ConfiguracaoPrecificacaoViewSet → /api/v1/precificacao/config/
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from src.infrastructure.precificacao.views import (
    AprovacaoDescontoViewSet,
    CalculoPrecoView,
    ConfiguracaoPrecificacaoViewSet,
    RegraFormacaoPrecoViewSet,
)

router = DefaultRouter()
router.register(r"regras", RegraFormacaoPrecoViewSet, basename="precificacao-regras")
router.register(r"aprovacoes", AprovacaoDescontoViewSet, basename="precificacao-aprovacoes")
router.register(r"config", ConfiguracaoPrecificacaoViewSet, basename="precificacao-config")
router.register(r"", CalculoPrecoView, basename="precificacao-calculo")

urlpatterns: list[URLPattern | URLResolver] = router.urls
