"""Use case `registrar_recal_envio` — US-PAD-002 (M5 T-PAD-021).

Envia o padrao ao laboratorio externo de recalibracao. Transiciona
EM_USO -> EM_RECAL_EXTERNO (maquina de estados) via CAS optimistic
(`atualizar_com_lock`), e cria o RecalExternoPadrao em status ENVIADO.

Use case PURO. Bloqueios:
- estado deve aceitar envio (`EstadoPadrao.aceita_recal_envio` — so EM_USO).
- rastreabilidade da origem nao pode estar revogada (C-5) — padrao em duvida
  nao deve circular; reenvio decidido pelo RT.
- transicao validada pela maquina de estados (TransicaoInvalidaError).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

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


class PadraoNaoEncontradoError(Exception):
    def __init__(self, padrao_id: UUID) -> None:
        self.padrao_id = padrao_id
        super().__init__(f"Padrao {padrao_id} nao encontrado (ou de outro tenant).")


class PadraoNaoAceitaRecalError(Exception):
    def __init__(self, estado: EstadoPadrao) -> None:
        self.estado = estado
        super().__init__(
            f"Padrao em {estado.value} nao pode ser enviado a recal externo "
            f"(apenas EM_USO)."
        )


class RastreabilidadeRevogadaError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "C-5: padrao com rastreabilidade da origem revogada nao pode ser "
            "enviado a recal — decisao do RT primeiro."
        )


class ConflitoVersaoError(Exception):
    """CAS optimistic falhou (revision mudou — outra transacao venceu). 409."""

    def __init__(self, padrao_id: UUID) -> None:
        self.padrao_id = padrao_id
        super().__init__(f"Conflito de versao no padrao {padrao_id} (recarregue).")


@dataclass(frozen=True, slots=True)
class RegistrarRecalEnvioInput:
    tenant_id: UUID
    padrao_id: UUID
    enviado_em: datetime
    lab_externo: str
    responsavel_envio_id_hash: str
    numero_protocolo_lab_externo: str = ""

    def __post_init__(self) -> None:
        if self.enviado_em.tzinfo is None:
            raise ValueError("enviado_em exige datetime tz-aware (INV-VIG-004).")
        if not self.responsavel_envio_id_hash:
            raise ValueError(
                "responsavel_envio_id_hash obrigatorio (HashVersionado ADR-0064)."
            )


@dataclass(frozen=True, slots=True)
class RegistrarRecalEnvioOutput:
    recal: RecalExternoPadraoSnapshot
    padrao: PadraoMetrologicoSnapshot


def executar(
    inp: RegistrarRecalEnvioInput,
    repo_padrao: PadraoRepository,
    repo_recal: RecalExternoRepository,
) -> RegistrarRecalEnvioOutput:
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)
    if not padrao.estado.aceita_recal_envio:
        raise PadraoNaoAceitaRecalError(padrao.estado)
    if padrao.rastreabilidade_origem_revogada:
        raise RastreabilidadeRevogadaError

    validar_transicao(padrao.estado, EstadoPadrao.EM_RECAL_EXTERNO)

    recal = RecalExternoPadraoSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        padrao_id=inp.padrao_id,
        enviado_em=inp.enviado_em,
        lab_externo=inp.lab_externo,
        responsavel_envio_id_hash=inp.responsavel_envio_id_hash,
        status=StatusRecal.ENVIADO,
        numero_protocolo_lab_externo=inp.numero_protocolo_lab_externo,
    )
    repo_recal.salvar_novo(recal)

    novo_padrao = replace(
        padrao, estado=EstadoPadrao.EM_RECAL_EXTERNO, revision=padrao.revision + 1
    )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(inp.padrao_id)

    return RegistrarRecalEnvioOutput(recal=recal, padrao=novo_padrao)
