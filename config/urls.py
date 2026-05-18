"""URLconf raiz do projeto.

Foundation F-A: so admin + endpoint de health + OpenAPI docs.
Apps de produto plugam aqui via include() conforme entram em Wave A.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def healthz(_request):
    """Endpoint trivial pra docker-compose validar que app esta de pe."""
    return JsonResponse({"status": "ok", "fase": "foundation-f-a"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    # OpenAPI / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
