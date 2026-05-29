"""Use case `baixar_padrao` / `sucatar_padrao` — US-PAD-004 (M5 T-PAD-028).

Tira o padrao de uso (BAIXADO — reversivel com avaliacao tecnica) ou descarta
definitivamente (SUCATEADO — terminal duro). Exige assinatura A3 do RT
(ADR-0022 v2 / ADR-0068 — capturada no caller; aqui chega como
`responsavel_rt_id_hash`). Soft-delete B (ADR-0031): grava `revogado_em` +
`motivo_revogacao`; nunca DELETE fisico (INV-SOFT-002 — trigger PG).

INV-PAD-003: bloqueado se ha calibracao em curso usando o padrao. M5 nao depende
de M4 — o caller consulta `PadraoUsado` de calibracoes nao-terminais (M4) e passa
`tem_calibracao_em_curso`. Defesa em profundidade no use case.

Use case PURO. CAS optimistic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.padroes.entities import PadraoMetrologicoSnapshot
from src.domain.metrologia.padroes.enums import EstadoPadrao
from src.domain.metrologia.padroes.repository import PadraoRepository
from src.domain.metrologia.padroes.transicoes import validar_transicao

from .registrar_recal_envio import (
    ConflitoVersaoError,
    PadraoNaoEncontradoError,
)

_MIN_MOTIVO = 10  # ADR-0030 — motivo_revogacao >= 10 chars


class CalibracaoEmCursoError(Exception):
    """INV-PAD-003 — padrao em uso por calibracao nao-terminal."""

    def __init__(self) -> None:
        super().__init__(
            "INV-PAD-003: padrao em uso por calibracao em curso nao pode ser "
            "baixado/sucateado — conclua ou cancele a calibracao primeiro."
        )


@dataclass(frozen=True, slots=True)
class BaixarPadraoInput:
    tenant_id: UUID
    padrao_id: UUID
    sucatar: bool
    motivo_revogacao: str
    responsavel_rt_id_hash: str
    revogado_em: datetime
    tem_calibracao_em_curso: bool

    def __post_init__(self) -> None:
        if self.revogado_em.tzinfo is None:
            raise ValueError("revogado_em exige datetime tz-aware (INV-VIG-004).")
        if len(self.motivo_revogacao.strip()) < _MIN_MOTIVO:
            raise ValueError(
                f"motivo_revogacao exige >= {_MIN_MOTIVO} chars (ADR-0030)."
            )
        if not self.responsavel_rt_id_hash:
            raise ValueError(
                "responsavel_rt_id_hash obrigatorio (A3 RT — ADR-0022 v2/0068)."
            )


@dataclass(frozen=True, slots=True)
class BaixarPadraoOutput:
    padrao: PadraoMetrologicoSnapshot


def executar(inp: BaixarPadraoInput, repo_padrao: PadraoRepository) -> BaixarPadraoOutput:
    if inp.tem_calibracao_em_curso:
        raise CalibracaoEmCursoError
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)

    novo_estado = EstadoPadrao.SUCATEADO if inp.sucatar else EstadoPadrao.BAIXADO
    validar_transicao(padrao.estado, novo_estado)

    novo_padrao = replace(
        padrao,
        estado=novo_estado,
        revision=padrao.revision + 1,
        revogado_em=inp.revogado_em,
        motivo_revogacao=inp.motivo_revogacao,
    )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(inp.padrao_id)
    return BaixarPadraoOutput(padrao=novo_padrao)
