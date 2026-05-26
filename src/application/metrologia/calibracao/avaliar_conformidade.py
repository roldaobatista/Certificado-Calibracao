"""Use case `avaliar_conformidade` — US-CAL-006 (P4 Fase 5 Batch G — T-CAL-086).

Aplica regra de decisao ISO 17025 cl. 7.8.6 + ADR-0024 revisado + ILAC G8:2019 §4
para classificar a calibracao em 1 das 7 zonas (6 ILAC G8 + NA) e calcular
PFA/PRA conforme regra acordada.

ACs cobertos:
- AC-CAL-006-1 (MODIFICADO P3): GIVEN OrcamentoIncerteza cravado, WHEN
  avaliarConformidade, THEN sistema calcula zona_ilac_g8 em uma das 7
  zonas + popula decisao correspondente.
- AC-CAL-006-2: GIVEN zona ZONA DE INCERTEZA (CONDITIONAL_*), WHEN sistema
  mostra, THEN exige decisao explicita do metrologista (escopo: caller
  apresenta UI; este use case so classifica).
- AC-CAL-006-3: GIVEN regra de decisao escolhida, WHEN certificado emitido,
  THEN regra fica documentada (escopo emissao certificado M5; aqui so
  preservamos `regra_decisao` no snapshot — ja vem cravada da
  configurar_calibracao US-CAL-002).
- AC-CAL-006-4 (P3): GIVEN regra_decisao=BANDA_GUARDA_30, exige
  pfa_calculada NOT NULL; GIVEN regra_decisao=RISCO_COMPARTILHADO, exige
  pra_calculada NOT NULL; ausente -> 412 PFANaoCalculada / PRANaoCalculada.
  (Este use case CALCULA — se nao calculou eh bug; teste regressao).

Estados permitidos: EM_EXECUCAO + EM_REVISAO_1. Multiplas chamadas sao
aceitas (re-avaliar apos corrigir leitura) — cada chamada incrementa
revision via CAS.

INV-CAL-DEC-004: PFA NOT NULL quando regra=BANDA_GUARDA_30 + PRA NOT NULL
quando regra=RISCO_COMPARTILHADO.
INV-CAL-DEC-005: zona_ilac_g8 NOT NULL (CHECK constraint PG).

Decisao high-level (campo `decisao`):
  ZonaILACG8.aprova -> "CONFORME"
  ZonaILACG8.reprova -> "NAO_CONFORME"
  ZonaILACG8.NA -> "NA"

Permissao caller: AuthorizationProvider.can('calibracao.avaliar_conformidade',
resource={tenant_id, calibracao_id}).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import UUID

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConflitoVersaoCalibracao,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao, RegraDecisao
from src.domain.metrologia.calibracao.motor_calculo.decisao_ilac import (
    EntradaAvaliacao,
    classificar_zona_ilac_g8,
)
from src.domain.metrologia.calibracao.motor_calculo.pfa_pra import (
    K_PADRAO,
    ParametrosPFAPRA,
    calcular_pfa,
    calcular_pra,
)
from src.domain.metrologia.calibracao.repository import CalibracaoRepository
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8

_ESTADOS_PERMITIDOS: frozenset[EstadoCalibracao] = frozenset({
    EstadoCalibracao.EM_EXECUCAO,
    EstadoCalibracao.EM_REVISAO_1,
})


class CalibracaoEstadoNaoPermiteAvaliar(Exception):
    """Calibracao em estado que nao permite avaliacao."""


@dataclass(frozen=True, slots=True)
class AvaliarConformidadeInput:
    """Payload para avaliar conformidade (ILAC G8 + ADR-0024)."""

    calibracao_id: UUID
    revision_esperada: int
    valor_medido: Decimal  # mensurando (Decimal puro)
    U_expandida: Decimal  # incerteza expandida do orcamento - INV-CAL-INC-001
    k: Decimal  # fator de cobertura (default 2.0)
    lsl: Decimal | None  # Lower Specification Limit (None => sem limite inferior)
    usl: Decimal | None  # Upper Specification Limit (None => sem limite superior)

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
                f"U_expandida deve ser >= 0 (achou {self.U_expandida})"
            )
        if self.k <= 0:
            raise ValueError(f"k deve ser > 0 (achou {self.k})")


@dataclass(frozen=True, slots=True)
class AvaliarConformidadeOutput:
    snapshot: CalibracaoSnapshot
    zona: ZonaILACG8
    pfa: Decimal | None
    pra: Decimal | None


def _derivar_decisao(zona: ZonaILACG8) -> str:
    """Reduz zona ILAC G8 (7) para 3 valores high-level de `decisao`."""
    if zona.aprova:
        return "CONFORME"
    if zona.reprova:
        return "NAO_CONFORME"
    return "NA"


def executar(
    inp: AvaliarConformidadeInput,
    repo: CalibracaoRepository,
) -> AvaliarConformidadeOutput:
    """Classifica zona ILAC G8 + calcula PFA/PRA + persiste no snapshot."""
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status not in _ESTADOS_PERMITIDOS:
        raise CalibracaoEstadoNaoPermiteAvaliar(
            f"status atual={atual.status.value}; avaliar_conformidade exige "
            f"status IN {sorted(s.value for s in _ESTADOS_PERMITIDOS)}"
        )

    # Motor de decisao puro — classifica zona
    zona = classificar_zona_ilac_g8(
        EntradaAvaliacao(
            valor_medido=inp.valor_medido,
            U_expandida=inp.U_expandida,
            lsl=inp.lsl,
            usl=inp.usl,
            regra=atual.regra_decisao,
        )
    )

    # Calcula PFA/PRA conforme regra (INV-CAL-DEC-004)
    pfa: Decimal | None = None
    pra: Decimal | None = None
    if zona != ZonaILACG8.NA:
        parametros = ParametrosPFAPRA(
            valor_medido=inp.valor_medido,
            U_expandida=inp.U_expandida,
            k=inp.k if inp.k > 0 else K_PADRAO,
            lsl=inp.lsl,
            usl=inp.usl,
        )
        if atual.regra_decisao == RegraDecisao.BANDA_GUARDA_30:
            pfa = calcular_pfa(parametros)
        elif atual.regra_decisao == RegraDecisao.RISCO_COMPARTILHADO:
            pra = calcular_pra(parametros)
        # ACEITACAO_SIMPLES: pfa/pra opcionais (nao exigidos por INV-CAL-DEC-004)

    decisao = _derivar_decisao(zona)

    novo = replace(
        atual,
        revision=atual.revision + 1,
        zona_ilac_g8=zona,
        decisao=decisao,
        pfa_calculada=pfa,
        pra_calculada=pra,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return AvaliarConformidadeOutput(snapshot=novo, zona=zona, pfa=pfa, pra=pra)
