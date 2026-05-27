"""Use case `cancelar_calibracao` — US-CAL-007 / T-CAL-095 (PROD-CAL-03 conserto P5).

Conserto causa-raiz do achado PROD-CAL-03 da 1a passada Familia 5 (2026-05-27):
> CalibracaoViewSet.cancelar retorna 501 com mensagem expondo T-CAL-095 Wave A.
> Spec §4.1 lista `cancelada` como transicao valida; bloqueio operacional pra
> dogfooding (recepcionou errado -> nao consegue cancelar).

Transicao §4.1 spec: qualquer estado nao-terminal -> CANCELADA, mediante
motivo canonicalizado >=30 chars (anti-PII) cujo HashVersionado fica em
`motivo_cancelamento_hash`. Estados terminais (APROVADA, REJEITADA,
CANCELADA, NAO_CONFORME) sao IMUTAVEIS — caller recebe 409.

Concorrencia: ADR-0065 + INV-CAL-CONC-003 — UPDATE atomico via
`repo.atualizar_com_lock(snapshot, revision_anterior)`. Se race perdida
(rowcount=0), levanta `ConflitoVersaoCalibracaoCancelar` carregando
snapshot atual pra caller decidir retry / 409.

Caller (view) emite `EventoDeCalibracao(tipo=Cancelada)` no MESMO
transaction.atomic (OBS-CAL-01 conserto P5) — trilha WORM da operacao.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import CalibracaoRepository


class CalibracaoNaoEncontrada(Exception):
    """ID nao existe no tenant ativo (RLS ja filtrou) — caller retorna 404."""


class EstadoInvalidoParaCancelar(Exception):
    """Estado atual eh terminal — cancelamento bloqueado (caller retorna 409)."""


class ConflitoVersaoCalibracaoCancelar(Exception):
    """CAS perdeu race — caller decide retry vs 409. INV-CAL-CONC-003 + ADR-0065."""

    def __init__(self, snapshot_atual: CalibracaoSnapshot) -> None:
        self.snapshot_atual = snapshot_atual
        super().__init__(
            f"ConflitoVersao calibracao_id={snapshot_atual.id} "
            f"revision_atual={snapshot_atual.revision}"
        )


@dataclass(frozen=True, slots=True)
class CancelarCalibracaoInput:
    """Payload de cancelamento (transicao qualquer-nao-terminal -> CANCELADA)."""

    calibracao_id: UUID
    revision_esperada: int  # CAS — INV-CAL-CONC-003
    motivo_cancelamento_hash: str  # HashVersionado v<NN>$<base64> (ADR-0064)

    def __post_init__(self) -> None:
        if not self.motivo_cancelamento_hash:
            raise ValueError(
                "cancelar_calibracao: motivo_cancelamento_hash obrigatorio "
                "(derivado server-side a partir do motivo >=30 chars "
                "canonicalizado — SEG-CAL-07 + ADR-0064)"
            )


@dataclass(frozen=True, slots=True)
class CancelarCalibracaoOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: CancelarCalibracaoInput,
    repo: CalibracaoRepository,
) -> CancelarCalibracaoOutput:
    """Cancela calibracao (transicao -> CANCELADA via CAS).

    Levanta:
      CalibracaoNaoEncontrada — id nao existe (404).
      EstadoInvalidoParaCancelar — estado terminal (409).
      ConflitoVersaoCalibracaoCancelar — CAS perdeu race (409/retry).
    """
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status.terminal:
        raise EstadoInvalidoParaCancelar(
            f"status atual={atual.status.value} eh terminal — cancelar "
            f"exige estado nao-terminal (INV-CAL-WORM-001 + §4.1 spec)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.CANCELADA,
        revision=atual.revision + 1,
        motivo_cancelamento_hash=inp.motivo_cancelamento_hash,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracaoCancelar(snapshot_para_excecao)

    return CancelarCalibracaoOutput(snapshot=novo)
