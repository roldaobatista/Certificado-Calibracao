"""Máquina de estados da despesa do caixa_tecnico (Fatia 1a — T-CT-014).

D-CT-3 (máquina de estados despesa):
    pendente  → validada | rejeitada | cancelada
    rejeitada → pendente  (reapresentação — US-CT-007 / R3)
    validada  → (terminal — imutável WORM)
    cancelada → (terminal)

Trigger PG ``caixa_tecnico_despesa_anti_mutacao`` bloqueia UPDATE/DELETE quando
``OLD.status = 'validada'``. A reapresentação ``rejeitada→pendente`` NÃO dispara
o trigger — é UPDATE legítimo (R3 / teste obrigatório TL-CT-05).

Funções PURAS — sem I/O, sem Django.

Refs: D-CT-3; INV-CT-IMUT-001; AC-CT-007-2.
"""

from __future__ import annotations

from collections.abc import Mapping

from .enums import EstadoDespesa
from .erros import TransicaoInvalida

# Transições válidas: estado atual → conjunto de destinos permitidos.
_TRANSICOES: Mapping[EstadoDespesa, frozenset[EstadoDespesa]] = {
    EstadoDespesa.PENDENTE: frozenset(
        {
            EstadoDespesa.VALIDADA,
            EstadoDespesa.REJEITADA,
            EstadoDespesa.CANCELADA,
        }
    ),
    EstadoDespesa.REJEITADA: frozenset(
        {
            EstadoDespesa.PENDENTE,  # reapresentação (US-CT-007)
        }
    ),
    EstadoDespesa.VALIDADA: frozenset(),  # terminal — WORM
    EstadoDespesa.CANCELADA: frozenset(),  # terminal
}


def validar_transicao(de: EstadoDespesa, para: EstadoDespesa) -> None:
    """Levanta ``TransicaoInvalida`` se ``de → para`` não é permitida (D-CT-3).

    Args:
        de:   estado atual da despesa.
        para: estado de destino pretendido.

    Raises:
        TransicaoInvalida: se a transição não é permitida pela máquina de estados.
    """
    destinos = _TRANSICOES.get(de, frozenset())
    if para not in destinos:
        raise TransicaoInvalida(
            f"transição de despesa proibida: {de.value!r} → {para.value!r} "
            f"(destinos válidos: {sorted(e.value for e in destinos) or 'nenhum — estado terminal'})"
        )


def eh_terminal(estado: EstadoDespesa) -> bool:
    """Retorna ``True`` se o estado é terminal (sem saídas permitidas)."""
    return not _TRANSICOES.get(estado, frozenset())
