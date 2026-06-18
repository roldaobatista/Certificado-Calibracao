"""Máquina de estados do adiantamento do caixa_tecnico (Fatia 1a — T-CT-014).

D-CT-7 (máquina de estados adiantamento):
    solicitado → aprovado | recusado | cancelado
    aprovado   → entregue
    entregue   → (terminal — AdiantamentoNaoCancelavel se tentativa de cancelar)
    recusado   → (terminal)
    cancelado  → (terminal)

Tentativa de mover ``entregue`` para qualquer estado levanta
``AdiantamentoNaoCancelavel`` (422) — não ``TransicaoInvalida`` (AC T-CT-014).

Funções PURAS — sem I/O, sem Django.

Refs: D-CT-7; INV-CT-ADIAN-001; AC-CT-007-2.
"""

from __future__ import annotations

from collections.abc import Mapping

from .enums import EstadoAdiantamento
from .erros import AdiantamentoNaoCancelavel, TransicaoInvalida

# Transições válidas: estado atual → conjunto de destinos permitidos.
_TRANSICOES: Mapping[EstadoAdiantamento, frozenset[EstadoAdiantamento]] = {
    EstadoAdiantamento.SOLICITADO: frozenset(
        {
            EstadoAdiantamento.APROVADO,
            EstadoAdiantamento.RECUSADO,
            EstadoAdiantamento.CANCELADO,
        }
    ),
    EstadoAdiantamento.APROVADO: frozenset(
        {
            EstadoAdiantamento.ENTREGUE,
        }
    ),
    EstadoAdiantamento.ENTREGUE: frozenset(),  # terminal — AdiantamentoNaoCancelavel
    EstadoAdiantamento.RECUSADO: frozenset(),  # terminal
    EstadoAdiantamento.CANCELADO: frozenset(),  # terminal
}


def validar_transicao(de: EstadoAdiantamento, para: EstadoAdiantamento) -> None:
    """Levanta erro apropriado se ``de → para`` não é permitida (D-CT-7).

    ``entregue`` é terminal especial: levanta ``AdiantamentoNaoCancelavel`` (422)
    em vez de ``TransicaoInvalida`` — sinaliza semântica de negócio distinta
    (adiantamento entregue não cancela; acerto via prestação ou devolução Wave B).

    Args:
        de:   estado atual do adiantamento.
        para: estado de destino pretendido.

    Raises:
        AdiantamentoNaoCancelavel: se ``de == entregue`` (terminal especial).
        TransicaoInvalida: se a transição não é permitida pela máquina.
    """
    # Terminal especial: entregue levanta erro semântico específico (AC T-CT-014)
    if de == EstadoAdiantamento.ENTREGUE:
        raise AdiantamentoNaoCancelavel(
            f"adiantamento entregue não pode ser cancelado: {de.value!r} → {para.value!r}. "
            f"Acerto via prestação de contas ou devolução (Wave B — GATE-CT-DEVOLUCAO-EXEC)"
        )

    destinos = _TRANSICOES.get(de, frozenset())
    if para not in destinos:
        raise TransicaoInvalida(
            f"transição de adiantamento proibida: {de.value!r} → {para.value!r} "
            f"(destinos válidos: {sorted(e.value for e in destinos) or 'nenhum — estado terminal'})"
        )


def eh_terminal(estado: EstadoAdiantamento) -> bool:
    """Retorna ``True`` se o estado é terminal (sem saídas permitidas)."""
    return not _TRANSICOES.get(estado, frozenset())
