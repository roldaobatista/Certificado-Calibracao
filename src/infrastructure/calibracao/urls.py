"""URL routing M4 P4 Fase 8 (T-CAL-123..135).

Registros:
  - calibracoes (CalibracaoViewSet) — recepcionar/configurar/cancelar (T-CAL-123)
  - LeituraViewSet (T-CAL-124) — registrar-leitura + corrigir
    Como ambas actions sao detail=False com url_path absoluto
    (`calibracoes/{pk}/registrar-leitura` e `leituras/{pk}/corrigir`),
    nao usamos DefaultRouter pra LeituraViewSet — mapeamos cada action
    direto via as_view.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CalibracaoViewSet, LeituraViewSet

router = DefaultRouter()
router.register("calibracoes", CalibracaoViewSet, basename="calibracao")

urlpatterns = [
    *router.urls,
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
]
