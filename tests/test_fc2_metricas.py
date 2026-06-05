"""F-C2 Fatia D — métricas Prometheus (/metrics) + instrumentação HTTP.

- /metrics responde 200 no formato Prometheus com os contadores do Aferê;
- um request instrumentado (/livez) incrementa o contador com label `view`;
- /metrics NÃO se auto-instrumenta (path ignorado — evita ruído de self-scrape);
- `classe_status` reduz status code à faixa (baixa cardinalidade).
"""

from __future__ import annotations

from django.test import Client
from src.infrastructure.observabilidade.metricas import classe_status

_PROM_NS = "afere_http_requests_total"


def test_classe_status_reduz_para_faixa():
    assert classe_status(200) == "2xx"
    assert classe_status(404) == "4xx"
    assert classe_status(503) == "5xx"
    assert classe_status(301) == "3xx"


def test_metrics_endpoint_200_formato_prometheus():
    r = Client().get("/metrics")
    assert r.status_code == 200, r.content
    assert r["Content-Type"].startswith("text/plain")
    corpo = r.content.decode()
    assert _PROM_NS in corpo
    assert "afere_http_request_duration_seconds" in corpo


def test_request_instrumentado_incrementa_contador_com_view():
    # bate num endpoint instrumentado (livez) e confere a série no /metrics
    Client().get("/livez/")
    corpo = Client().get("/metrics").content.decode()
    # serie do livez presente com label view (baixa cardinalidade)
    assert 'view="livez"' in corpo
    assert _PROM_NS in corpo


def test_metrics_nao_se_autoinstrumenta():
    # /metrics e path ignorado pelo middleware -> nao cria serie view="metrics"
    Client().get("/metrics")
    corpo = Client().get("/metrics").content.decode()
    assert 'view="metrics"' not in corpo
