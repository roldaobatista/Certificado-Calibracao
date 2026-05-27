"""Motor de regras Western Electric — P-CAL-R8 RBC + cl. 7.7.1.

4 regras classicas de deteccao de desvio sistematico em grafico de
controle X/R (Shewhart). Aplicadas sobre serie temporal de medicoes
de controle do mesmo padrao+grandeza, em ordem cronologica crescente
(antiga -> nova).

RULE_1_3SIGMA:
  1 ponto fora de +-3 sigma do centro (z_score > 3 ou < -3).
  Sinal mais forte — defeito grave / fora-de-controle imediato.

RULE_2_SEVEN_SAME_SIDE:
  7 pontos consecutivos do MESMO lado da media (todos > 0 OU todos < 0
  do desvio centrado).
  Indica deriva sistematica do padrao ou da medida.

RULE_3_TREND:
  6+ pontos consecutivos em tendencia monotonica (crescente OU
  decrescente). Sinal de degradacao gradual.

RULE_5_TWO_OF_THREE:
  2 de 3 pontos consecutivos > +2 sigma (ou < -2 sigma) do mesmo lado.
  Sinal antecipado — alerta antes da regra 1 disparar.

Ordem de avaliacao (mais grave primeiro):
  1. RULE_1_3SIGMA
  2. RULE_5_TWO_OF_THREE
  3. RULE_2_SEVEN_SAME_SIDE
  4. RULE_3_TREND

Funcao pura — recebe sequencia de medicoes (escore_z ou desvio
normalizado) e retorna primeiro nome de regra violada (str em
REGRAS_WESTERN_ELECTRIC_ACEITAS) ou None.

Determinismo bit-a-bit (Decimal puro) — INV-CAL-INC-001.
"""

from __future__ import annotations

from decimal import Decimal

# Limites em sigmas (z-score)
_LIMITE_3SIGMA = Decimal("3.0")
_LIMITE_2SIGMA = Decimal("2.0")

# Numero minimo de pontos consecutivos para cada regra
_N_RULE_2 = 7
_N_RULE_3 = 6


def avaliar_regras_we(escores_z: list[Decimal]) -> str | None:
    """Avalia 4 regras Western Electric sobre serie temporal cronologica.

    Args:
      escores_z: lista de z-scores em ordem crescente de timestamp
        (antiga -> nova). Cada Decimal.

    Returns:
      Nome da primeira regra violada (str na whitelist) ou None se
      todas pasaram.

    Levanta:
      TypeError se algum elemento nao for Decimal.
    """
    if not escores_z:
        return None
    for i, z in enumerate(escores_z):
        if not isinstance(z, Decimal):
            raise TypeError(
                f"avaliar_regras_we: escore_z[{i}] deve ser Decimal "
                f"(achou {type(z).__name__}) — INV-CAL-INC-001"
            )

    # Ordem: mais grave primeiro (cada return interrompe avaliacao).

    # RULE_1_3SIGMA — ultima medicao fora de +-3 sigma
    # (Tipicamente o foco eh a medicao MAIS RECENTE — caller invoca
    # apos INSERT da nova medicao. Mas tambem aceitamos violacao em
    # qualquer ponto da janela.)
    for z in escores_z:
        if abs(z) > _LIMITE_3SIGMA:
            return "RULE_1_3SIGMA"

    # RULE_5_TWO_OF_THREE — entre as ultimas 3, 2+ violam +2 sigma (mesmo lado)
    if len(escores_z) >= 3:
        ultimos_3 = escores_z[-3:]
        positivos = sum(1 for z in ultimos_3 if z > _LIMITE_2SIGMA)
        negativos = sum(1 for z in ultimos_3 if z < -_LIMITE_2SIGMA)
        if positivos >= 2 or negativos >= 2:
            return "RULE_5_TWO_OF_THREE"

    # RULE_2_SEVEN_SAME_SIDE — ultimas 7+ medicoes todas do mesmo lado da media
    if len(escores_z) >= _N_RULE_2:
        ultimos_7 = escores_z[-_N_RULE_2:]
        if all(z > Decimal("0") for z in ultimos_7):
            return "RULE_2_SEVEN_SAME_SIDE"
        if all(z < Decimal("0") for z in ultimos_7):
            return "RULE_2_SEVEN_SAME_SIDE"

    # RULE_3_TREND — ultimas 6+ medicoes em tendencia monotonica estrita
    if len(escores_z) >= _N_RULE_3:
        ultimos_6 = escores_z[-_N_RULE_3:]
        crescente = all(
            ultimos_6[i] < ultimos_6[i + 1] for i in range(len(ultimos_6) - 1)
        )
        decrescente = all(
            ultimos_6[i] > ultimos_6[i + 1] for i in range(len(ultimos_6) - 1)
        )
        if crescente or decrescente:
            return "RULE_3_TREND"

    return None
