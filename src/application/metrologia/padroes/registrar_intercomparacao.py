"""Use case `registrar_intercomparacao` — US-PAD-005 (M5 T-PAD-025).

Intercomparacao / proficiency testing (cl. 6.6 — INV-023), EXCLUSIVO perfil A
(laboratorio acreditado). Dois passos:

- `executar_inicio`: cria a IntercomparacaoPT (sem resultado) e transiciona o
  padrao EM_USO -> INTERCOMPARACAO_PT_EM_CURSO.
- `executar_resultado`: grava resultado/zeta/relatorio (one-shot) e transiciona
  INTERCOMPARACAO_PT_EM_CURSO -> EM_USO. PT REJEITADO bloqueia uso ate NC
  tratada — bloqueio computado em `padrao_bloqueado_para_uso` (P4), nao muda a
  maquina de estados.

Use case PURO. CAS optimistic nas transicoes do padrao.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.padroes.entities import (
    IntercomparacaoPTSnapshot,
    PadraoMetrologicoSnapshot,
)
from src.domain.metrologia.padroes.enums import EstadoPadrao, ResultadoPT
from src.domain.metrologia.padroes.repository import (
    IntercomparacaoPTRepository,
    PadraoRepository,
)
from src.domain.metrologia.padroes.transicoes import validar_transicao

from .registrar_recal_envio import (
    ConflitoVersaoError,
    PadraoNaoEncontradoError,
)


class PerfilNaoPermitePTError(Exception):
    """US-PAD-005 / INV-023 — intercomparacao PT e exclusiva perfil A."""

    def __init__(self) -> None:
        super().__init__(
            "INV-023: intercomparacao/PT e exclusiva de tenant perfil A "
            "(laboratorio acreditado — ADR-0067)."
        )


class PTNaoEncontradaError(Exception):
    def __init__(self, pt_id: UUID) -> None:
        self.pt_id = pt_id
        super().__init__(f"Intercomparacao/PT {pt_id} nao encontrada.")


class PTJaFinalizadaError(Exception):
    def __init__(self) -> None:
        super().__init__("PT ja finalizada — resultado imutavel (WORM cl. 6.6).")


class PadraoNaoEmPTError(Exception):
    def __init__(self, estado: EstadoPadrao) -> None:
        self.estado = estado
        super().__init__(
            f"Padrao em {estado.value} nao esta em intercomparacao "
            f"(esperado INTERCOMPARACAO_PT_EM_CURSO)."
        )


@dataclass(frozen=True, slots=True)
class IniciarPTInput:
    tenant_id: UUID
    padrao_id: UUID
    lab_organizador: str
    protocolo: str
    data_inicio: datetime
    tenant_e_perfil_a: bool

    def __post_init__(self) -> None:
        if self.data_inicio.tzinfo is None:
            raise ValueError("data_inicio exige datetime tz-aware (INV-VIG-004).")


@dataclass(frozen=True, slots=True)
class IniciarPTOutput:
    pt: IntercomparacaoPTSnapshot
    padrao: PadraoMetrologicoSnapshot


@dataclass(frozen=True, slots=True)
class RegistrarResultadoPTInput:
    tenant_id: UUID
    pt_id: UUID
    resultado: ResultadoPT
    data_resultado: datetime
    zeta_score: Decimal | None = None
    relatorio_pt_storage_key: str = ""
    nao_conformidade_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.data_resultado.tzinfo is None:
            raise ValueError("data_resultado exige datetime tz-aware (INV-VIG-004).")


@dataclass(frozen=True, slots=True)
class RegistrarResultadoPTOutput:
    pt: IntercomparacaoPTSnapshot
    padrao: PadraoMetrologicoSnapshot


def executar_inicio(
    inp: IniciarPTInput,
    repo_padrao: PadraoRepository,
    repo_pt: IntercomparacaoPTRepository,
) -> IniciarPTOutput:
    if not inp.tenant_e_perfil_a:
        raise PerfilNaoPermitePTError
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)
    validar_transicao(padrao.estado, EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO)

    pt = IntercomparacaoPTSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        padrao_id=inp.padrao_id,
        lab_organizador=inp.lab_organizador,
        protocolo=inp.protocolo,
        data_inicio=inp.data_inicio,
    )
    repo_pt.salvar_nova(pt)

    novo_padrao = replace(
        padrao,
        estado=EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO,
        revision=padrao.revision + 1,
    )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(inp.padrao_id)
    return IniciarPTOutput(pt=pt, padrao=novo_padrao)


def executar_resultado(
    inp: RegistrarResultadoPTInput,
    repo_padrao: PadraoRepository,
    repo_pt: IntercomparacaoPTRepository,
) -> RegistrarResultadoPTOutput:
    pt = repo_pt.obter_por_id(inp.pt_id)
    if pt is None:
        raise PTNaoEncontradaError(inp.pt_id)
    if pt.data_resultado is not None:
        raise PTJaFinalizadaError
    padrao = repo_padrao.obter_por_id(pt.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(pt.padrao_id)
    if padrao.estado != EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO:
        raise PadraoNaoEmPTError(padrao.estado)

    pt_final = replace(
        pt,
        resultado=inp.resultado,
        data_resultado=inp.data_resultado,
        zeta_score=inp.zeta_score,
        relatorio_pt_storage_key=inp.relatorio_pt_storage_key,
        nao_conformidade_id=inp.nao_conformidade_id,
    )
    repo_pt.atualizar_resultado(pt_final)

    validar_transicao(padrao.estado, EstadoPadrao.EM_USO)
    novo_padrao = replace(
        padrao, estado=EstadoPadrao.EM_USO, revision=padrao.revision + 1
    )
    if not repo_padrao.atualizar_com_lock(novo_padrao, padrao.revision):
        raise ConflitoVersaoError(pt.padrao_id)
    return RegistrarResultadoPTOutput(pt=pt_final, padrao=novo_padrao)
