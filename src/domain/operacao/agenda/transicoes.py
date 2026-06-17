"""Máquina de estados do domínio agenda (Fatia 1a — T-AGE-013).

D-AGE-3 (Padrão A — máquina de estados):
    agendado    → em_execucao | cancelado | no_show
    em_execucao → concluido | cancelado
    concluido   → (terminal)
    cancelado   → (terminal)
    no_show     → (terminal)

Eventos passados imutáveis: move = update timestamps + ``EventoAuditoriaAgenda``
append-only (D-AGE-3). A transição de estado é validada ANTES de qualquer
persistência.

Funções PURAS — sem I/O, sem Django.
"""

from __future__ import annotations

from collections.abc import Mapping

from .enums import EstadoEvento
from .erros import TransicaoEventoProibida

# Transições válidas: estado atual → conjunto de destinos permitidos.
_TRANSICOES: Mapping[EstadoEvento, frozenset[EstadoEvento]] = {
    EstadoEvento.AGENDADO: frozenset(
        {
            EstadoEvento.EM_EXECUCAO,
            EstadoEvento.CANCELADO,
            EstadoEvento.NO_SHOW,
        }
    ),
    EstadoEvento.EM_EXECUCAO: frozenset(
        {
            EstadoEvento.CONCLUIDO,
            EstadoEvento.CANCELADO,
        }
    ),
    EstadoEvento.CONCLUIDO: frozenset(),  # terminal
    EstadoEvento.CANCELADO: frozenset(),  # terminal
    EstadoEvento.NO_SHOW: frozenset(),  # terminal
}


def validar_transicao(de: EstadoEvento, para: EstadoEvento) -> None:
    """Levanta ``TransicaoEventoProibida`` se ``de → para`` não é permitida (D-AGE-3).

    Args:
        de:   estado atual do evento.
        para: estado de destino pretendido.

    Raises:
        TransicaoEventoProibida: se a transição não é permitida pela máquina.
    """
    destinos = _TRANSICOES.get(de, frozenset())
    if para not in destinos:
        raise TransicaoEventoProibida(
            f"transição proibida: {de.value!r} → {para.value!r} "
            f"(destinos válidos: {sorted(e.value for e in destinos) or 'nenhum — estado terminal'})"
        )


def eh_terminal(estado: EstadoEvento) -> bool:
    """Retorna ``True`` se o estado é terminal (sem saídas permitidas)."""
    return not _TRANSICOES.get(estado, frozenset())
