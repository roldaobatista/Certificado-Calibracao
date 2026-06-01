"""URLconf raiz do projeto.

Wave A · Marco 1 acrescenta `/api/v1/clientes/` ao Foundation.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from src.infrastructure.authz.decorators import public


@public
def healthz(_request):
    """Endpoint trivial pra docker-compose validar que app esta de pe."""
    return JsonResponse({"status": "ok", "fase": "wave-a"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    # OpenAPI / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Wave A modulos
    path("api/v1/", include("src.infrastructure.clientes.urls")),
    path("api/v1/", include("src.infrastructure.equipamentos.urls")),
    path("api/v1/", include("src.infrastructure.responsavel_tecnico.urls")),
    path("api/v1/", include("src.infrastructure.ordens_servico.urls")),
    path("api/v1/", include("src.infrastructure.calibracao.urls")),
    path("api/v1/", include("src.infrastructure.metrologia.padroes.urls")),
    path("api/v1/", include("src.infrastructure.metrologia.escopos_cmc.urls")),
    path("api/v1/", include("src.infrastructure.metrologia.procedimentos_calibracao.urls")),
    path("api/v1/", include("src.infrastructure.metrologia.certificados.urls")),
]
