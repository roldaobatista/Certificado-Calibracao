"""URLs do módulo colaboradores — Fatia 2 REST (T-COL-035).

Router DRF para ColaboradorViewSet com ações extra:
  POST/DELETE  /colaboradores/{id}/papeis/
  POST/DELETE  /colaboradores/{id}/habilidades/
  POST         /colaboradores/{id}/documentos/
  GET          /colaboradores/{id}/auditoria/
  GET          /colaboradores/elegiveis/
  GET          /colaboradores/{id}/comissao-vigente/
"""

from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from src.infrastructure.colaboradores.views import ColaboradorViewSet

router = DefaultRouter()
router.register(r"colaboradores", ColaboradorViewSet, basename="colaborador")

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include(router.urls)),
]
