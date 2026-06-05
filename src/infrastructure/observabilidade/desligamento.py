"""Graceful shutdown / drain (F-C2 Fatia C).

Padrao de drain pra deploy zero-downtime: ao receber SIGTERM, o processo NAO
morre na hora — ele marca `iniciar_desligamento()`, o `/readyz` passa a
responder 503 "draining", o balanceador (K8s/LB) tira o pod do pool, e os
requests em voo terminam dentro da `--graceful-timeout` do gunicorn. So depois
o worker encerra.

O handler de SIGTERM NAO e auto-registrado (seria errado em management command/
test/migrate). O servidor (gunicorn worker / entrypoint) chama
`registrar_handler_sigterm()` explicitamente — wiring documentado em
`docs/operacao/gates-externos-pre-producao.md`. Em dev (runserver) o gunicorn
nao roda; o drain so importa em producao.
"""

from __future__ import annotations

import logging
import signal
from types import FrameType

logger = logging.getLogger(__name__)

# Flag de processo (1 worker = 1 processo). threading nao necessario: o handler
# de sinal roda na main thread e o GIL garante visibilidade da escrita simples.
_desligando = False


def esta_desligando() -> bool:
    """True apos `iniciar_desligamento()` — `/readyz` retorna 503 draining."""
    return _desligando


def iniciar_desligamento() -> None:
    """Marca o processo como drenando. Idempotente."""
    global _desligando
    if not _desligando:
        _desligando = True
        logger.info(
            "servico.drain_iniciado",
            extra={"evento": "graceful_shutdown", "fase": "draining"},
        )


def _resetar_para_teste() -> None:
    """Reset do flag — SO para testes (fixture restaura estado limpo)."""
    global _desligando
    _desligando = False


def _handler_sigterm(_signum: int, _frame: FrameType | None) -> None:
    iniciar_desligamento()


def registrar_handler_sigterm() -> None:
    """Registra o handler de SIGTERM. Chamado SO pelo servidor (gunicorn),
    nunca em import de settings/app — ver docstring do modulo."""
    signal.signal(signal.SIGTERM, _handler_sigterm)
    logger.info("servico.sigterm_handler_registrado")
