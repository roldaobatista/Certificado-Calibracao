"""Métricas Prometheus (F-C2 Fatia D) — infra do OBS-003.

Expõe `/metrics` (formato Prometheus) + instrumenta requests HTTP. Fecha a
INFRA do OBS-003 (a partir daqui há onde publicar métrica por path crítico); o
scrape pelo coletor é deploy-time (runbook gates-externos-pre-producao.md).

Cardinalidade controlada de propósito: labels = (method, view, status_class).
`view` é o NOME da rota resolvida (não o path cru — senão UUIDs explodiriam a
série). `status_class` é a faixa (2xx/4xx/5xx). tenant_id NÃO é label de métrica
HTTP (N tenants = explosão de séries); métrica de negócio por tenant é fatia
futura e usa exemplars/labels controlados.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from src.infrastructure.authz.decorators import public

REQUESTS_TOTAL = Counter(
    "afere_http_requests_total",
    "Total de requests HTTP atendidos.",
    ["method", "view", "status_class"],
)

REQUEST_DURATION = Histogram(
    "afere_http_request_duration_seconds",
    "Duração do request HTTP em segundos.",
    ["method", "view"],
)


def classe_status(status_code: int) -> str:
    """200..599 -> '2xx'/'3xx'/'4xx'/'5xx' (mantém baixa cardinalidade)."""
    return f"{status_code // 100}xx"


def render_latest() -> tuple[bytes, str]:
    """Payload do /metrics + content-type. `generate_latest` lê o registry
    default (onde os Counter/Histogram acima se registraram)."""
    return generate_latest(), CONTENT_TYPE_LATEST


_PATHS_IGNORADOS = ("/metrics",)


def _nome_view(request: HttpRequest) -> str:
    """Nome da rota resolvida (baixa cardinalidade). Sem match (404) -> 'no_match'."""
    match = getattr(request, "resolver_match", None)
    if match is not None and getattr(match, "view_name", None):
        return str(match.view_name)
    return "no_match"


class MetricasMiddleware:
    """Cronometra cada request e incrementa os contadores Prometheus.

    Posição: logo após CorrelationIdMiddleware (captura quase todo o tempo do
    request). `resolver_match` já está populado quando `get_response` retorna.
    Não instrumenta o próprio `/metrics` (evita ruído de self-scrape).
    """

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith(_PATHS_IGNORADOS):
            return self.get_response(request)
        inicio = time.perf_counter()
        response = self.get_response(request)
        duracao = time.perf_counter() - inicio
        view = _nome_view(request)
        REQUESTS_TOTAL.labels(
            method=request.method or "UNKNOWN",
            view=view,
            status_class=classe_status(response.status_code),
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method or "UNKNOWN", view=view
        ).observe(duracao)
        return response


@public
def metrics_view(_request: HttpRequest) -> HttpResponse:
    """GET /metrics — exposição Prometheus (texto). Público + bypass tenant."""
    corpo, content_type = render_latest()
    return HttpResponse(corpo, content_type=content_type)
