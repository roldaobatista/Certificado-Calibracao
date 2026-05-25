"""Arredondamento metrologico NIT-DICLA-030 §7.5 (P4 Fase 3 Batch A — T-CAL-046..049).

Regra (NIT-DICLA-030 rev. 15 §7.5 + JCGM 100:2008 §7.2.6):
  Incerteza expandida U deve ser declarada com 2 algarismos significativos
  no certificado de calibracao. Algarismos significativos contam a partir
  do primeiro digito nao-zero.

Exemplos:
  0.001234 -> 0.0012 (2 sig: '1' e '2')
  0.05678  -> 0.057  (2 sig: '5' e '7'; banker's rounding eleva 6->7)
  1.234    -> 1.2
  12.345   -> 12     (2 sig: '1' e '2')
  98.765   -> 99     (banker's: 98.765 -> '99' porque 8 par, 7>5 nao se aplica)
  150      -> 150    (2 sig: '1' e '5'; trailing zero conta como ordem de magnitude)

Banker's rounding (ROUND_HALF_EVEN):
  Quando digito a arredondar = 5 sem residuo: arredonda pra par mais proximo.
  Reduz vies estatistico em populacoes grandes (BIPM JCGM 100 recomenda).

Limites:
  - Zero retorna Decimal('0.0e-2') (preservacao de 2 sig em zero exato).
  - Valores negativos suportados (preserva sinal).
  - Valores muito pequenos (e-30) e muito grandes (e+30) suportados via
    expoente decimal.

Use:
  from src.domain.metrologia.calibracao.motor_calculo.arredondamento import (
      arredondar_2_digitos_significativos,
  )
  U_arred = arredondar_2_digitos_significativos(Decimal("0.05678"))
  # U_arred == Decimal("0.057")
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

# Identificador da regra de arredondamento aplicada — vai pra
# OrcamentoIncerteza.arredondamento_aplicado_regra (§16.6 spec).
REGRA_ID: str = "NIT_DICLA_030_2_DIGITOS_SIG"

# Numero de digitos significativos (constante NIT-DICLA-030 §7.5).
DIGITOS_SIGNIFICATIVOS: int = 2


def arredondar_2_digitos_significativos(valor: Decimal) -> Decimal:
    """Arredonda valor metrologico pra 2 digitos significativos (NIT-DICLA-030 §7.5).

    Algoritmo:
      1. Se valor == 0: retorna Decimal('0E-2') (zero com escala 2 sig).
      2. Calcula expoente da ordem de magnitude: floor(log10(|valor|)).
      3. Quantiza com ROUND_HALF_EVEN preservando (DIGITOS_SIGNIFICATIVOS - 1)
         casas apos o primeiro algarismo significativo.

    Args:
      valor: Decimal (positivo, negativo ou zero). Float NAO aceito —
        introduz erro de arredondamento metrologico (INV-CAL-INC-003).

    Retorna:
      Decimal arredondado preservando sinal + ordem de magnitude.

    Levanta:
      TypeError — se valor nao for Decimal.

    Exemplos:
      >>> arredondar_2_digitos_significativos(Decimal("0.001234"))
      Decimal("0.0012")
      >>> arredondar_2_digitos_significativos(Decimal("-0.05678"))
      Decimal("-0.057")
      >>> arredondar_2_digitos_significativos(Decimal("12.345"))
      Decimal("12")
      >>> arredondar_2_digitos_significativos(Decimal("0"))
      Decimal("0E-2")
    """
    if not isinstance(valor, Decimal):
        raise TypeError(
            f"arredondar_2_digitos_significativos espera Decimal "
            f"(achou {type(valor).__name__}) — float introduz erro metrologico "
            f"(INV-CAL-INC-003)"
        )

    if valor == 0:
        # Zero exato: preserva escala de 2 algarismos significativos.
        # Sem isso, Decimal('0') geraria string ambigua na serializacao.
        return Decimal("0E-2")

    # Ordem de magnitude: expoente do primeiro algarismo significativo.
    # |valor| esta em [10^expoente_msd, 10^(expoente_msd + 1))
    valor_abs = abs(valor)
    expoente_msd = valor_abs.adjusted()  # log10(|valor|) inteiro inferior

    # Pra N digitos sig, quantizamos com expoente = expoente_msd - (N - 1)
    # Ex: 0.05678 -> expoente_msd=-2 (5 ocupa posicao 10^-2)
    #     N=2 -> quantizar com 10^-3 (1 casa apos o '5')
    #     0.05678 -> 0.057 (banker's rounding)
    #
    # ATENCAO: usamos Decimal(1).scaleb(e) e nao Decimal(10) ** e, porque
    # quantize() segue o EXPOENTE do quantizer, nao o valor. Decimal(10)**1
    # vira Decimal('10') (expoente=0), enquanto Decimal(1).scaleb(1) =
    # Decimal('1E+1') (expoente=1). Sem isso, quantize(155, Decimal('10'))
    # retorna '155' nao '1.6E+2'.
    expoente_quantize = expoente_msd - (DIGITOS_SIGNIFICATIVOS - 1)
    quantize_to = Decimal(1).scaleb(expoente_quantize)

    return valor.quantize(quantize_to, rounding=ROUND_HALF_EVEN)


def arredondar_lista(valores: list[Decimal]) -> list[Decimal]:
    """Helper: aplica arredondar_2_digitos_significativos em uma lista.

    Util para arredondar OrcamentoPorPonto[].U_expandida em batch.
    """
    return [arredondar_2_digitos_significativos(v) for v in valores]
