"""URLconf raiz do projeto.

Wave A · Marco 1 acrescenta `/api/v1/clientes/` ao Foundation.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from src.infrastructure.observabilidade.health import healthz, livez, readyz

urlpatterns = [
    path("admin/", admin.site.urls),
    # F-C2: liveness (processo de pe) vs readiness (DB+cache OK -> 503 se nao).
    path("healthz/", healthz, name="healthz"),  # legado, alias de liveness
    path("livez/", livez, name="livez"),
    path("readyz/", readyz, name="readyz"),
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
    path("api/v1/", include("src.infrastructure.metrologia.licencas_acreditacoes.urls")),
]
