"""URL routing M8 certificados (T-CER-048).

`CertificadoViewSet` via DefaultRouter (`certificados`). Plugado em config/urls.py
raiz (lição T-CAL-124 — não deixar órfã). Os models/tabelas vivem no app achatado
`src.infrastructure.certificados` (ADR-0078); a camada REST/lógica é aninhada
(ADR-0072) — este módulo NÃO é um app Django (sem migrations próprias).
"""

from rest_framework.routers import DefaultRouter

from .views import CertificadoViewSet

router = DefaultRouter()
router.register("certificados", CertificadoViewSet, basename="certificado")

urlpatterns = [
    *router.urls,
]
