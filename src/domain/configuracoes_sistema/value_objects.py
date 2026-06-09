"""Value objects do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-011).

Reusa `CNPJ` e `JanelaVigencia` de `src.domain.shared.value_objects` (anti-retrabalho).
Define só `Aliquota` (específico do catálogo tributário). Sem Django (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Aliquota:
    """Percentual de alíquota tributária (0 a 100), em pontos percentuais.

    Decimal para precisão fiscal. `valor=Decimal("18.5")` = 18,5%. INV-026: a
    alíquota usada por documento emitido é imutável (versionamento — nova linha de
    `Imposto` por vigência, nunca UPDATE).
    """

    valor: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError(f"Aliquota.valor deve ser Decimal, veio {type(self.valor)!r}")
        if self.valor < Decimal("0") or self.valor > Decimal("100"):
            raise ValueError(f"Aliquota fora de 0..100: {self.valor}")

    def fracao(self) -> Decimal:
        """Fração para multiplicar uma base (18,5% → 0.185)."""
        return self.valor / Decimal("100")

    def __str__(self) -> str:
        return f"{self.valor}%"
