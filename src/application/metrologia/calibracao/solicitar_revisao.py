"""Use case `solicitar_revisao` — US-CAL-007 (P4 Fase 5 Batch F — T-CAL-087).

Transicao EM_EXECUCAO -> EM_REVISAO_1. Cravada ANTES de US-CAL-007 efetiva
(aprovar/rejeitar) — quando o metrologista termina o trabalho de bancada
e envia pra revisao tecnica.

Concorrencia (ADR-0065 + INV-CAL-CONC-003): CAS via
repo.atualizar_com_lock(snapshot, revision_anterior). Race perdida ->
ConflitoVersaoCalibracao com snapshot atual.

Permissao caller: AuthorizationProvider.can('calibracao.solicitar_revisao',
resource={tenant_id, calibracao_id}) ANTES de invocar este use case. Use
case nao re-chama provider.

Invariantes:
- INV-CAL-WORM-001: so transita de EM_EXECUCAO; outros estados -> 412.
- Use case nao captura snapshot_competencia (isso eh em aprovar_revisao
  US-CAL-007). Aqui apenas marca "trabalho de bancada terminado".
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


class EstadoInvalidoParaSolicitarRevisao(Exception):
    """Calibracao nao esta em EM_EXECUCAO — caller retorna 409 Conflict."""


@dataclass(frozen=True, slots=True)
class SolicitarRevisaoInput:
    calibracao_id: UUID
    revision_esperada: int


@dataclass(frozen=True, slots=True)
class SolicitarRevisaoOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: SolicitarRevisaoInput,
    repo: CalibracaoRepository,
) -> SolicitarRevisaoOutput:
    """Solicita revisao: EM_EXECUCAO -> EM_REVISAO_1 via CAS."""
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.EM_EXECUCAO:
        raise EstadoInvalidoParaSolicitarRevisao(
            f"status atual={atual.status.value}; solicitar_revisao exige "
            f"EM_EXECUCAO (INV-CAL-WORM-001)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.EM_REVISAO_1,
        revision=atual.revision + 1,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return SolicitarRevisaoOutput(snapshot=novo)
