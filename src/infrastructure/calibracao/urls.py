"""URL routing M4 P4 Fase 8 (T-CAL-123..127 + 135).

Registros:
  - calibracoes (CalibracaoViewSet) — recepcionar/configurar/cancelar (T-CAL-123)
  - LeituraViewSet (T-CAL-124) — registrar-leitura + corrigir
  - RevisaoViewSet (T-CAL-126) — aprovar-revisao + rejeitar-revisao
  - ConferenciaViewSet (T-CAL-127) — aprovar-2a-conferencia

ViewSets de Leitura/Revisao/Conferencia usam url_path absoluto em cada
@action (calibracoes/{pk}/<acao>) — nao registrados via DefaultRouter
pra evitar prefixo extra.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CalibracaoViewSet,
    ConferenciaViewSet,
    LeituraViewSet,
    RevisaoViewSet,
)

router = DefaultRouter()
router.register("calibracoes", CalibracaoViewSet, basename="calibracao")

urlpatterns = [
    *router.urls,
    # T-CAL-124 LeituraViewSet
    path(
        "calibracoes/<str:calibracao_pk>/registrar-leitura/",
        LeituraViewSet.as_view({"post": "registrar"}),
        name="calibracao-registrar-leitura",
    ),
    path(
        "leituras/<str:leitura_pk>/corrigir/",
        LeituraViewSet.as_view({"post": "corrigir"}),
        name="leitura-corrigir",
    ),
    # T-CAL-126 RevisaoViewSet
    path(
        "calibracoes/<str:calibracao_pk>/aprovar-revisao/",
        RevisaoViewSet.as_view({"post": "aprovar"}),
        name="calibracao-aprovar-revisao",
    ),
    path(
        "calibracoes/<str:calibracao_pk>/rejeitar-revisao/",
        RevisaoViewSet.as_view({"post": "rejeitar"}),
        name="calibracao-rejeitar-revisao",
    ),
    # T-CAL-127 ConferenciaViewSet
    path(
        "calibracoes/<str:calibracao_pk>/aprovar-2a-conferencia/",
        ConferenciaViewSet.as_view({"post": "aprovar_2a"}),
        name="calibracao-aprovar-2a-conferencia",
    ),
]
