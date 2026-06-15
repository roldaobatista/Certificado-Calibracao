"""Conversor único de borda: string decimal → `Dinheiro` em centavos (Fatia 1a — T-CR-014).

D-CR-23 / R9 / R-CR-NOVO-2:
  `valor_total` chega como string decimal de fatos geradores externos (ex: `os.concluida`
  enriquecido, envelope do outbox). CR opera internamente em centavos (`Dinheiro`).
  Este módulo é o ÚNICO ponto de conversão de entrada — usar aqui, não em outro lugar.

Bordas testadas (T-CR-016):
  "0.10"    → Dinheiro(10)    (dez centavos)
  "100.005" → Dinheiro(10001) (arredondamento HALF_UP)
  "0"       → Dinheiro(0)
  "0.00"    → Dinheiro(0)
  negativo  → ValueError
  vazio     → ValueError

Sem I/O, sem Django.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from src.domain.shared.value_objects import Dinheiro


def valor_decimal_str_para_dinheiro(s: str, moeda: str = "BRL") -> Dinheiro:
    """Converte string decimal (ex: "1234.56") para `Dinheiro` em centavos.

    Parâmetros:
        s     — string representando valor monetário positivo (ex: "1234.56", "0.10").
        moeda — código ISO 4217, default "BRL".

    Regras:
      - Arredondamento ROUND_HALF_UP para centavos (ex: "100.005" → 10001 centavos).
      - "0" e "0.00" → Dinheiro(0).
      - Valor negativo → ValueError.
      - String vazia ou inválida → ValueError.

    Retorna `Dinheiro(centavos, moeda)`.
    """
    if not isinstance(s, str) or not s.strip():
        raise ValueError(f"valor_decimal_str_para_dinheiro: string vazia ou inválida: {s!r}")

    try:
        dec = Decimal(s.strip())
    except InvalidOperation as exc:
        raise ValueError(
            f"valor_decimal_str_para_dinheiro: não é um número decimal válido: {s!r}"
        ) from exc

    if dec < 0:
        raise ValueError(f"valor_decimal_str_para_dinheiro: valor negativo não é permitido: {s!r}")

    # Multiplica por 100 e arredonda para int (HALF_UP — padrão contábil)
    centavos_dec = (dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return Dinheiro(int(centavos_dec), moeda)
