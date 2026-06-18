"""Regra de negócio pura: cálculo do saldo do caixa do técnico (T-CT-013).

D-CT-2 / INV-CT-SALDO-001:
    saldo_final = Σ adiantamentos ENTREGUES - Σ despesas VALIDADAS

Direção derivada automaticamente (AC T-CT-013):
    calcular_saldo([adiant_500], [despesa_300]) → saldo=200, direcao=tenant_deve

Função PURA — determinística, sem I/O, sem Django.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.shared.value_objects import Dinheiro

from ..enums import EstadoAdiantamento, EstadoDespesa
from ..value_objects import ResultadoSaldo

if TYPE_CHECKING:
    from ..entities import Adiantamento, Despesa


def calcular_saldo(
    adiantamentos: list[Adiantamento],
    despesas: list[Despesa],
) -> ResultadoSaldo:
    """Calcula o saldo do caixa do técnico para o conjunto de operações dado.

    Soma apenas:
      - Adiantamentos com ``estado == EntregUE`` (entregues ao técnico).
      - Despesas com ``estado == VALIDADA`` (aprovadas pelo financeiro).

    Derivação de direção (D-CT-8):
      saldo > 0  → tenant_deve  (tenant deve reembolsar — estado consultável Wave A)
      saldo < 0  → tecnico_deve (técnico deve devolver — execução Wave B)
      saldo == 0 → quitado

    Args:
        adiantamentos: lista de objetos ``Adiantamento`` (domínio puro).
        despesas:      lista de objetos ``Despesa`` (domínio puro).

    Returns:
        ``ResultadoSaldo`` com total_adiantado, total_despesas, saldo_final e direcao.
    """
    zero = Dinheiro(0)

    total_adiantado = zero
    for adian in adiantamentos:
        if adian.estado == EstadoAdiantamento.ENTREGUE:
            total_adiantado = total_adiantado + adian.valor

    total_despesas = zero
    for despesa in despesas:
        if despesa.estado == EstadoDespesa.VALIDADA:
            total_despesas = total_despesas + despesa.valor

    return ResultadoSaldo.calcular(total_adiantado, total_despesas)
