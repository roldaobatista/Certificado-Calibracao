"""Use case `iniciar_leituras` — US-CAL-004 (P4 Fase 5 Batch C — T-CAL-084).

Transicao CONFIGURADA -> EM_EXECUCAO via CAS. Use case PURO — nao
registra leituras (isso eh `registrar_leitura`); apenas avanca o estado
para que leituras possam ser registradas.

Caller (view) chama AuthorizationProvider.can('calibracao.iniciar_leituras',
resource={tenant_id, grandeza, ...}) ANTES de invocar. Predicate
cmc_cobre ja registrado (Fase 4) — re-valida CMC vigente na data de
inicio (por seguranca, mesmo que tenha rodado em configurar).

Levanta:
  CalibracaoNaoEncontrada — id nao existe.
  EstadoInvalidoParaIniciarLeituras — status != CONFIGURADA.
  ConflitoVersaoCalibracao — CAS perdeu race.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConflitoVersaoCalibracao,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import CalibracaoRepository


class EstadoInvalidoParaIniciarLeituras(Exception):
    """Calibracao nao esta em CONFIGURADA — caller retorna 409 Conflict."""


@dataclass(frozen=True, slots=True)
class IniciarLeiturasInput:
    calibracao_id: UUID
    revision_esperada: int  # CAS


@dataclass(frozen=True, slots=True)
class IniciarLeiturasOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: IniciarLeiturasInput,
    repo: CalibracaoRepository,
) -> IniciarLeiturasOutput:
    """Avanca status: CONFIGURADA -> EM_EXECUCAO via CAS."""
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.CONFIGURADA:
        raise EstadoInvalidoParaIniciarLeituras(
            f"status atual={atual.status.value}; iniciar_leituras exige "
            f"CONFIGURADA (INV-CAL-WORM-001)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.EM_EXECUCAO,
        revision=atual.revision + 1,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return IniciarLeiturasOutput(snapshot=novo)
