"""Value objects do catálogo (T-PPS-011).

`Preco` segue o molde `Aliquota` (configuracoes_sistema): Decimal com validação
no __post_init__. Escala canônica 2 casas `ROUND_HALF_EVEN` (TL-PPS-15 — fiscal
a jusante trabalha em centavos; soma de kit qtd×preço reconcilia sem deriva).
`> 0` obrigatório (TL-PPS-16 — a OS trata `valor ≤ 0` como sentinela de
`PrecoTabelaAusente`; cortesia/desconto 100% é responsabilidade da frente
`precificacao`, não do catálogo).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

_ESCALA = Decimal("0.01")


@dataclass(frozen=True)
class Preco:
    """Preço monetário em BRL, escala 2, estritamente positivo (INV-PPS-PRECO-POSITIVO)."""

    valor: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError(f"Preco.valor deve ser Decimal, veio {type(self.valor)!r}")
        normalizado = self.valor.quantize(_ESCALA, rounding=ROUND_HALF_EVEN)
        if normalizado <= 0:
            raise ValueError(
                f"Preco deve ser > 0 (veio {self.valor}) — INV-PPS-PRECO-POSITIVO "
                "(0 é sentinela de PrecoTabelaAusente na OS; cortesia é da precificacao)."
            )
        object.__setattr__(self, "valor", normalizado)

    def em_centavos(self) -> int:
        """Reconciliação exata com consumidores que trabalham em centavos (fiscal)."""
        return int(self.valor * 100)
