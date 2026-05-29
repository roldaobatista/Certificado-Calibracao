"""Use case `revogar_rastreabilidade_origem` — (M5 T-PAD-029, C-5 FURO-4).

Liga a flag transversal `rastreabilidade_origem_revogada` quando um evento
EXTERNO invalida a cadeia de rastreabilidade do padrao (ex: o laboratorio de
origem perdeu a acreditacao CGCRE — paralelo ADR-0045 recall de certificado).
A flag bloqueia o uso do padrao em calibracao INDEPENDENTE do estado
(`padrao_bloqueado_para_uso`, P4), sem mudar a maquina de estados — o padrao
nao deixa de existir, mas nao pode ser usado ate a situacao ser resolvida
(novo recal numa origem valida).

NAO toca `incertezas_certificado` (a flag e campo proprio — atualizar_com_lock
nao dispara INV-PAD-006). Use case PURO. CAS optimistic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from src.domain.metrologia.padroes.entities import PadraoMetrologicoSnapshot
from src.domain.metrologia.padroes.repository import PadraoRepository

from .registrar_recal_envio import (
    ConflitoVersaoError,
    PadraoNaoEncontradoError,
)

_MIN_MOTIVO = 10


class JaRevogadaError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Rastreabilidade da origem ja revogada para este padrao (idempotente)."
        )


@dataclass(frozen=True, slots=True)
class RevogarRastreabilidadeInput:
    tenant_id: UUID
    padrao_id: UUID
    motivo: str

    def __post_init__(self) -> None:
        if len(self.motivo.strip()) < _MIN_MOTIVO:
            raise ValueError(f"motivo exige >= {_MIN_MOTIVO} chars (auditoria C-5).")


@dataclass(frozen=True, slots=True)
class RevogarRastreabilidadeOutput:
    padrao: PadraoMetrologicoSnapshot


def executar(
    inp: RevogarRastreabilidadeInput, repo_padrao: PadraoRepository
) -> RevogarRastreabilidadeOutput:
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)
    if padrao.rastreabilidade_origem_revogada:
        raise JaRevogadaError

    novo_padrao = replace(
        padrao,
        rastreabilidade_origem_revogada=True,
        revision=padrao.revision + 1,
    )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(inp.padrao_id)
    return RevogarRastreabilidadeOutput(padrao=novo_padrao)
