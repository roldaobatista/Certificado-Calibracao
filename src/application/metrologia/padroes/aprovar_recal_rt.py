"""Use case `aprovar_recal_rt` — US-PAD-002 (M5 T-PAD-023, C-4 FURO-1).

Analise critica do RT sobre o recal retornado. Dois desfechos a partir de
RECAL_RETORNADO_PENDENTE_APROVACAO:

- APROVADO: grava `aprovado_rt_em`/`aprovado_rt_id_hash` no recal (one-shot,
  trigger PG), transiciona o padrao -> EM_USO e SO ENTAO atualiza as incertezas
  do padrao com os valores do recal — via `repo_padrao.aplicar_recal_aprovado`,
  que e o UNICO caminho que o trigger INV-PAD-006 libera (adapter seta
  `SET LOCAL app.padrao_recal_em_curso = '1'`).
- REJEITADO: padrao volta a EM_RECAL_EXTERNO (RT pede re-envio); incertezas
  intactas.

Use case PURO. CAS optimistic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID

from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
)
from src.domain.metrologia.padroes.enums import EstadoPadrao
from src.domain.metrologia.padroes.repository import (
    PadraoRepository,
    RecalExternoRepository,
)
from src.domain.metrologia.padroes.transicoes import validar_transicao

from .registrar_recal_envio import (
    ConflitoVersaoError,
    PadraoNaoEncontradoError,
)
from .registrar_recal_retorno import RecalNaoEncontradoError


class RecalNaoRetornadoError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Recal sem retorno registrado — nao ha o que o RT aprovar/rejeitar."
        )


class RecalJaAprovadoError(Exception):
    def __init__(self) -> None:
        super().__init__("Recal ja aprovado pelo RT (one-shot, imutavel — C-4).")


class PadraoNaoPendenteAprovacaoError(Exception):
    def __init__(self, estado: EstadoPadrao) -> None:
        self.estado = estado
        super().__init__(
            f"Padrao em {estado.value} nao esta pendente de aprovacao de recal "
            f"(esperado RECAL_RETORNADO_PENDENTE_APROVACAO)."
        )


@dataclass(frozen=True, slots=True)
class AprovarRecalRTInput:
    tenant_id: UUID
    recal_id: UUID
    aprovado: bool
    aprovado_rt_id_hash: str
    decidido_em: datetime
    # obrigatorio quando aprovado=True — proximo recal calculado pelo caller
    # (retornado_em + intervalo_recal_meses do padrao).
    proximo_recal_novo: date | None = None

    def __post_init__(self) -> None:
        if self.decidido_em.tzinfo is None:
            raise ValueError("decidido_em exige datetime tz-aware (INV-VIG-004).")
        if not self.aprovado_rt_id_hash:
            raise ValueError(
                "aprovado_rt_id_hash obrigatorio (HashVersionado ADR-0064)."
            )
        if self.aprovado and self.proximo_recal_novo is None:
            raise ValueError(
                "aprovacao exige proximo_recal_novo (intervalo de recal — C-9)."
            )


@dataclass(frozen=True, slots=True)
class AprovarRecalRTOutput:
    recal: RecalExternoPadraoSnapshot
    padrao: PadraoMetrologicoSnapshot


def executar(
    inp: AprovarRecalRTInput,
    repo_padrao: PadraoRepository,
    repo_recal: RecalExternoRepository,
) -> AprovarRecalRTOutput:
    recal = repo_recal.obter_por_id(inp.recal_id)
    if recal is None:
        raise RecalNaoEncontradoError(inp.recal_id)
    if recal.retornado_em is None:
        raise RecalNaoRetornadoError
    if recal.aprovado_rt_em is not None:
        raise RecalJaAprovadoError
    padrao = repo_padrao.obter_por_id(recal.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(recal.padrao_id)
    if padrao.estado != EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO:
        raise PadraoNaoPendenteAprovacaoError(padrao.estado)

    if not inp.aprovado:
        # RT rejeita -> re-envia
        validar_transicao(padrao.estado, EstadoPadrao.EM_RECAL_EXTERNO)
        novo_padrao = replace(
            padrao, estado=EstadoPadrao.EM_RECAL_EXTERNO, revision=padrao.revision + 1
        )
        if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
            raise ConflitoVersaoError(recal.padrao_id)
        return AprovarRecalRTOutput(recal=recal, padrao=novo_padrao)

    # Aprovado: grava aprovacao no recal (one-shot)
    validar_transicao(padrao.estado, EstadoPadrao.EM_USO)
    recal_aprovado = replace(
        recal, aprovado_rt_em=inp.decidido_em, aprovado_rt_id_hash=inp.aprovado_rt_id_hash
    )
    repo_recal.atualizar_retorno_e_aprovacao(recal_aprovado)

    # Atualiza o padrao com os novos valores — UNICO caminho que libera INV-PAD-006.
    assert inp.proximo_recal_novo is not None  # garantido por __post_init__
    assert recal.validade_nova is not None  # garantido em registrar_recal_retorno
    novo_padrao = replace(
        padrao,
        estado=EstadoPadrao.EM_USO,
        revision=padrao.revision + 1,
        incertezas_certificado=recal.incertezas_novas,
        validade_certificado_rastreabilidade=recal.validade_nova,
        proximo_recal=inp.proximo_recal_novo,
    )
    if not repo_padrao.aplicar_recal_aprovado(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(recal.padrao_id)

    return AprovarRecalRTOutput(recal=recal_aprovado, padrao=novo_padrao)
