"""Motor de decisao ILAC G8:2019 §4 — 6 zonas + NA (T-CAL-086 / Batch G).

US-CAL-006 + ADR-0024 (revisado 2026-05-25 — 6 zonas) + INV-CAL-DEC-005.

Funcao PURA — Decimal puro, sem efeitos colaterais.

Inputs:
  valor_medido: Decimal — leitura corrigida do mensurando.
  U_expandida: Decimal — incerteza expandida (k=2 padrao).
  lsl: Decimal | None — Lower Specification Limit (None = sem limite inferior).
  usl: Decimal | None — Upper Specification Limit (None = sem limite superior).
  regra: RegraDecisao — ACEITACAO_SIMPLES / BANDA_GUARDA_30 / RISCO_COMPARTILHADO.

Output:
  ZonaILACG8 — uma das 7 zonas (6 + NA).

Algoritmo:
  1. Se nem LSL nem USL definidos -> NA (calibracao descritiva).
  2. ACEITACAO_SIMPLES + RISCO_COMPARTILHADO (mesma classificacao,
     diferenca eh apenas em quem assume risco do PFA/PRA):
     - valor-U >= LSL E valor+U <= USL -> PASS (totalmente dentro).
     - valor+U < LSL OU valor-U > USL -> FAIL (totalmente fora).
     - LSL <= valor <= USL (valor dentro) MAS intervalo cruza limite -> CONDITIONAL_PASS.
     - valor fora MAS intervalo cruza limite -> CONDITIONAL_FAIL.
  3. BANDA_GUARDA_30: aplica banda 30%*U aos limites:
     - LSL_eff = LSL + 0.30*U; USL_eff = USL - 0.30*U.
     - valor-U >= LSL_eff E valor+U <= USL_eff -> PASS (totalmente dentro guarda).
     - dentro [LSL, USL] mas fora banda guarda -> PASS_COM_RESSALVA.
     - fora [LSL, USL] mas dentro intervalo expandido -> FAIL_COM_RESSALVA.
     - resto idem aceitacao simples.

Referencias:
  ILAC G8:2019 §4 tabela 1 + JCGM 106:2012 §9 + NIT-DICLA-030 rev. 15.

Por que Decimal puro (nao float):
  determinismo replay 25a (ADR-0025 cl. 7.11) + INV-CAL-INC-001 (replay
  bit-a-bit). Float introduz arredondamento nao-deterministico em
  comparacoes proximas dos limites.

Por que motor PURO (sem snapshot/repo):
  use case `avaliar_conformidade` orquestra; motor decide. Testar motor
  exaustivamente em isolamento (centenas de combinacoes); use case fica
  fino — so persistencia + transicao.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.domain.metrologia.calibracao.enums import RegraDecisao
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

BANDA_GUARDA_PCT = Decimal("0.30")  # 30% — ILAC G8 + ADR-0024


@dataclass(frozen=True, slots=True)
class EntradaAvaliacao:
    """Payload imutavel de entrada do motor de decisao."""

    valor_medido: Decimal
    U_expandida: Decimal  # - U canonico
    lsl: Decimal | None
    usl: Decimal | None
    regra: RegraDecisao

    def __post_init__(self) -> None:
        if not isinstance(self.valor_medido, Decimal):
            raise TypeError(
                f"valor_medido deve ser Decimal "
                f"(achou {type(self.valor_medido).__name__}) — INV-CAL-INC-001"
            )
        if not isinstance(self.U_expandida, Decimal):
            raise TypeError(
                f"U_expandida deve ser Decimal "
                f"(achou {type(self.U_expandida).__name__}) — INV-CAL-INC-001"
            )
        if self.U_expandida < 0:
            raise ValueError(
                f"U_expandida deve ser >= 0 (achou {self.U_expandida}) — "
                f"incerteza nao pode ser negativa"
            )
        if self.lsl is not None and not isinstance(self.lsl, Decimal):
            raise TypeError("lsl deve ser Decimal ou None")
        if self.usl is not None and not isinstance(self.usl, Decimal):
            raise TypeError("usl deve ser Decimal ou None")
        # LSL > USL eh erro de configuracao (caller deve validar)
        if (
            self.lsl is not None
            and self.usl is not None
            and self.lsl > self.usl
        ):
            raise ValueError(
                f"lsl ({self.lsl}) > usl ({self.usl}) — limites invertidos"
            )


def classificar_zona_ilac_g8(entrada: EntradaAvaliacao) -> ZonaILACG8:
    """Classifica valor +- U em uma das 7 zonas ILAC G8 (6 + NA).

    Determinismo bit-a-bit garantido (Decimal puro). Replay 25 anos
    pos-emissao (ADR-0025 cl. 7.11 + INV-CAL-INC-001).
    """
    # Cl. 7.8.6 — calibracao descritiva (sem limites de especificacao)
    if entrada.lsl is None and entrada.usl is None:
        return ZonaILACG8.NA

    inferior = entrada.valor_medido - entrada.U_expandida
    superior = entrada.valor_medido + entrada.U_expandida

    # Trata limites one-sided (so LSL ou so USL)
    lsl = entrada.lsl if entrada.lsl is not None else Decimal("-Infinity")
    usl = entrada.usl if entrada.usl is not None else Decimal("Infinity")

    valor_dentro = lsl <= entrada.valor_medido <= usl
    intervalo_dentro = inferior >= lsl and superior <= usl
    intervalo_fora_total = superior < lsl or inferior > usl

    if entrada.regra == RegraDecisao.BANDA_GUARDA_30:
        guarda = BANDA_GUARDA_PCT * entrada.U_expandida
        lsl_eff = lsl + guarda if entrada.lsl is not None else lsl
        usl_eff = usl - guarda if entrada.usl is not None else usl

        intervalo_dentro_guarda = inferior >= lsl_eff and superior <= usl_eff
        if intervalo_dentro_guarda:
            return ZonaILACG8.PASS
        # Dentro dos limites estritos mas viola a banda de guarda
        if intervalo_dentro:
            return ZonaILACG8.PASS_COM_RESSALVA
        # Valor fora limites estritos + intervalo expandido toca limites
        if valor_dentro:
            return ZonaILACG8.CONDITIONAL_PASS
        if intervalo_fora_total:
            return ZonaILACG8.FAIL
        # valor fora mas intervalo cruza limite — FAIL_COM_RESSALVA
        # eh especifico de BANDA_GUARDA_30 (PFA alto exige atencao).
        return ZonaILACG8.FAIL_COM_RESSALVA

    # ACEITACAO_SIMPLES + RISCO_COMPARTILHADO (mesma classificacao geometrica;
    # a diferenca eh quem absorve o risco do PFA/PRA — ver calcular_pfa/pra)
    if intervalo_dentro:
        return ZonaILACG8.PASS
    if intervalo_fora_total:
        return ZonaILACG8.FAIL
    if valor_dentro:
        return ZonaILACG8.CONDITIONAL_PASS
    return ZonaILACG8.CONDITIONAL_FAIL
