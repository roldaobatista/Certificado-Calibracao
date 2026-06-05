"""Observabilidade (F-C2) — logs estruturados, correlation_id, health/ready, metricas.

Stack decidida em AGENTS.md §2 (structlog + Grafana Cloud + Axiom). Este pacote
liga os pilares no codigo:
  - `contexto_log.py` — processor structlog que injeta correlation_id/tenant_id/
    usuario_id em TODO log (fecha OBS-002 na raiz, sem `extra=` manual).
  - `logging_config.py` — configura structlog + monta o dict LOGGING do Django
    (JSON em prod/test, console legivel em dev) reusando os loggers stdlib ja
    espalhados (integracao via `structlog.stdlib.ProcessorFormatter`).
  - `middleware.py` — `CorrelationIdMiddleware` (1o da cadeia) gera/propaga o
    correlation_id por request + devolve no header `X-Correlation-ID`.
"""
