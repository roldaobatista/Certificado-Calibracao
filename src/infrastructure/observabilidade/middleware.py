"""CorrelationIdMiddleware (F-C2) — correlation_id por request.

PRIMEIRO middleware da cadeia (antes de auth/tenant): garante que TODO request —
inclusive publico, 401 e 403 — tenha um correlation_id no contexto, injetado em
todos os logs (OBS-002) e devolvido no header `X-Correlation-ID` pro cliente
correlacionar. Reusa um `X-Correlation-ID`/`X-Request-ID` de entrada SE for um
valor seguro (anti log-injection); senao gera um novo.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from src.infrastructure.multitenant.context import correlation_id_context

HEADER_CORRELATION_ID = "X-Correlation-ID"

# Aceita so token seguro (hex/uuid/slug curto) vindo do cliente — evita injecao
# de conteudo arbitrario (newline, aspas) na linha de log estruturado.
_TOKEN_SEGURO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def _correlation_id_do_request(request: HttpRequest) -> str:
    recebido = (
        request.headers.get(HEADER_CORRELATION_ID)
        or request.headers.get("X-Request-ID")
        or ""
    ).strip()
    if recebido and _TOKEN_SEGURO.match(recebido):
        return recebido
    return uuid4().hex


class CorrelationIdMiddleware:
    """Seta `correlation_id_context` no inicio do request e reseta no fim.

    Token+reset (PEP 567) — leak-safe em pool de threads/async, mesmo padrao
    do TenantMiddleware.
    """

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = _correlation_id_do_request(request)
        token = correlation_id_context.set(correlation_id)
        try:
            response = self.get_response(request)
            response[HEADER_CORRELATION_ID] = correlation_id
            return response
        finally:
            correlation_id_context.reset(token)
