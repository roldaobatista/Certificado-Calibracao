"""Use case `registrar_recal_retorno` — US-PAD-002 (M5 T-PAD-022, C-4 FURO-1).

Registra o RETORNO do padrao do laboratorio externo. Dois desfechos:

- RETORNADO (normal): grava os novos valores no RecalExternoPadrao
  (incertezas/validade/valor convencional) e transiciona o padrao
  EM_RECAL_EXTERNO -> RECAL_RETORNADO_PENDENTE_APROVACAO. O padrao NAO volta a
  EM_USO automaticamente — so a analise critica do RT libera (C-4 FURO-1,
  `aprovar_recal_rt`). As incertezas do PADRAO NAO sao tocadas aqui (so na
  aprovacao, via INV-PAD-006/GUC).
- EXTRAVIADO_NO_TRANSPORTE / RECUSADO_PELO_LAB: padrao vai a BAIXADO (avaliacao
  tecnica), sem novos valores.

Use case PURO. CAS optimistic na transicao do padrao.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
)
from src.domain.metrologia.padroes.enums import EstadoPadrao, StatusRecal
from src.domain.metrologia.padroes.repository import (
    PadraoRepository,
    RecalExternoRepository,
)
from src.domain.metrologia.padroes.transicoes import validar_transicao
from src.domain.metrologia.value_objects import IncertezaExpandida

from .registrar_recal_envio import (
    ConflitoVersaoError,
    PadraoNaoEncontradoError,
)


class RecalNaoEncontradoError(Exception):
    def __init__(self, recal_id: UUID) -> None:
        self.recal_id = recal_id
        super().__init__(f"Recal {recal_id} nao encontrado (ou de outro tenant).")


class RecalJaRetornadoError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Recal ja retornado — valores imutaveis pos-retorno (WORM)."
        )


class RetornoIncompletoError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Retorno RETORNADO exige >=1 incerteza nova + validade_nova + "
            "valor_convencional_novo (INV-PAD-006 alimenta a aprovacao)."
        )


@dataclass(frozen=True, slots=True)
class RegistrarRecalRetornoInput:
    tenant_id: UUID
    recal_id: UUID
    status: StatusRecal
    retornado_em: datetime
    incertezas_novas: tuple[IncertezaExpandida, ...] = ()
    validade_nova: date | None = None
    valor_convencional_novo: Decimal | None = None
    cert_externo_novo_storage_key: str = ""

    def __post_init__(self) -> None:
        if self.retornado_em.tzinfo is None:
            raise ValueError("retornado_em exige datetime tz-aware (INV-VIG-004).")
        if self.status == StatusRecal.ENVIADO:
            raise ValueError("registrar_recal_retorno nao aceita status ENVIADO.")


@dataclass(frozen=True, slots=True)
class RegistrarRecalRetornoOutput:
    recal: RecalExternoPadraoSnapshot
    padrao: PadraoMetrologicoSnapshot


def executar(
    inp: RegistrarRecalRetornoInput,
    repo_padrao: PadraoRepository,
    repo_recal: RecalExternoRepository,
) -> RegistrarRecalRetornoOutput:
    recal = repo_recal.obter_por_id(inp.recal_id)
    if recal is None:
        raise RecalNaoEncontradoError(inp.recal_id)
    if recal.retornado_em is not None:
        raise RecalJaRetornadoError
    padrao = repo_padrao.obter_por_id(recal.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(recal.padrao_id)

    retorno_normal = inp.status == StatusRecal.RETORNADO
    if retorno_normal and (
        not inp.incertezas_novas
        or inp.validade_nova is None
        or inp.valor_convencional_novo is None
    ):
        raise RetornoIncompletoError

    novo_estado = (
        EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO
        if retorno_normal
        else EstadoPadrao.BAIXADO
    )
    validar_transicao(padrao.estado, novo_estado)

    recal_atualizado = replace(
        recal,
        status=inp.status,
        retornado_em=inp.retornado_em,
        incertezas_novas=inp.incertezas_novas,
        validade_nova=inp.validade_nova,
        valor_convencional_novo=inp.valor_convencional_novo,
        cert_externo_novo_storage_key=inp.cert_externo_novo_storage_key,
    )
    repo_recal.atualizar_retorno_e_aprovacao(recal_atualizado)

    novo_padrao = replace(padrao, estado=novo_estado, revision=padrao.revision + 1)
    if novo_estado == EstadoPadrao.BAIXADO:
        novo_padrao = replace(
            novo_padrao,
            revogado_em=inp.retornado_em,
            motivo_revogacao=f"recal {inp.status.value} no transporte/lab externo",
        )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(recal.padrao_id)

    return RegistrarRecalRetornoOutput(recal=recal_atualizado, padrao=novo_padrao)
