"""Use case `rejeitar_revisao` — US-CAL-007 (P4 Fase 5 Batch F — T-CAL-089).

Transicao EM_REVISAO_1 -> EM_EXECUCAO. RT identifica problema na revisao
e devolve pro metrologista corrigir (AC-CAL-007-2 PRD).

NAO marca revisor_id (rejeicao nao eh aprovacao — nao queima o RT
no slot revisor_id ate ele aprovar de fato). Snapshot competencia
revisor permanece None — sera capturado quando aprovar_revisao
finalmente acontecer.

Nota tecnica + motivo canonicalizado obrigatorios (cl. 7.8 + INV-DOC-CANON-001
+ anti-PII INV-CAL-TXT-001). Caller responsavel pela canonicalizacao.

Permissao caller: AuthorizationProvider.can('calibracao.rejeitar_revisao',
resource={tenant_id, calibracao_id}).

Invariantes:
- INV-CAL-WORM-001: so transita de EM_REVISAO_1.
- Motivo >= 30 chars (anti-PII + suficiente pra rastreio CGCRE 25a).
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

_MIN_CHARS_MOTIVO = 30


class EstadoInvalidoParaRejeitarRevisao(Exception):
    """Calibracao nao esta em EM_REVISAO_1 — caller retorna 409 Conflict."""


@dataclass(frozen=True, slots=True)
class RejeitarRevisaoInput:
    """Payload de rejeicao de revisao."""

    calibracao_id: UUID
    revision_esperada: int
    motivo_rejeicao_canonicalizado: str  # >=30 chars + NFC + anti-PII

    def __post_init__(self) -> None:
        if len(self.motivo_rejeicao_canonicalizado) < _MIN_CHARS_MOTIVO:
            raise ValueError(
                f"rejeitar_revisao: motivo_rejeicao_canonicalizado precisa "
                f">= {_MIN_CHARS_MOTIVO} chars (INV-DOC-CANON-001 + anti-PII); "
                f"achou {len(self.motivo_rejeicao_canonicalizado)}"
            )


@dataclass(frozen=True, slots=True)
class RejeitarRevisaoOutput:
    snapshot: CalibracaoSnapshot
    motivo: str  # echo do motivo registrado (caller persiste em EventoDeCalibracao)


def executar(
    inp: RejeitarRevisaoInput,
    repo: CalibracaoRepository,
) -> RejeitarRevisaoOutput:
    """Rejeita revisao: EM_REVISAO_1 -> EM_EXECUCAO via CAS.

    O motivo nao vai no snapshot (campo nao existe na entidade) — caller
    persiste como `EventoDeCalibracao(tipo='revisao_rejeitada', motivo=...)`
    em transacao envolvente (entidade EventoDeCalibracao ja existe — Fase 1
    T-CAL-011).
    """
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.EM_REVISAO_1:
        raise EstadoInvalidoParaRejeitarRevisao(
            f"status atual={atual.status.value}; rejeitar_revisao exige "
            f"EM_REVISAO_1 (INV-CAL-WORM-001)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.EM_EXECUCAO,
        revision=atual.revision + 1,
        # NAO grava revisor_id — rejeicao nao "queima" o slot.
        # snapshot_competencia_revisor_json continua None.
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return RejeitarRevisaoOutput(
        snapshot=novo, motivo=inp.motivo_rejeicao_canonicalizado
    )
