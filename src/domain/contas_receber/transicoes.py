"""Máquina de estados do domínio contas-receber (Fatia 1a — T-CR-012).

D-CR-3 (máquina de estados):
    emitido            → pago | parcialmente_pago | vencido | cancelado
    vencido            → pago | parcialmente_pago | cancelado
    parcialmente_pago  → pago | vencido | cancelado
    pago               → (terminal)
    cancelado          → (terminal)

`cancelado` só sem pagamento parcial (`pode_cancelar` enforça — D-CR-3).
Funções PURAS — sem I/O, sem Django.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .entities import Pagamento, Titulo
from .enums import EstadoTitulo
from .erros import TituloComPagamentoParcial, TransicaoProibida

# Transições válidas: estado atual → conjunto de destinos permitidos.
_TRANSICOES: Mapping[EstadoTitulo, frozenset[EstadoTitulo]] = {
    EstadoTitulo.EMITIDO: frozenset(
        {
            EstadoTitulo.PAGO,
            EstadoTitulo.PARCIALMENTE_PAGO,
            EstadoTitulo.VENCIDO,
            EstadoTitulo.CANCELADO,
        }
    ),
    EstadoTitulo.VENCIDO: frozenset(
        {
            EstadoTitulo.PAGO,
            EstadoTitulo.PARCIALMENTE_PAGO,
            EstadoTitulo.CANCELADO,
        }
    ),
    EstadoTitulo.PARCIALMENTE_PAGO: frozenset(
        {
            EstadoTitulo.PAGO,
            EstadoTitulo.VENCIDO,
            EstadoTitulo.CANCELADO,
        }
    ),
    EstadoTitulo.PAGO: frozenset(),  # terminal
    EstadoTitulo.CANCELADO: frozenset(),  # terminal
}


def validar_transicao(de: EstadoTitulo, para: EstadoTitulo) -> None:
    """Levanta `TransicaoProibida` se `de → para` não é permitida (D-CR-3)."""
    destinos = _TRANSICOES.get(de, frozenset())
    if para not in destinos:
        raise TransicaoProibida(f"transição proibida: {de.value!r} → {para.value!r}")


def pode_cancelar(titulo: Titulo, pagamentos: Sequence[Pagamento]) -> bool:
    """Título só pode ser cancelado se não há pagamento parcial registrado (D-CR-3).

    Regra: `cancelado` é permitido pela máquina (via `validar_transicao`), mas
    a invariante de negócio exige que não exista nenhum `Pagamento` associado.
    Se houver qualquer pagamento, levanta `TituloComPagamentoParcial`.

    Retorna `True` se o cancelamento é permitido.
    Levanta `TituloComPagamentoParcial` se não pode cancelar.
    """
    if pagamentos:
        raise TituloComPagamentoParcial(
            f"título {titulo.titulo_id} não pode ser cancelado: "
            f"há {len(pagamentos)} pagamento(s) registrado(s)"
        )
    return True
