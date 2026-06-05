"""Processor structlog que injeta o contexto do request em TODO log (F-C2).

Fecha OBS-002 na RAIZ: em vez de cada `logger.info(..., extra={"tenant_id":...,
"correlation_id":...})` (manual, esquecivel — 42 call-sites sem isso), o
processor le os ContextVars do request e preenche os campos que faltam. Logs
que JA passam o campo no `extra=` vencem (nao sobrescreve).

Import dos ContextVars e LAZY (dentro da funcao): este modulo e referenciado
pelo dict LOGGING montado no carregamento do settings, ANTES dos apps subirem —
importar `multitenant.context` no topo arriscaria ciclo.
"""

from __future__ import annotations

from typing import Any


def injetar_contexto_observabilidade(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """structlog processor: adiciona correlation_id/tenant_id/usuario_id.

    Assinatura padrao de processor structlog `(logger, method_name, event_dict)`.
    Idempotente e nao-sobrescreve: se o call-site ja mandou o campo via `extra=`,
    o valor dele e preservado.
    """
    from src.infrastructure.multitenant.context import (
        active_tenant_context,
        correlation_id_context,
        usuario_id_context,
    )

    correlation_id = correlation_id_context.get()
    if correlation_id and "correlation_id" not in event_dict:
        event_dict["correlation_id"] = correlation_id

    tenant_id = active_tenant_context.get()
    if tenant_id is not None and "tenant_id" not in event_dict:
        event_dict["tenant_id"] = str(tenant_id)

    usuario_id = usuario_id_context.get()
    if usuario_id is not None and "usuario_id" not in event_dict:
        event_dict["usuario_id"] = str(usuario_id)

    return event_dict
