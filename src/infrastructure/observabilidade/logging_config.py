"""Configuracao de logging estruturado (F-C2) — structlog + dict LOGGING Django.

Integra os ~21 modulos que ja usam `logging.getLogger(__name__)` SEM reescrever
call-site nenhum: o `structlog.stdlib.ProcessorFormatter` aplica a cadeia de
processors (timestamp ISO, nivel, nome do logger, `ExtraAdder` que captura o
`extra={}`, e `injetar_contexto_observabilidade`) sobre os LogRecord do stdlib
("foreign") e renderiza JSON (prod/test) ou console legivel (dev).

Uso em config/settings/base.py:
    from src.infrastructure.observabilidade.logging_config import configurar_logging
    LOGGING = configurar_logging(json_logs=not DEBUG)
"""

from __future__ import annotations

from typing import Any

import structlog

from src.infrastructure.observabilidade.contexto_log import (
    injetar_contexto_observabilidade,
)

# Cadeia aplicada aos LogRecord do stdlib ("foreign" — a maioria do projeto).
# Ordem: nivel + nome + timestamp -> ExtraAdder (puxa o `extra={}` do call-site)
# -> injetar_contexto (preenche correlation_id/tenant_id/usuario_id que faltam).
_FOREIGN_PRE_CHAIN: list[Any] = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.stdlib.ExtraAdder(),
    injetar_contexto_observabilidade,
]


def configurar_logging(*, json_logs: bool, nivel: str = "INFO") -> dict[str, Any]:
    """Configura structlog (global) e devolve o dict LOGGING do Django.

    `json_logs=True` -> 1 linha JSON por evento (prod/test, ingerivel por
    Grafana/Axiom). `json_logs=False` -> console legivel (dev).
    """
    # Loggers nativos structlog (codigo novo pode usar structlog.get_logger):
    # mesma cadeia, terminando em wrap_for_formatter pra cair no ProcessorFormatter.
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            injetar_contexto_observabilidade,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "estruturado": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    renderer,
                ],
                "foreign_pre_chain": _FOREIGN_PRE_CHAIN,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "estruturado",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": nivel,
        },
    }
